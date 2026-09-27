"""GET /api/runs — list + detail (live API, fixture fallback lives in frontend).

Detail is the run envelope (run.schema.json's four keys) plus artifact
pointers, and 404s for an unknown id — the old stub echoed any id back with
`status: "pending"`, which was a stub, not a lookup.
"""
import json
import os

from fastapi import APIRouter, HTTPException

from ..orchestrator.pipeline import fetch_run_row, list_run_rows

router = APIRouter(prefix="/api/runs")


@router.get("")
def list_runs():
    """All runs, newest first, from the runs table (rows are small pointers —
    the envelope itself lives in the artifact, per the §6 convention)."""
    return {"runs": list_run_rows()}


@router.get("/{run_id}")
def get_run(run_id: str):
    row = fetch_run_row(run_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"unknown run: {run_id}")

    # run.schema.json's four keys + pointers. Verdicts arrive with M8; until
    # then they are honestly empty and measured is honestly false.
    verdicts: list = []
    measured = False
    exit_code = None
    artifact = None

    path = row["artifact_path"]
    if path is not None:
        if not os.path.isfile(path):
            # Row points at a file that is not there — a defect, not an empty
            # result. Loud (500), never a silent null.
            raise HTTPException(status_code=500, detail=f"artifact missing for {run_id}")
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        inner = data.get("record") if isinstance(data.get("record"), dict) else {}
        # emit writes the adjudicate output under `record` today; M9's target
        # record conforms to run.schema.json directly — read either.
        verdicts = data.get("verdicts") or inner.get("verdicts") or []
        measured = bool(data.get("measured", inner.get("measured", False)))
        exit_code = data.get("exit_code")
        artifact = {"path": path, "sha256": data.get("sha256")}

    return {
        "run_id": row["run_id"],
        "status": row["status"],
        "created_at": row["created_at"],
        "verdicts": verdicts,
        "measured": measured,
        "exit_code": exit_code,
        "artifact": artifact,
    }
