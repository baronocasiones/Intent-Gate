"""Pipeline + job queue — docs/architecture.md §1, §4 (as coded) and §11.1.

The jobs queue was *intentionally unwired* (§11.1) until the M15 core slice:
`enqueue_run` now persists a `queued` row and submits, and the app lifespan
starts `worker()`. The old "worker is never started by the app" characterization
flipped in the same change (modules.md rule 7) — it now pins the wiring instead
of its absence.
"""
import json
import re
from pathlib import Path

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
    """§11.1 characterization — FLIPPED (M15 core slice, rule 7).

    The old claim ("submit() puts on the queue; nothing consumes it … the app
    never starts worker()") is no longer true: main.py's lifespan starts
    worker(), which consumption is pinned by
    `test_worker_is_coroutinefunction_and_lifespan_starts_it`. What stands:
    submit() puts exactly one envelope on the queue, and this test still
    drains it itself so the module-level queue stays clean for other tests.
    """
    from app.orchestrator import jobs

    assert jobs._queue.qsize() == 0
    jobs.submit({"run_id": "run-deadbeef"})
    assert jobs._queue.qsize() == 1
    got = jobs._queue.get_nowait()
    jobs._queue.task_done()
    assert got == {"run_id": "run-deadbeef"}
    assert jobs._queue.qsize() == 0


def test_worker_is_coroutinefunction_and_lifespan_starts_it():
    """FLIPPED (M15 core slice): worker() is started by main.py's lifespan and
    cancelled again at shutdown. The old assertion (`"jobs" not in vars(main)`)
    pinned the unwired queue and was rewritten deliberately (rule 7)."""
    import inspect

    from fastapi.testclient import TestClient

    from app.orchestrator import jobs

    # `inspect`, not `asyncio` — the latter is deprecated as of Python 3.14 and
    # slated for removal in 3.16. Identical result here: `worker` is a plain
    # `async def` with no `markcoroutinefunction` decorator, which is the only
    # case where the two disagree.
    assert inspect.iscoroutinefunction(jobs.worker)
    from app import main

    assert "jobs" in vars(main)  # lifespan wiring lives in main.py (M15 owns it)

    with TestClient(main.app):
        assert main._worker_task is not None
        assert not main._worker_task.done()
    # shutdown cancels the task and clears the handle
    assert main._worker_task is None


def test_enqueue_run_persists_queued_row_and_submits():
    """M15 core slice: the id is no longer minted into the void — the row is
    listable immediately and the queue gains exactly one item."""
    from app.orchestrator import jobs, pipeline

    before = jobs._queue.qsize()
    run_id = enqueue_run({"pr": 1})

    assert jobs._queue.qsize() == before + 1
    row = pipeline.fetch_run_row(run_id)
    assert row is not None
    assert row["status"] == "queued"
    assert row["artifact_path"] is None


def test_run_pipeline_persists_row_and_artifact():
    """The synchronous path persists exactly like the queued one: row flipped
    to the lowercased verdict (D9 default), artifact written with a sha256."""
    from app.orchestrator import pipeline

    run_id = enqueue_run({"pr": 7})
    run_pipeline({"pr": 7}, run_id=run_id)

    row = pipeline.fetch_run_row(run_id)
    assert row["status"] == "pending"  # stub verdict PENDING -> D9 lowercase
    assert row["artifact_path"] is not None

    data = json.loads(Path(row["artifact_path"]).read_text(encoding="utf-8"))
    assert data["stage"] == "emit"
    assert data["exit_code"] == 1  # fail-closed default (§1.5)
    assert len(data["sha256"]) == 64


def test_run_pipeline_marks_run_failed_when_a_stage_raises(monkeypatch):
    """Rule 6: a crash must not leave a run looking alive or certified. The
    exception still propagates — it is never swallowed to get to green."""
    from app.orchestrator import pipeline

    class Boom:
        @staticmethod
        def run(payload):
            raise RuntimeError("stage exploded")

    monkeypatch.setattr(pipeline, "ingest", Boom)

    run_id = enqueue_run({})
    with pytest.raises(RuntimeError, match="stage exploded"):
        run_pipeline({}, run_id=run_id)

    assert pipeline.fetch_run_row(run_id)["status"] == "failed"
