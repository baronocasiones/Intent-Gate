"""JSON artifact writer — hash-chained evidence records land under ARTIFACT_DIR."""
import hashlib
import json
import os

from ..config import ARTIFACT_DIR


def write_artifact(run_id: str, payload: dict) -> str:
    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    path = os.path.join(ARTIFACT_DIR, f"{run_id}.json")
    body = json.dumps(payload, sort_keys=True).encode()
    digest = hashlib.sha256(body).hexdigest()
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"sha256": digest, **payload}, fh, indent=2)
    return path
