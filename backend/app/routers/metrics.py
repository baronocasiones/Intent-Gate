"""GET /api/metrics — false-certified rate + per-operator breakdown.

Delegates the math to M13's false_certified_rate() and feeds it whatever
mutation results are in the artifact store. M13's harness has not landed, so
today that is nothing: the endpoint returns the honest pre-measurement state
(`null` rate, `measured: false`) with all seven operator buckets at zero —
never 0.0, which would read as a good number we do not have (modules.md 1.7).

Storage convention (the wiring point M13 needs): a mutation result is an
artifact carrying the two keys false_certified_rate() consumes — `operator`
and `verdict`. Formal shape is D15's to define when the harness lands; this
reader deliberately consumes only M13's documented input, not an invented
envelope. Run artifacts have no `operator` key and are skipped.
"""
import json
from pathlib import Path

from fastapi import APIRouter

from ..metrics.false_certified import false_certified_rate
from ..store import artifacts

router = APIRouter(prefix="/api/metrics")


def _stored_mutation_results() -> list[dict]:
    results: list[dict] = []
    for path in sorted(Path(artifacts.ARTIFACT_DIR).glob("*.json")):
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)  # a corrupt artifact is a defect — let it 500
        if isinstance(data, dict) and "operator" in data and "verdict" in data:
            results.append({"operator": data["operator"], "verdict": data["verdict"]})
    return results


@router.get("")
def get_metrics():
    return false_certified_rate(_stored_mutation_results())
