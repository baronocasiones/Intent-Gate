"""Typed reads over the artifact store — the read half of M14.

`artifacts.py` writes bytes; this module reads records. `read_artifact`
returns the raw envelope dict (`None` when the file is absent — M15's 404);
`project_run_payload` strips a dict down to the keys `run.schema.json` owns;
`read_run_record` combines the two into M3's strict `RunRecord`.

The projection exists because the models are `extra="forbid"`
(modules.md §M3): the envelope's `sha256`, the PROPOSED `prev_digest`
(D15), and M9's superset keys (traceability, ledger, exposure, `signed`,
`findings`) are not contract keys, so reading an artifact into `RunRecord`
unprojected would raise. The projection whitelists, so it stays correct even
while the envelope itself is uncontracted.
"""
import json
from pathlib import Path

from ..models.schemas import RunRecord
from . import artifacts

# Exactly the keys `run.schema.json` requires — modules.md §M3 obligation 1.
RUN_RECORD_KEYS = ("run_id", "status", "verdicts", "measured")


def read_artifact(run_id: str) -> dict | None:
    """The raw envelope for `run_id`, or `None` when no artifact exists."""
    path = artifacts.artifact_path_for(run_id)
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None


def project_run_payload(data: dict) -> dict:
    """Keep only the `RunRecord` keys. Everything else — `sha256`,
    `prev_digest`, M9's superset — is dropped here, deliberately, before the
    strict model ever sees it.
    """
    return {k: data[k] for k in RUN_RECORD_KEYS if k in data}


def read_run_record(run_id: str) -> RunRecord | None:
    """A validated `RunRecord` for `run_id`. `None` when the artifact is
    absent (M15's 404); raises `ValidationError` on a malformed artifact — a
    corrupt record must be loud, like `sandbox.py`'s malformed-evidence
    posture, never a quiet pass (modules.md rule 6).
    """
    data = read_artifact(run_id)
    if data is None:
        return None
    return RunRecord(**project_run_payload(data))
