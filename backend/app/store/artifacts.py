"""JSON artifact writer — tamper-evident evidence records land under ARTIFACT_DIR.

M14 owns this file. Each artifact is an *envelope* around the payload: the
store's keys (`sha256`, and the PROPOSED `prev_digest`) are written *last*,
so a payload key of the same name can never silently override them. The
digest covers the sorted payload body only — `test_store_db.py` pins that.

`prev_digest` is the D8 (cross-file chain) seam for M9: the previous
artifact's digest, threaded by the emitter. It is PROPOSED and UNCONTRACTED
(modules.md D15 — the envelope has no contract); the self-invalidating guard
`test_prev_digest_is_provisional_until_m1_contracts_the_envelope` fails the
day M1 adds an envelope contract, so this key gets ratified or removed. Until
D8 is ratified the per-file digest stays authoritative.
"""
import hashlib
import json
import os
from pathlib import Path

from ..config import ARTIFACT_DIR

# Store-owned envelope keys — always win over payload keys of the same name.
SHA256_KEY = "sha256"
PREV_DIGEST_KEY = "prev_digest"


def artifact_path_for(run_id: str) -> Path:
    """The on-disk path for a run's artifact. One resolver, so `read_artifact`
    (records.py) and `write_artifact` can never drift to different
    directories, and tests keep a single patch point
    (`artifacts_mod.ARTIFACT_DIR`, read dynamically at call time).
    """
    return Path(ARTIFACT_DIR) / f"{run_id}.json"


def write_artifact(run_id: str, payload: dict,
                   prev_digest: str | None = None) -> str:
    """Write `{**payload, sha256, prev_digest}` to the artifact dir and return
    the path as a string.
    """
    path = artifact_path_for(run_id)
    os.makedirs(path.parent, exist_ok=True)
    body = json.dumps(payload, sort_keys=True).encode()
    digest = hashlib.sha256(body).hexdigest()
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({**payload, SHA256_KEY: digest,
                   PREV_DIGEST_KEY: prev_digest}, fh, indent=2)
    return str(path)
