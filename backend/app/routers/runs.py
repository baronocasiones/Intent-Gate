"""GET /api/runs — list + detail (M15 reads M14's index + artifacts).

List serves the index newest-first. Detail merges the row (the lifecycle
status, D-e) with the run's artifact (verdicts/measured when the chain has
written one); unknown ids 404. Reads are defensive `.get()`s, so stub-shaped
artifacts serve honestly today and contracted ones serve unchanged tomorrow —
no branch on producer shape, ever.
"""
from fastapi import APIRouter, HTTPException

from ..db import get_db, get_run, list_runs
from ..store.records import read_artifact

router = APIRouter(prefix="/api/runs")


@router.get("")
def list_runs_endpoint():
    conn = get_db()
    try:
        rows = list_runs(conn)
    finally:
        conn.close()
    return {"runs": [{"run_id": row["id"], "status": row["status"]} for row in rows]}


@router.get("/{run_id}")
def get_run_endpoint(run_id: str):
    conn = get_db()
    try:
        row = get_run(conn, run_id)
    finally:
        conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail=f"unknown run {run_id}")
    artifact = read_artifact(run_id) or {}
    return {
        "run_id": row["id"],
        # The artifact's overall verdict when the chain has written one
        # (§1.7); the row's lifecycle status while it has not (D-e).
        "status": artifact.get("status", row["status"]),
        "measured": artifact.get("measured", False),
        "verdicts": artifact.get("verdicts", []),
        "artifact_path": row["artifact_path"],
    }
