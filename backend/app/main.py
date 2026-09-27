"""FastAPI entry — serves API + React dashboard (fixture fallback).

Owns the two integration points that only this file may change (modules.md
§0.4): the static mount (this session fixes the _dist climb — it went three
levels up from backend/app/, landing outside the project, so the mount never
activated even with a built dashboard) and the app lifespan that starts the
jobs worker (M10's wiring request, filed through M15 because M15 owns this
file).
"""
import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from .routers import webhooks, runs, metrics
from .orchestrator import jobs

# Set while the lifespan runs; None otherwise (tests pin both states).
_worker_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _worker_task
    _worker_task = asyncio.create_task(jobs.worker())
    try:
        yield
    finally:
        # Shutdown: cancel at the next await point. run_pipeline is fully
        # synchronous, so at most one in-flight run finishes first — the queue
        # item it holds is task_done()'d by worker()'s finally either way.
        _worker_task.cancel()
        try:
            await _worker_task
        except asyncio.CancelledError:
            pass
        _worker_task = None


app = FastAPI(title="Intent Attestation Gate", version="0.1.0", lifespan=lifespan)

app.include_router(webhooks.router)
app.include_router(runs.router)
app.include_router(metrics.router)


@app.get("/health")
def health() -> JSONResponse:
    return JSONResponse({"ok": True, "service": "intent-attestation-gate"})


def _resolve_dist() -> str:
    """Project's frontend/dist — TWO levels up from backend/app/ (the old
    climb went three and silently landed outside the repository)."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))


def mount_dashboard(app: FastAPI, dist: str | None = None) -> bool:
    """Mount the built dashboard at / when `dist` exists; API-first otherwise.

    Split out of module scope so a test can prove the mount activates (the
    honest fix for the defect, per modules.md M15) instead of the old silent
    isdir check. Returns whether the mount happened.
    """
    target = _resolve_dist() if dist is None else dist
    if os.path.isdir(target):
        app.mount("/", StaticFiles(directory=target, html=True), name="dashboard")
        return True
    return False


# Serve built frontend when present; API-first otherwise. Registered last, so
# every API route above still wins over the "/" catch-all.
mount_dashboard(app)
