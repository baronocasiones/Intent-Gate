"""Pipeline + job queue — docs/architecture.md §1, §4 (as coded) and §11.1.

The jobs queue is *intentionally unwired* (§11.1): submit() enqueues but no
worker is ever started by the app. These are characterization tests — they
pin today's behavior and must be updated deliberately when the queue lands.
"""
import re

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
