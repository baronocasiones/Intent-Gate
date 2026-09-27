"""Pipeline — ingest → extract → parse → verify → adjudicate → emit.
Non-zero exit blocks merge (gate, not reviewer).

Run lifecycle (M15 session): `enqueue_run` persists a `queued` row and submits
to the jobs queue; `run_pipeline` marks the run `running`, executes the six
stages, writes the artifact, and flips the row to its final status.

Status values follow the D9 *recommended default* (modules.md §6: take the
recommended default and record that you did): `queued` → `running` →
lowercased run verdict (`certified` / `conditional` / `rejected`), with
`failed` for a crash. One recorded deviation: a `PENDING` verdict maps to
`pending`, not `failed` — D9's proposed set has no value for "not yet decided",
and inventing `failed` for an unexamined run would misreport a fail-closed
default as a crash. `status` is a free string in `run.schema.json`, so this
cannot violate the contract.

Persistence is a deliberate shim (modules.md M15 core slice): `db.py` and
`store/artifacts.py` are used as-built and untouched; the glue lives here
because orchestrator/ is shim-approved for this session. Reads
(`list_run_rows` / `fetch_run_row`) are here for the same reason — routers are
M15's files and import from here rather than growing query code of their own.
"""
import sqlite3
import uuid
from datetime import datetime, timezone

from ..config import DATABASE_URL
from ..db import get_db
from ..store import artifacts
from ..gates import ingest, extract, parse, verify, adjudicate, emit as emit_gate
from . import jobs

SQLITE_PREFIX = "sqlite:///"


def _db_path(url: str = DATABASE_URL) -> str:
    """`db.get_db()` wants a file path; config carries a sqlite:/// URL."""
    if not url.startswith(SQLITE_PREFIX):
        raise ValueError(f"only sqlite:/// URLs are supported, got {url!r}")
    return url[len(SQLITE_PREFIX):]


# Resolved once at import (same style as store/artifacts.py's ARTIFACT_DIR).
# Tests redirect it via monkeypatch — see backend/tests/conftest.py, which
# keeps every test off the repo tree (Convention 3).
DB_PATH = _db_path()


def _now() -> str:
    # ISO-8601 string (M14: the column is TEXT and the type must be pinned by
    # a test — test_api.py pins it on the read path).
    return datetime.now(timezone.utc).isoformat()


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.executescript(
        "CREATE TABLE IF NOT EXISTS runs ("
        "id TEXT PRIMARY KEY, status TEXT NOT NULL, "
        "created_at TEXT NOT NULL, artifact_path TEXT);"
    )
    conn.row_factory = sqlite3.Row
    return conn


def _set_status(run_id: str, status: str) -> None:
    """Flip an existing row; a no-op when the row never got created."""
    conn = _connect()
    try:
        conn.execute("UPDATE runs SET status = ? WHERE id = ?", (status, run_id))
        conn.commit()
    finally:
        conn.close()


def _mark_running(run_id: str) -> None:
    """Ensure the row exists and is `running` — no-op update if it pre-exists
    (the enqueue path inserted it as `queued` first)."""
    conn = _connect()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO runs (id, status, created_at, artifact_path) "
            "VALUES (?, 'running', ?, NULL)",
            (run_id, _now()),
        )
        conn.execute("UPDATE runs SET status = 'running' WHERE id = ?", (run_id,))
        conn.commit()
    finally:
        conn.close()


def _final_status(record: dict) -> str:
    """Run status from the emit envelope's adjudicated verdict, lowercased.

    No verdict → `failed`: a record that cannot say what it decided must not
    read as a pass (rule 6).
    """
    inner = record.get("record")
    verdict = inner.get("verdict") if isinstance(inner, dict) else None
    if verdict:
        return str(verdict).lower()
    return "failed"


def enqueue_run(payload: dict) -> str:
    """Mint a run id, persist the `queued` row, submit to the jobs queue.

    Plain INSERT (not OR IGNORE): an id collision surfaces as a loud failure
    rather than silently serving a different run's row.
    """
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    conn = _connect()
    try:
        conn.execute(
            "INSERT INTO runs (id, status, created_at, artifact_path) "
            "VALUES (?, 'queued', ?, NULL)",
            (run_id, _now()),
        )
        conn.commit()
    finally:
        conn.close()
    jobs.submit({"run_id": run_id, "payload": payload})
    return run_id


def run_pipeline(payload: dict, run_id: str | None = None) -> dict:
    """Synchronous path — each gate returns fixture-shaped stubs until M4–M9 land.

    `run_id` is supplied by the queue (the row was minted by `enqueue_run`);
    a direct call without one mints its own row, so the synchronous path
    persists exactly like the queued one.
    """
    run_id = run_id or f"run-{uuid.uuid4().hex[:8]}"
    _mark_running(run_id)
    try:
        bundle = ingest.run(payload)
        criteria = extract.run(bundle)
        ast = parse.run(criteria)
        findings = verify.run(ast)
        verdict = adjudicate.run(findings)
        record = emit_gate.run(verdict)
        path = artifacts.write_artifact(run_id, record)
        conn = _connect()
        try:
            conn.execute(
                "UPDATE runs SET status = ?, artifact_path = ? WHERE id = ?",
                (_final_status(record), path, run_id),
            )
            conn.commit()
        finally:
            conn.close()
    except Exception:
        # A crash must never leave a run looking alive or certified (rule 6);
        # the row says `failed` and the exception still propagates to the
        # caller — never swallowed here.
        _set_status(run_id, "failed")
        raise
    return record


def list_run_rows() -> list[dict]:
    """All runs, newest first (created_at, insertion order as tiebreak)."""
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT id, status, created_at, artifact_path FROM runs "
            "ORDER BY created_at DESC, rowid DESC"
        ).fetchall()
        return [
            {
                "run_id": r["id"],
                "status": r["status"],
                "created_at": r["created_at"],
                "artifact_path": r["artifact_path"],
            }
            for r in rows
        ]
    finally:
        conn.close()


def fetch_run_row(run_id: str) -> dict | None:
    """One run's row, or None when the id is unknown (router turns that into 404)."""
    conn = _connect()
    try:
        r = conn.execute(
            "SELECT id, status, created_at, artifact_path FROM runs WHERE id = ?",
            (run_id,),
        ).fetchone()
        if r is None:
            return None
        return {
            "run_id": r["id"],
            "status": r["status"],
            "created_at": r["created_at"],
            "artifact_path": r["artifact_path"],
        }
    finally:
        conn.close()
