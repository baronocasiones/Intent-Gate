"""Pipeline + job queue — R1 (refactor plan): the loop is WIRED.

`enqueue_run` persists a `queued` row and submits the work item; the worker
runs the chain off-loop under the read-only capability check and the app
lifespan starts/stops it. The two §11.1 characterizations flipped with the
wiring in the same change (rule 7); the guards below pin the wired behavior
and must be updated deliberately if it ever changes again.
"""
import asyncio
import contextlib
import os
import re
from pathlib import Path

import pytest

import app.db as db_mod
import app.store.artifacts as artifacts_mod
from app.attestor.policy import (
    ATTESTOR_CAPS_ENV,
    GRANTS,
    assert_read_only,
    resolve_worker_caps,
)
from app.db import get_db, get_run, list_runs
from app.orchestrator import jobs, persistence
from app.orchestrator.pipeline import enqueue_run, run_pipeline


def test_run_pipeline_chains_all_six_stages_to_emit():
    out = run_pipeline({"pr": 142})
    assert out["stage"] == "emit"
    assert out["ok"] is True
    # Gate default: non-zero exit blocks merge (§4.4)
    assert out["exit_code"] == 1
    # FLIPPED 2026-09-27 (Session 25 seam fix, found by the cold E2E): these
    # two lines pinned M9's nested `record` wrapper, which the committed
    # consumers of a run record all miss — `run.schema.json`, M14's
    # `project_run_payload`, and M15's `runs.py`. The artifact was correct
    # while `GET /api/runs/{id}` served `pending` + `[]`. The adjudicate
    # verdict is now echoed at the top level; `stage` is emit's own, per the
    # same convention every other stage in the chain follows.
    assert out["verdict"] == "PENDING"
    assert out["status"] == "pending"


def test_run_pipeline_feeds_payload_through_every_stage():
    """ingest sees the raw payload keys; later stages receive prior output.

    Proven via ingest's input_keys echo surviving in the chain: only stage 1
    reads the raw payload, everything downstream is shaped stub data.
    """
    out = run_pipeline({"b": 1, "a": 2})
    assert out["stage"] == "emit"
    assert out["verdict"] == "PENDING"  # flipped 2026-09-27 — see above


def test_pure_run_pipeline_writes_no_rows():
    """D-b, second half: `run_id=None` is pure — no row, no artifact."""
    run_pipeline({"pr": 142})
    with contextlib.closing(get_db()) as conn:
        assert list_runs(conn) == []


def test_enqueue_run_id_format():
    run_id = enqueue_run({})
    assert re.fullmatch(r"run-[0-9a-f]{8}", run_id)


def test_enqueue_run_ids_unique():
    ids = {enqueue_run({}) for _ in range(50)}
    assert len(ids) == 50


def test_enqueue_run_persists_queued_row():
    run_id = enqueue_run({"pr": 142})
    with contextlib.closing(get_db()) as conn:
        row = get_run(conn, run_id)
    assert row is not None
    assert row["status"] == "queued"
    assert row["artifact_path"] is None


def test_run_pipeline_transitions_queued_running_pending():
    run_id = enqueue_run({"pr": 142})
    out = run_pipeline({"pr": 142}, run_id)
    assert out["stage"] == "emit" and out["ok"] is True
    with contextlib.closing(get_db()) as conn:
        row = get_run(conn, run_id)
    assert row["status"] == "pending"
    assert row["artifact_path"] is not None
    assert Path(row["artifact_path"]).is_file()


def test_stage_raise_stores_blocking_failure(monkeypatch):
    """AC3 / rule 6: a crash must never read as CERTIFIED — the failure is
    stored (row `failed` + artifact with the detail) and returned."""
    import app.gates.parse as parse_mod

    def boom(ast):
        raise ValueError("gherkin exploded")

    monkeypatch.setattr(parse_mod, "run", boom)
    run_id = "run-stage-fail-1"
    persistence.mark_queued(run_id)
    out = run_pipeline({"pr": 1}, run_id)
    assert out == {
        "run_id": run_id,
        "stage": "parse",
        "ok": False,
        "exit_code": 1,
        "error": "ValueError: gherkin exploded",
    }
    with contextlib.closing(get_db()) as conn:
        row = get_run(conn, run_id)
    assert row["status"] == "failed"
    assert Path(row["artifact_path"]).is_file()


def test_missing_row_skips_stages_and_still_blocks(monkeypatch):
    """Row absent at `mark_running` (rule-6 anomaly): stages never run, but
    the blocking record is still written to disk — a lost run is durable."""
    import app.gates.ingest as ingest_mod

    def never(payload):
        raise AssertionError("stages must not run without a row")

    monkeypatch.setattr(ingest_mod, "run", never)
    out = run_pipeline({}, "run-ghost-1")
    assert out["stage"] == "orchestrator"
    assert out["ok"] is False and out["exit_code"] == 1
    with contextlib.closing(get_db()) as conn:
        assert get_run(conn, "run-ghost-1") is None
    assert Path(artifacts_mod.ARTIFACT_DIR, "run-ghost-1.json").is_file()


def test_persistence_redirect_is_active(tmp_path):
    """Proves the conftest redirect (Convention 3): the row and the artifact
    land under `tmp_path`, never the repo tree."""
    run_id = enqueue_run({"pr": 142})
    run_pipeline({"pr": 142}, run_id)
    assert str(tmp_path) in db_mod.DATABASE_URL
    assert Path(artifacts_mod.ARTIFACT_DIR).parent == tmp_path
    with contextlib.closing(get_db()) as conn:
        row = get_run(conn, run_id)
    assert row["status"] == "pending"
    assert Path(row["artifact_path"]).is_file()


def test_jobs_submit_enqueues_a_work_item_and_drains_cleanly():
    """submit() builds the {"run_id", "payload"} work item; the queue stays
    clean — drained here and by conftest (AC5)."""
    assert jobs._queue.qsize() == 0
    jobs.submit("run-deadbeef", {"pr": 142})
    assert jobs._queue.qsize() == 1
    got = jobs._queue.get_nowait()
    jobs._queue.task_done()
    assert got == {"run_id": "run-deadbeef", "payload": {"pr": 142}}
    assert jobs._queue.qsize() == 0


def test_launch_caps_default_resolves_to_grants(monkeypatch):
    """The launch-site default IS the GRANTS set (D-g) — order-independent:
    re-apply the setdefault after clearing, then vet the real startup path."""
    monkeypatch.delenv(ATTESTOR_CAPS_ENV, raising=False)
    os.environ.setdefault(ATTESTOR_CAPS_ENV, jobs._LAUNCH_CAPS)
    caps = resolve_worker_caps(os.environ.get(ATTESTOR_CAPS_ENV))
    assert caps == GRANTS
    assert_read_only(caps)  # the worker-startup call — must not raise


async def test_worker_with_poisoned_caps_refuses_before_consuming(monkeypatch):
    """D-g fail-closed: a foreign declaration refuses startup — and the
    queued item is untouched, proving the check runs BEFORE consuming.

    The 5s bound is load-bearing, not belt-and-braces. `worker()` is an
    unbounded loop that exits on the `None` sentinel, and this test queues one
    item and deliberately no sentinel — so the gate raising is the only thing
    that can end the call. Remove `assert_read_only` from `worker()` and the
    loop consumes the item, then blocks forever on `await q.get()`: the suite
    HANGS instead of failing, which is how this was found (a mutation run that
    had to be killed by timeout rather than reporting a victim).

    `asyncio.wait_for` converts that hang into a `TimeoutError`, which is not a
    `PermissionError`, so `pytest.raises` fails with a real traceback naming
    this test. It does not weaken the assertion: with the gate present the
    `PermissionError` still propagates immediately and is still what is
    required. Proven: the gate-removal mutation now kills this test instead of
    timing the harness out.
    """
    monkeypatch.setenv(ATTESTOR_CAPS_ENV, "edit")
    q: asyncio.Queue = asyncio.Queue()
    q.put_nowait({"run_id": "run-poison-1", "payload": {}})
    with pytest.raises(PermissionError):
        await asyncio.wait_for(jobs.worker(queue=q), timeout=5)
    assert q.qsize() == 1


async def test_worker_processes_item_then_stops_on_sentinel():
    """The worker runs the item through the full persist path and exits on
    the `None` sentinel — the lifespan's cooperative shutdown, deterministic
    with no timing involved."""
    run_id = "run-worker-1"
    persistence.mark_queued(run_id)
    q: asyncio.Queue = asyncio.Queue()
    q.put_nowait({"run_id": run_id, "payload": {"pr": 7}})
    q.put_nowait(None)
    await jobs.worker(queue=q)  # returns after the sentinel
    with contextlib.closing(get_db()) as conn:
        row = get_run(conn, run_id)
    assert row["status"] == "pending"
    assert q.qsize() == 0


async def test_worker_with_preset_stop_consumes_nothing():
    """A pre-set stop ends the loop before the first take — no consume."""
    q: asyncio.Queue = asyncio.Queue()
    q.put_nowait({"run_id": "run-stop-1", "payload": {}})
    stop = asyncio.Event()
    stop.set()
    await jobs.worker(queue=q, stop=stop)
    assert q.qsize() == 1


def test_worker_is_started_by_app_lifespan():
    """§11.1 FLIPPED (R1): the lifespan starts the worker off the request
    path and stops it cooperatively on shutdown. Rewritten on purpose — the
    unwired-queue gap this test used to pin is closed."""
    from fastapi.testclient import TestClient

    from app import main
    from app.main import app

    assert "jobs" in vars(main)  # lifespan wiring lives in main
    with TestClient(app) as client:
        task = app.state.worker_task
        assert task is not None and not task.done()
        assert client.get("/health").status_code == 200
    assert task.done() and not task.cancelled()  # cooperative, not cancelled
