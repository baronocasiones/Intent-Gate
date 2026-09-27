"""Autouse isolation for every test in this suite.

Two things, both of which a test should never have to remember.

1. **Storage → `tmp_path`.** No test may write a database, an artefact or a
   directory into the repository tree (docs/test-suite.md Convention 3); the
   pre-commit cleanliness gate depends on it. Paths are patched on the modules
   that read them, which is the consumer-module rule (Convention 2), not via
   `os.environ`.

2. **An attestor-gated run has to be startable.** `run_pipeline` refuses a run
   that cannot prove its workspace read-only and that was launched without a
   capability declaration, so every test that runs a pipeline needs both, or it
   would be testing a refusal it did not ask for. The workspace lives under
   `tmp_path` and is restored on the way out, because provisioning takes away
   the ability to write and pytest's cleanup needs that ability back.

   Set `ATTESTOR_CAPS=""` or point `ATTESTOR_WORKSPACE` elsewhere to see the
   refusals; that is what the gate tests in `test_pipeline.py` do.
"""
import os

import pytest


@pytest.fixture(autouse=True)
def attestor_workspace(tmp_path_factory, monkeypatch):
    """A read-only workspace under tmp_path, provisioned for this test.

    The function-scoped `monkeypatch` keeps the environment isolated per test,
    and the restore runs in `finally` so a test that fails mid-provisioning
    still hands a writable directory back to pytest.
    """
    from app.attestor.sandbox import ensure_readonly_workspace, restore_workspace_writable

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


@pytest.fixture(autouse=True)
def storage_isolated(tmp_path, monkeypatch):
    """Keep DB and artefact writes inside the test's own tmp_path."""
    monkeypatch.setattr("app.store.artifacts.ARTIFACT_DIR", str(tmp_path / "artifacts"))
    yield
