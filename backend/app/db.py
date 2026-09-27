"""SQLite (WAL) engine — the run index. JSON artifacts live on disk (store/).

M14 owns this file. The connection default comes from `config.DATABASE_URL`,
bound at import so tests patch `app.db.DATABASE_URL` — the consumer module —
never `os.environ` (docs/test-suite.md Convention 2). `DATABASE_URL` keeps
its `sqlite:///` URL form from `.env.example`; `_sqlite_path()` strips the
scheme. `get_db` callers pass explicit paths (tests use `tmp_path`), which
always win over the env default.

The write helpers (`save_run`, `set_status`) hold the `commit()` — not the
caller — because `sqlite3` opens an implicit transaction before DML and a
forgotten commit silently loses the row on close. M10 writes rows only
through these helpers; M15 reads through `get_run` / `list_runs`.
"""
import sqlite3
from datetime import datetime, timezone

from .config import DATABASE_URL

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    artifact_path TEXT
);
CREATE INDEX IF NOT EXISTS idx_runs_created_at ON runs(created_at);
"""

SQLITE_URL_PREFIX = "sqlite:///"

_RUN_COLS = ("id", "status", "created_at", "artifact_path")


def _sqlite_path(url: str) -> str:
    """Strip the `sqlite:///` scheme; pass bare paths through untouched.

    `sqlite:///./attestation.db` -> `./attestation.db` (relative, CWD-bound —
    see the known limitation in docs/architecture.md §6);
    `sqlite:////abs/x.db` -> `/abs/x.db`; `plain/path.db` unchanged.
    """
    if url.startswith(SQLITE_URL_PREFIX):
        return url[len(SQLITE_URL_PREFIX):]
    return url


def now_iso() -> str:
    """The one timestamp source for every writer. UTC, timezone-aware,
    ISO-8601 — so `created_at` is always a `str` (never a float, never naive)
    and lexicographic order is time order, which is what `list_runs` relies
    on for newest-first.
    """
    return datetime.now(timezone.utc).isoformat()


def get_db(path: str | None = None) -> sqlite3.Connection:
    """Open the runs index. An explicit `path` always wins; otherwise derive
    from `DATABASE_URL`. WAL mode is set on every open; the schema (table +
    index) is idempotent, so opening twice is safe.
    """
    resolved = path if path is not None else _sqlite_path(DATABASE_URL)
    conn = sqlite3.connect(resolved)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.executescript(SCHEMA)
    return conn


def save_run(conn: sqlite3.Connection, run_id: str, status: str,
             artifact_path: str | None = None) -> None:
    """INSERT a run row and commit. M10 calls this; it never hand-rolls SQL
    for the insert. A duplicate `run_id` raises — a re-minted id is a loud
    bug, not a silent overwrite.
    """
    conn.execute(
        "INSERT INTO runs (id, status, created_at, artifact_path)"
        " VALUES (?, ?, ?, ?)",
        (run_id, status, now_iso(), artifact_path),
    )
    conn.commit()


def set_status(conn: sqlite3.Connection, run_id: str, status: str,
               artifact_path: str | None = None) -> int:
    """Flip a stored run's status and commit. A provided `artifact_path`
    overwrites; `None` keeps the existing one. Returns the rowcount — 0 means
    the run does not exist, which the caller must treat as a blocking failure
    (modules.md rule 6), never as a pass.
    """
    cur = conn.execute(
        "UPDATE runs SET status = ?,"
        " artifact_path = COALESCE(?, artifact_path) WHERE id = ?",
        (status, artifact_path, run_id),
    )
    conn.commit()
    return cur.rowcount


def get_run(conn: sqlite3.Connection, run_id: str) -> dict | None:
    """One `runs` row as a dict, or `None` for an unknown id (M15's 404)."""
    row = conn.execute(
        "SELECT id, status, created_at, artifact_path FROM runs WHERE id = ?",
        (run_id,),
    ).fetchone()
    return dict(zip(_RUN_COLS, row)) if row is not None else None


def list_runs(conn: sqlite3.Connection, limit: int = 50) -> list[dict]:
    """Runs newest-first (M15's `GET /api/runs`). `idx_runs_created_at` keeps
    this an index scan; `id DESC` breaks `created_at` ties deterministically.
    """
    rows = conn.execute(
        "SELECT id, status, created_at, artifact_path FROM runs"
        " ORDER BY created_at DESC, id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return [dict(zip(_RUN_COLS, row)) for row in rows]
