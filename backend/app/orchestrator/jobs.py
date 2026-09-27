"""In-process asyncio job queue — no worker infra for 48h build.

The worker catches what a run raises and keeps going. That boundary is not
decorative: `run_pipeline` now refuses a run it cannot prove read-only, and an
uncaught refusal here would end this task. The queue would then keep accepting
submissions that nothing ever consumes, so a refused run would look exactly
like a run that is still working — a fail-open built out of an exception
handler that was never written.
"""
import asyncio

_queue: asyncio.Queue = asyncio.Queue()


async def worker() -> None:
    from .pipeline import run_pipeline

    while True:
        payload = await _queue.get()
        try:
            try:
                run_pipeline(payload)
            except Exception as exc:  # noqa: BLE001 — deliberate boundary
                # One refused or failed run must not kill the worker. The
                # refusal is reported rather than swallowed: a run that could
                # not be gated is exactly the thing an operator must see.
                print(f"jobs: run refused or failed: {exc!r}", flush=True)
        finally:
            _queue.task_done()


def submit(payload: dict) -> None:
    _queue.put_nowait(payload)
