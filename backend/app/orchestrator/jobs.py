"""In-process asyncio job queue — no worker infra for 48h build."""
import asyncio
import logging
import os

from ..attestor.policy import (
    ATTESTOR_CAPS_ENV,
    assert_read_only,
    resolve_worker_caps,
)

_log = logging.getLogger(__name__)

# Launch-site capability default (D-g): the five GRANTS tokens, exactly as
# policy.py's docstring prescribes. `setdefault` keeps an operator override
# intact — resolve + assert still vet it at worker startup, so a narrower or
# foreign declaration fails closed *there* instead of silently here.
_LAUNCH_CAPS = "read, subagent, skill, workflow, llm_egress"
os.environ.setdefault(ATTESTOR_CAPS_ENV, _LAUNCH_CAPS)

_queue: asyncio.Queue = asyncio.Queue()


async def worker(
    queue: asyncio.Queue | None = None, stop: asyncio.Event | None = None
) -> None:
    """Consume work items off the request path (D-c, D-d, D-f: pool of one).

    Capability check FIRST (D-g): a worker that cannot prove it is read-only
    refuses to start — before touching the queue. Each item runs via
    `asyncio.to_thread` so the loop never blocks on sqlite/JSON I/O.
    Per-run failures are logged and survived, never silently dropped
    (`except Exception` deliberately lets `CancelledError` through).

    Shutdown is cooperative, never cancellation: `stop` set + a `None`
    sentinel (or a pre-set `stop` before the first take) ends the loop after
    `task_done` stays balanced.
    """
    assert_read_only(resolve_worker_caps(os.environ.get(ATTESTOR_CAPS_ENV)))
    from .pipeline import run_pipeline

    q = queue if queue is not None else _queue
    while True:
        if stop is not None and stop.is_set():
            return
        item = await q.get()
        try:
            if item is None:  # shutdown sentinel — never a real run
                return
            await asyncio.to_thread(run_pipeline, item["payload"], item["run_id"])
        except Exception:
            _log.exception("worker: run failed; the loop survives")
        finally:
            q.task_done()


def submit(run_id: str, payload: dict) -> None:
    """Enqueue one unit of work. `put_nowait` — no loop needed, so neither
    the webhook path nor the tests ever block on submit."""
    _queue.put_nowait({"run_id": run_id, "payload": payload})
