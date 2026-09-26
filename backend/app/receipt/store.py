"""Receipt artefact writer - self-contained HTML receipts land beside the
signed JSON under ARTIFACT_DIR.

The JSON artefact remains the signed record; the receipt is a rendering that
can be regenerated from it at any time. Keeping the two apart is why this
module owns writing only, and why render.py stays pure.
"""
import json
import os

from ..config import ARTIFACT_DIR
from .render import render


def _stored_artifact(run_id: str):
    """The artefact as written to disk, or None if it is not there yet."""
    path = os.path.join(ARTIFACT_DIR, f"{run_id}.json")
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def write_receipt(run_id: str, artifact: dict) -> str:
    """Write {ARTIFACT_DIR}/{run_id}.receipt.html and return its path.

    Prefers the stored artefact when one exists, so the receipt reports the
    record *as written* rather than the record as passed in. Recomputing the
    digest here instead would be worse than useless: a tampered artefact
    would re-verify itself and the receipt would certify the tampering. The
    digest has to come from the stored envelope, never from this call.
    """
    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    path = os.path.join(ARTIFACT_DIR, f"{run_id}.receipt.html")
    stored = _stored_artifact(run_id)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(render(stored if stored is not None else artifact))
    return path
