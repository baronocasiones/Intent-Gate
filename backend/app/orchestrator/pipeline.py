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

Persistence goes through M14's `db.py` helpers — writes via `save_run` /
`set_status`, reads via `get_run` / `list_runs`, exactly as db.py's docstring
assigns them (M10 writes, M15 reads). This module owns no SQL and no
connection tuning (§0.4: db.py and store/ are called, never edited). The row
readers stay re-exported here so routers import from one place instead of
growing query code of their own.
"""
import uuid

from .. import db
from ..store import artifacts
from ..gates import ingest, extract, parse, verify, adjudicate, emit as emit_gate
from . import jobs


def _set_status(run_id: str, status: str) -> None:
    """Flip an existing row on the crash path. The row may never have been
    created (a direct call that failed before `_mark_running`), so rowcount 0
    is tolerated here: this helper only *tries* to record the failure, and the
    re-raise after it is what keeps rule 6 honest — never a swallowed error."""
    conn = db.get_db()
    try:
        db.set_status(conn, run_id, status)
    finally:
        conn.close()


def _mark_running(run_id: str) -> None:
    """Ensure the row exists and reads `running`: flip the `queued` row the
    enqueue path inserted; when the row is absent (a direct `run_pipeline`
    call minting its own id), insert it as `running` instead. Rowcount 0 here
    means *create*, not *pass* — the final flip is where a missing row must
    fail loud (rule 6)."""
    conn = db.get_db()
    try:
        if db.set_status(conn, run_id, "running") == 0:
            db.save_run(conn, run_id, "running")
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

    `db.save_run` is a plain INSERT (not OR IGNORE): an id collision surfaces
    as a loud failure rather than silently serving a different run's row.
    """
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    conn = db.get_db()
    try:
        db.save_run(conn, run_id, "queued")
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
        conn = db.get_db()
        try:
            written = db.set_status(conn, run_id, _final_status(record), path)
        finally:
            conn.close()
        if written == 0:
            # The row vanished between `_mark_running` and now: a defect, and
            # a run whose row does not exist must not read as a pass (rule 6).
            # Raising inside the try lands in the except below, which records
            # `failed` (a no-op — the row is gone) and re-raises: loud twice.
            raise RuntimeError(f"run row disappeared before final status: {run_id}")
    except Exception:
        # A crash must never leave a run looking alive or certified (rule 6);
        # the row says `failed` and the exception still propagates to the
        # caller — never swallowed here.
        _set_status(run_id, "failed")
        raise
    return record


def _project(row: dict) -> dict:
    """`db.py` rows key on `id` (the column name); the API shape is `run_id`
    (run.schema.json / rule 3 — the endpoint's contract does not move because
    persistence named the column differently)."""
    return {
        "run_id": row["id"],
        "status": row["status"],
        "created_at": row["created_at"],
        "artifact_path": row["artifact_path"],
    }


def list_run_rows() -> list[dict]:
    """All runs, newest first — M14's `list_runs`: `created_at DESC` with the
    `id DESC` tiebreak, capped at 50 (db.py's default limit; the cap is
    documented rather than hidden behind an unbounded query)."""
    conn = db.get_db()
    try:
        return [_project(r) for r in db.list_runs(conn)]
    finally:
        conn.close()


def fetch_run_row(run_id: str) -> dict | None:
    """One run's row in router shape, or None when the id is unknown (the
    router turns that into 404)."""
    conn = db.get_db()
    try:
        row = db.get_run(conn, run_id)
    finally:
        conn.close()
    return None if row is None else _project(row)
