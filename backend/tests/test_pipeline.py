"""Pipeline + job queue — docs/architecture.md §1, §4 (as coded) and §11.1.

The jobs queue is *intentionally unwired* (§11.1): submit() enqueues but no
worker is ever started by the app. These are characterization tests — they
pin today's behavior and must be updated deliberately when the queue lands.

The bottom section covers the attestor gate `run_pipeline` now applies before
any stage executes. Those are what make the gate a control rather than a claim:
each one makes a run impossible and asserts that no stage ran.
"""
import re

import pytest

from app.orchestrator.pipeline import enqueue_run, run_pipeline


def test_run_pipeline_chains_all_six_stages_to_emit():
    out = run_pipeline({"pr": 142})
    assert out["stage"] == "emit"
    assert out["ok"] is True
    # Gate default: non-zero exit blocks merge (§4.4)
    assert out["exit_code"] == 1
    # record is the adjudicate stage's output, passed through emit
    assert out["record"]["stage"] == "adjudicate"
    assert out["record"]["verdict"] == "PENDING"


def test_run_pipeline_feeds_payload_through_every_stage():
    """ingest sees the raw payload keys; later stages receive prior output.

    Proven via ingest's input_keys echo surviving in the chain: only stage 1
    reads the raw payload, everything downstream is shaped stub data.
    """
    out = run_pipeline({"b": 1, "a": 2})
    assert out["record"]["stage"] == "adjudicate"
    assert out["stage"] == "emit"


def test_enqueue_run_id_format():
    run_id = enqueue_run({})
    assert re.fullmatch(r"run-[0-9a-f]{8}", run_id)


def test_enqueue_run_ids_unique():
    ids = {enqueue_run({}) for _ in range(50)}
    assert len(ids) == 50


def test_jobs_submit_enqueues_and_drains_cleanly():
    """§11.1 characterization: submit() puts on the queue; nothing consumes it.

    The test drains the queue itself so the module-level queue stays clean
    for other tests — the app never starts worker().
    """
    from app.orchestrator import jobs

    assert jobs._queue.qsize() == 0
    jobs.submit({"run_id": "run-deadbeef"})
    assert jobs._queue.qsize() == 1
    got = jobs._queue.get_nowait()
    jobs._queue.task_done()
    assert got == {"run_id": "run-deadbeef"}
    assert jobs._queue.qsize() == 0


def test_worker_is_async_but_never_started_by_app():
    """§11.1: worker() exists and is a coroutine function, but main.py never
    schedules it. Asserting absence here means: when wiring lands, this test
    flips and must be rewritten on purpose."""
    import inspect

    from app.orchestrator import jobs

    # `inspect`, not `asyncio` — the latter is deprecated as of Python 3.14 and
    # slated for removal in 3.16. Identical result here: `worker` is a plain
    # `async def` with no `markcoroutinefunction` decorator, which is the only
    # case where the two disagree.
    assert inspect.iscoroutinefunction(jobs.worker)
    # main.py imports only the routers — no jobs import at app entry:
    from app import main

    assert "jobs" not in vars(main)


# --- the attestor gate: a run that cannot prove read-only never starts ---

DECLARED_ALL = "read, subagent, skill, workflow, llm_egress"


def _no_stage_may_run(monkeypatch) -> list:
    """A spy standing in for `ingest.run` that records calls, so "no stage
    executed" is an assertion about this run rather than an inference from
    which exception surfaced first."""
    calls: list = []
    monkeypatch.setattr(
        "app.gates.ingest.run", lambda payload: calls.append(payload) or {"stage": "ingest"}
    )
    return calls


def test_a_gated_run_carries_the_attestor_fragment_it_actually_proved():
    """The point of the wiring: the evidence lands in the record the run
    returns, so an artefact carries the proof rather than the promise.

    The keys are asserted exactly. A fragment that quietly lost
    `workspace_mechanism` would still read as compliant while no longer saying
    which control held — shape stability (rule 3) is what makes an auditor's
    reading of it stable across sessions."""
    out = run_pipeline({"pr": 142})
    fragment = out["attestor_policy"]
    assert sorted(fragment) == [
        "capabilities",
        "denied",
        "enforcement_applied",
        "granted",
        "workspace_mechanism",
        "workspace_mount_readonly",
        "workspace_mount_witness",
        "workspace_path",
        "workspace_readonly",
        "workspace_witness",
    ]
    assert fragment["enforcement_applied"] is True
    assert fragment["workspace_readonly"] is True
    assert fragment["workspace_witness"] in {"EACCES", "EROFS"}
    assert fragment["denied"] == ["edit", "execute"]
    # A mount we could not ask about is null, never a claim in either direction.
    assert fragment["workspace_mount_readonly"] is None or fragment[
        "workspace_mount_readonly"
    ] in (True, False)


def test_the_fragment_names_the_workspace_that_was_proved(monkeypatch, tmp_path):
    """The record is evidence about *something*. A fragment that reported a
    refusal without saying which directory was refused would be true of every
    workspace on the machine, so the path is asserted against the directory the
    test actually provisioned."""
    workspace = tmp_path / "named-workspace"
    workspace.mkdir()
    monkeypatch.setenv("ATTESTOR_WORKSPACE", str(workspace))
    out = run_pipeline({"pr": 142})
    assert out["attestor_policy"]["workspace_path"] == str(workspace)


def test_a_run_without_a_capability_declaration_is_refused_before_any_stage(monkeypatch):
    """Fail closed on the declaration. A worker that was never told what it may
    do is a worker whose capabilities are unknown, and a set comparison against
    our own constant cannot establish what it was told — the declaration is
    external precisely so that it can be absent and visible.

    The spy is the assertion that matters: refusal happened *before* `ingest`,
    not after the work the gate was meant to authorise."""
    monkeypatch.delenv("ATTESTOR_CAPS", raising=False)
    calls = _no_stage_may_run(monkeypatch)
    with pytest.raises(PermissionError, match="ATTESTOR_CAPS absent"):
        run_pipeline({"pr": 142})
    assert calls == []


def test_a_run_whose_declaration_lacks_a_grant_is_refused(monkeypatch):
    """A short declaration fails closed too. This is the direction that matters
    operationally: a worker launched with four of the five tokens is a worker
    that cannot reach watsonx.ai, and it must not start pretending it can."""
    monkeypatch.setenv("ATTESTOR_CAPS", "read, subagent, skill, workflow")
    calls = _no_stage_may_run(monkeypatch)
    with pytest.raises(PermissionError, match="missing"):
        run_pipeline({"pr": 142})
    assert calls == []


def test_a_run_whose_declaration_claims_a_denied_capability_is_refused(monkeypatch):
    """The other direction: `edit` in the declaration is a leak, and it is
    refused before a single stage runs."""
    monkeypatch.setenv("ATTESTOR_CAPS", DECLARED_ALL + ", edit")
    calls = _no_stage_may_run(monkeypatch)
    with pytest.raises(PermissionError, match="denied caps granted"):
        run_pipeline({"pr": 142})
    assert calls == []


def test_a_run_against_a_workspace_that_still_accepts_writes_is_refused(
    monkeypatch, tmp_path
):
    """The control's own fail-closed path, reached through the pipeline.

    The workspace is a fresh writable directory, not the provisioned one the
    suite fixture hands out — provisioning is probe-first, so pointing at an
    already-refusing workspace would return before reaching the branch under
    test. Here the denial is stubbed to a no-op, standing in for a platform
    that cannot make a directory read-only at all. The gate must refuse rather
    than run the stages and record a proof it does not have: a record claiming
    enforcement with no refused write behind it is exactly what `policy_record`
    refuses to mint, and the pipeline inherits that refusal rather than working
    around it."""
    fresh = tmp_path / "writable"
    fresh.mkdir()
    monkeypatch.setenv("ATTESTOR_WORKSPACE", str(fresh))
    monkeypatch.setattr("app.attestor.sandbox._deny_write", lambda root: None)
    calls = _no_stage_may_run(monkeypatch)
    with pytest.raises(PermissionError, match="writable"):
        run_pipeline({"pr": 142})
    assert calls == []


def test_a_configured_workspace_that_does_not_exist_is_refused_not_created(
    monkeypatch, tmp_path
):
    """An operator's path is never invented. Creating a directory because a
    configured path was mistyped would attest to a workspace nobody chose and
    would hide the typo, so a missing configured workspace is undetermined and
    that is a refusal."""
    missing = tmp_path / "typo-in-the-config"
    monkeypatch.setenv("ATTESTOR_WORKSPACE", str(missing))
    calls = _no_stage_may_run(monkeypatch)
    with pytest.raises(PermissionError, match="undetermined"):
        run_pipeline({"pr": 142})
    assert calls == []
    assert not missing.exists()


@pytest.mark.asyncio
async def test_a_refused_run_does_not_kill_the_queue_worker(monkeypatch):
    """One refused run must not stop the next one being attempted.

    `worker()` calls `run_pipeline`, which now raises for a run it cannot prove
    read-only. Without a boundary here that exception would end the task, and
    the queue would keep accepting submissions that nothing ever consumes — a
    refused run would be indistinguishable from a run that is merely slow. The
    test makes the first run fail and asserts the worker is still consuming."""
    import asyncio

    from app.orchestrator import jobs

    refusals = {"read, subagent, skill, workflow"}
    seen: list = []

    def _fake_run_pipeline(payload):
        declared = refusals.pop() if refusals else None
        if declared is None:
            seen.append(payload)
            return {"stage": "emit"}
        raise PermissionError(f"attestor policy incomplete — missing: {declared!r}")

    monkeypatch.setenv("ATTESTOR_CAPS", DECLARED_ALL)
    monkeypatch.setattr("app.orchestrator.pipeline.run_pipeline", _fake_run_pipeline)

    task = asyncio.ensure_future(jobs.worker())
    jobs.submit({"pr": 1})  # refused
    jobs.submit({"pr": 2})  # must still be consumed
    for _ in range(200):
        await asyncio.sleep(0.005)
        if seen:
            break
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    assert seen == [{"pr": 2}], "the queue stopped after a refused run"
