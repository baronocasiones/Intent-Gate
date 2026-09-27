"""FastAPI entry — serves API + React dashboard (fixture fallback)."""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import os

from .orchestrator import jobs
from .routers import webhooks, runs, metrics


@asynccontextmanager
async def _lifespan(app: FastAPI):
    """R1: run the attestation worker off the request path. Shutdown is
    cooperative (stop event + sentinel — never cancellation), so an
    in-flight run finishes its write before the task ends."""
    stop = asyncio.Event()
    app.state.worker_task = asyncio.create_task(jobs.worker(stop=stop))
    try:
        yield
    finally:
        stop.set()
        await jobs._queue.put(None)
        await app.state.worker_task


app = FastAPI(title="Intent Attestation Gate", version="0.1.0", lifespan=_lifespan)

app.include_router(webhooks.router)
app.include_router(runs.router)
app.include_router(metrics.router)


@app.get("/health")
def health() -> JSONResponse:
    return JSONResponse({"ok": True, "service": "intent-attestation-gate"})


# Serve built frontend when present; API-first otherwise.
def _dashboard_dir() -> str:
    """`<repo>/frontend/dist` — two levels up from `backend/app` (M15's _dist
    fix: the old three-level climb landed outside the project, so the mount
    silently never activated)."""
    here = os.path.dirname(__file__)
    return os.path.abspath(os.path.join(here, "..", "..", "frontend", "dist"))


def mount_dashboard(target_app: FastAPI, dist_dir: str | None = None) -> bool:
    """Mount a built dashboard, returning whether anything was mounted."""
    dist = dist_dir or _dashboard_dir()
    if os.path.isdir(dist):
        target_app.mount("/", StaticFiles(directory=dist, html=True), name="dashboard")
        return True
    return False


_dist = _dashboard_dir()
mount_dashboard(app)
