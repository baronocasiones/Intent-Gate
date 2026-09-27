"""Lane-wide test isolation — M10 (R1, refactor plan).

Every test runs against throwaway persistence:

- `app.db.DATABASE_URL` and `app.store.artifacts.ARTIFACT_DIR` are patched on
  the *consumer modules* (Convention 2 — never `os.environ`; `test_config.py`
  reloads `app.config` itself and must keep seeing defaults). Both bindings
  are read dynamically at call time (`db.get_db`, `artifact_path_for`), so the
  patch redirects every writer.
- The module-level `jobs._queue` is drained before AND after each test with
  pure `get_nowait` (never awaited, so F1's loop binding cannot trigger).

Without this, `enqueue_run`'s persistence — 50 queue items from
`test_enqueue_run_ids_unique`, 7 webhook rows — leaks across tests and
`test_jobs_submit`'s `qsize() == 0` fails on ordering alone.

Unowned file — M17 owns adoption (one writer per file, §0.4).
"""
import asyncio

import pytest

import app.db as db_mod
import app.store.artifacts as artifacts_mod
from app.orchestrator import jobs


def _drain(queue: asyncio.Queue) -> None:
    """Synchronously empty the queue; `task_done` stays balanced."""
    while True:
        try:
            queue.get_nowait()
        except asyncio.QueueEmpty:
            return
        queue.task_done()


@pytest.fixture(autouse=True)
def _isolated_persistence_and_queue(tmp_path, monkeypatch):
    monkeypatch.setattr(
        db_mod, "DATABASE_URL", f"sqlite:///{tmp_path}/attestation.db"
    )
    monkeypatch.setattr(
        artifacts_mod, "ARTIFACT_DIR", str(tmp_path / "artifacts")
    )
    _drain(jobs._queue)
    yield
    _drain(jobs._queue)
