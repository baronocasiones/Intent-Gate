"""FastAPI entry — serves API + React dashboard (fixture fallback)."""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import os

from .routers import webhooks, runs, metrics

app = FastAPI(title="Intent Attestation Gate", version="0.1.0")

app.include_router(webhooks.router)
app.include_router(runs.router)
app.include_router(metrics.router)


@app.get("/health")
def health() -> JSONResponse:
    return JSONResponse({"ok": True, "service": "intent-attestation-gate"})


# Serve built frontend when present; API-first otherwise.
_dist = os.path.join(os.path.dirname(__file__), "..", "..", "..", "frontend", "dist")
_dist = os.path.abspath(_dist)
if os.path.isdir(_dist):
    app.mount("/", StaticFiles(directory=_dist, html=True), name="dashboard")
