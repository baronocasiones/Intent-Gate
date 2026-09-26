"""GET /api/runs — list + detail (live API, fixture fallback lives in frontend)."""
from fastapi import APIRouter

router = APIRouter(prefix="/api/runs")


@router.get("")
def list_runs():
    # TODO: query SQLite; return [] until store lands.
    return {"runs": []}


@router.get("/{run_id}")
def get_run(run_id: str):
    # TODO: load run + artifact pointers from store.
    return {"run_id": run_id, "status": "pending"}
