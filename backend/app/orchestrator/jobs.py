"""In-process asyncio job queue — no worker infra for 48h build."""
import asyncio

_queue: asyncio.Queue = asyncio.Queue()


async def worker() -> None:
    from .pipeline import run_pipeline

    while True:
        payload = await _queue.get()
        try:
            run_pipeline(payload)
        finally:
            _queue.task_done()


def submit(payload: dict) -> None:
    _queue.put_nowait(payload)
