"""Typed reads over the artifact store — backend/app/store/records.py (M14).

Covers `read_artifact` (raw envelope / missing), `project_run_payload` (the
M3 §obligation-1 whitelist), and `read_run_record` (strict `RunRecord`).
Same tmp_path discipline as `test_store_db.py`: `ARTIFACT_DIR` is patched on
the *producer* module and read dynamically through it (one patch point), so
the repo tree stays clean.
"""
import pytest
from pydantic import ValidationError

import app.store.artifacts as artifacts_mod
from app.models.schemas import RunRecord
from app.store.records import (
    RUN_RECORD_KEYS,
    project_run_payload,
    read_artifact,
    read_run_record,
)


def test_read_artifact_returns_full_envelope(tmp_path, monkeypatch):
    monkeypatch.setattr(artifacts_mod, "ARTIFACT_DIR", str(tmp_path))
    artifacts_mod.write_artifact("run-abc", {"run_id": "run-abc"})
    data = read_artifact("run-abc")
    assert data["run_id"] == "run-abc"
    assert "sha256" in data
    assert data["prev_digest"] is None


def test_read_artifact_missing_returns_none(tmp_path, monkeypatch):
    monkeypatch.setattr(artifacts_mod, "ARTIFACT_DIR", str(tmp_path))
    assert read_artifact("ghost") is None


def test_project_run_payload_keeps_only_run_record_keys():
    """M3 obligation 1: the envelope's `sha256`, the PROPOSED `prev_digest`,
    and M9's superset keys never reach the strict model."""
    data = {
        "run_id": "run-abc",
        "status": "rejected",
        "verdicts": [],
        "measured": False,
        "sha256": "abc123",
        "prev_digest": None,
        "findings": [{"criterion_id": "AC-1"}],
        "traceability": {"links": []},
        "ledger": [],
        "exposure": {"measured": False},
        "signed": "deadbeef",
    }
    assert project_run_payload(data) == {
        "run_id": "run-abc",
        "status": "rejected",
        "verdicts": [],
        "measured": False,
    }
    assert set(RUN_RECORD_KEYS) == {"run_id", "status", "verdicts", "measured"}


def test_project_run_payload_tolerates_a_subset():
    """The envelope is uncontracted (D15) — projection must tolerate, not
    demand, the owned keys."""
    assert project_run_payload({}) == {}
    assert project_run_payload({"run_id": "x"}) == {"run_id": "x"}


def test_read_run_record_builds_strict_model(tmp_path, monkeypatch):
    monkeypatch.setattr(artifacts_mod, "ARTIFACT_DIR", str(tmp_path))
    artifacts_mod.write_artifact(
        "run-abc",
        {
            "run_id": "run-abc",
            "status": "rejected",
            "verdicts": [
                {
                    "criterion_id": "AC-1",
                    "verdict": "CERTIFIED",
                    "evidence_tier": "E4",
                    "locations": ["src/refund.py:44"],
                    "rationale": "approval path present",
                },
                {
                    "criterion_id": "AC-2",
                    "verdict": "REJECTED",
                    "evidence_tier": "E2",
                    "locations": ["src/refund.py:88"],
                    "rationale": "no retry path",
                },
            ],
            "measured": False,
        },
    )
    record = read_run_record("run-abc")
    assert isinstance(record, RunRecord)
    assert record.run_id == "run-abc"
    assert record.status == "rejected"
    assert record.measured is False
    assert [v.criterion_id for v in record.verdicts] == ["AC-1", "AC-2"]
    assert record.verdicts[1].verdict == "REJECTED"


def test_read_run_record_missing_returns_none(tmp_path, monkeypatch):
    monkeypatch.setattr(artifacts_mod, "ARTIFACT_DIR", str(tmp_path))
    assert read_run_record("ghost") is None


def test_read_run_record_malformed_raises(tmp_path, monkeypatch):
    """A corrupt record is loud (ValidationError), never a quiet pass — the
    `sandbox.py` posture applied to evidence (rule 6)."""
    monkeypatch.setattr(artifacts_mod, "ARTIFACT_DIR", str(tmp_path))
    artifacts_mod.write_artifact("bad-keys", {"status": "rejected"})  # no run_id
    with pytest.raises(ValidationError):
        read_run_record("bad-keys")
    artifacts_mod.write_artifact(
        "bad-enum",
        {
            "run_id": "bad-enum",
            "status": "rejected",
            "verdicts": [
                {
                    "criterion_id": "AC-1",
                    "verdict": "MAYBE",
                    "evidence_tier": "E4",
                }
            ],
            "measured": False,
        },
    )
    with pytest.raises(ValidationError):
        read_run_record("bad-enum")
