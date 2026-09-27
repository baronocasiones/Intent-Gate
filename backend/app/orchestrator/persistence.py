"""Persistence glue — M10's only path to the runs index (D-a').

M14's `db.py` owns ALL the SQL: this module never hand-rolls any and never
calls `commit()` (the helpers commit themselves — a forgotten commit silently
loses the row). It owns exactly two things:

1. the connection lifecycle — one short-lived connection per operation, closed
   in `finally`, so a forgotten close can never leak across runs; and
2. the rule-6 reading of `set_status`'s rowcount — 0 means the row is missing,
   which is a blocking anomaly reported upward, never treated as a pass.

Status vocabulary (D-e): `queued` → `running` → (`pending` | `failed`).
`pending` means the chain *completed* — the verdict lives inside the artifact
(M9/D9 own it). `failed` means a stage *crashed*.
"""
from contextlib import contextmanager
from sqlite3 import Connection
from typing import Iterator

from ..db import get_db, save_run, set_status


@contextmanager
def runs_conn() -> Iterator[Connection]:
    """Open the runs index, yield it, close it. Helpers commit themselves."""
    conn = get_db()
    try:
        yield conn
    finally:
        conn.close()


def mark_queued(run_id: str) -> None:
    """INSERT the run as `queued`. Raises on a duplicate id — a re-minted id
    is a loud bug (db.py); ids are uuid4, so this is unreachable in
    production and must stay loud in tests."""
    with runs_conn() as conn:
        save_run(conn, run_id, "queued")


def mark_running(run_id: str) -> bool:
    """Flip `queued` → `running`. False == the row is missing (rule 6)."""
    with runs_conn() as conn:
        return set_status(conn, run_id, "running") > 0


def mark_done(run_id: str, artifact_path: str) -> bool:
    """Flip → `pending` and point at the run's artifact."""
    with runs_conn() as conn:
        return set_status(conn, run_id, "pending", artifact_path) > 0


def mark_failed(run_id: str, artifact_path: str | None) -> bool:
    """Flip → `failed` and point at the blocking record's artifact (if any).

    The artifact — not the row — carries the failure detail: the `runs`
    table has no `error`/`stage` columns, so stage, message and `exit_code`
    live in the JSON the row points at.
    """
    with runs_conn() as conn:
        return set_status(conn, run_id, "failed", artifact_path) > 0
