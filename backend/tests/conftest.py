"""Suite-wide isolation. Two needs, from two modules, neither of which a test
should have to remember.

1. **Storage → `tmp_path`** (M15). `enqueue_run` / `run_pipeline` write SQLite
   rows and artifacts, and Convention 3 (docs/test-suite.md) requires the repo
   tree to stay unpolluted — no `./attestation.db`, no `./artifacts/`. The
   database is redirected at `app.db.DATABASE_URL` — db.py's own contract:
   tests patch the consumer module, never `os.environ` (Convention 2). The
   module-level job queue is drained around each test, because
   `test_pipeline.py`'s queue characterization asserts it starts empty and the
   webhook tests now enqueue for real.

2. **An attestor-gated run has to be startable** (M12). `run_pipeline` refuses a
   run it cannot prove read-only, and refuses one launched without a capability
   declaration, so every test that runs a pipeline needs both — otherwise the
   suite would only be testing refusals nobody asked for. The workspace lives
   under `tmp_path` and is restored on the way out, because provisioning takes
   away the ability to write and pytest's cleanup needs that ability back.

   Set `ATTESTOR_CAPS=""` or point `ATTESTOR_WORKSPACE` elsewhere to see the
   refusals; that is what the gate tests in `test_pipeline.py` do.

Ownership note: `backend/tests/` is M17's path (modules.md §0.2). This file was
M15-session-created (the M3 deviation pattern) and M12 appended its fixture
rather than replacing it.
"""
import pytest

from app import db
from app.attestor.sandbox import ensure_readonly_workspace, restore_workspace_writable
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


@pytest.fixture(autouse=True)
def attestor_workspace(tmp_path_factory, monkeypatch):
    """A read-only workspace under tmp_path, provisioned for this test.

    The function-scoped `monkeypatch` keeps the environment isolated per test,
    and the restore runs in `finally` so a test that fails mid-provisioning
    still hands a writable directory back to pytest.
    """
    workspace = tmp_path_factory.mktemp("attestor")
    monkeypatch.setenv(
        "ATTESTOR_CAPS", "read, subagent, skill, workflow, llm_egress"
    )
    monkeypatch.setenv("ATTESTOR_WORKSPACE", str(workspace))
    try:
        ensure_readonly_workspace(workspace)
        yield workspace
    finally:
        restore_workspace_writable(workspace)
