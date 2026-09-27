"""Suite-wide isolation for the M15 persistence slice.

M15 made `enqueue_run` / `run_pipeline` write SQLite rows and artifacts
(docs/modules.md M15 core slice). Convention 3 (docs/test-suite.md) requires
the repo tree to stay unpolluted — no `./attestation.db`, no `./artifacts/` —
so every test runs against tmp storage, and the module-level job queue is
drained around each test (`test_pipeline.py`'s queue characterization asserts
it starts empty, and webhook tests now enqueue for real).

The database is redirected at `app.db.DATABASE_URL` — db.py's own contract:
tests patch the consumer module, never `os.environ` (Convention 2). A bare
path passes through `db._sqlite_path` untouched. (Pre-rewire this file
patched `pipeline.DB_PATH`, a shim point that no longer exists.)

Ownership note: `backend/tests/` is M17's path (modules.md §0.2). This file is
new and M15-session-created — the same pattern M3 used when it added
`test_models_parity.py` rather than editing another owner's file (modules.md
§M3 deviation note).
"""
import pytest

from app import db
from app.orchestrator import jobs
from app.store import artifacts


def _drain_queue() -> None:
    while not jobs._queue.empty():
        jobs._queue.get_nowait()
        jobs._queue.task_done()


@pytest.fixture(autouse=True)
def _isolate_persistence(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DATABASE_URL", str(tmp_path / "attestation.db"))
    monkeypatch.setattr(artifacts, "ARTIFACT_DIR", str(tmp_path / "artifacts"))

    _drain_queue()
    yield
    _drain_queue()
