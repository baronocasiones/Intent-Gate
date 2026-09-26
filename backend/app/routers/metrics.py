"""GET /api/metrics — false-certified rate + per-operator breakdown."""
from fastapi import APIRouter

router = APIRouter(prefix="/api/metrics")


@router.get("")
def get_metrics():
    # TODO: aggregate spec-mutation results from store.
    return {"false_certified_rate": None, "measured": False, "by_operator": {}}
