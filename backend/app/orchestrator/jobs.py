"""In-process asyncio job queue — no worker infra for 48h build.

Queue item envelope (set by pipeline.enqueue_run):
    {"run_id": "run-xxxxxxxx", "payload": {...}}
A worker also tolerates a raw payload dict (anything without a "payload" key),
so pre-envelope submissions keep working.
"""
import asyncio

_queue: asyncio.Queue = asyncio.Queue()


async def worker() -> None:
    from .pipeline import run_pipeline

    while True:
        item = await _queue.get()
        try:
            if isinstance(item, dict) and "payload" in item:
                run_id, payload = item.get("run_id"), item["payload"]
            else:
                run_id, payload = None, item
            try:
                run_pipeline(payload, run_id=run_id)
            except Exception as exc:  # noqa: BLE001 — deliberate boundary
                # run_pipeline has already flipped the run to `failed` and
                # re-raised. One bad run must not kill the worker: a dead
                # worker would stall every future run silently.
                print(f"jobs: run {run_id or '(unknown)'} failed: {exc!r}", flush=True)
        finally:
            _queue.task_done()


def submit(payload: dict) -> None:
    _queue.put_nowait(payload)
