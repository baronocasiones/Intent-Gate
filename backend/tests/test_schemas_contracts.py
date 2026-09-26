"""Schemas + contracts — docs/architecture.md §3 (schemas row), §10.

Pydantic models mirror contracts/ (single source). Fixtures are the
frontend's API (convention 4) — both fixtures must validate against their
schemas, and the validator script itself is exercised exactly as CI runs it.
"""
import json
import subprocess
import sys
import typing
from pathlib import Path

import jsonschema

from app.models.schemas import CriterionVerdict, EvidenceTier, RunRecord, Verdict

ROOT = Path(__file__).resolve().parents[2]
CONTRACTS = ROOT / "contracts"
FIXTURES = ROOT / "fixtures"


def _resolver_for(schema_name: str, schema: dict) -> jsonschema.RefResolver:
    store = {
        (CONTRACTS / p.name).as_uri(): json.loads(p.read_text())
        for p in CONTRACTS.glob("*.schema.json")
    }
    return jsonschema.RefResolver(
        base_uri=(CONTRACTS / schema_name).as_uri(), referrer=schema, store=store
    )


def _validate_pair(schema_name: str, fixture_name: str) -> None:
    schema = json.loads((CONTRACTS / schema_name).read_text())
    fixture = json.loads((FIXTURES / fixture_name).read_text())
    resolver = _resolver_for(schema_name, schema)
    jsonschema.Draft7Validator(schema, resolver=resolver).validate(fixture)


def test_verdict_literal_matches_contract_enum():
    literal_values = typing.get_args(Verdict)
    schema = json.loads((CONTRACTS / "verdict.schema.json").read_text())
    assert set(literal_values) == set(schema["properties"]["verdict"]["enum"])
    assert set(literal_values) == {"CERTIFIED", "CONDITIONAL", "REJECTED", "PENDING"}


def test_evidence_tier_is_exactly_e0_to_e6():
    assert typing.get_args(EvidenceTier) == tuple(f"E{i}" for i in range(7))
    schema = json.loads((CONTRACTS / "traceability.schema.json").read_text())
    link_props = schema["properties"]["links"]["items"]["properties"]
    assert set(link_props["evidence_tier"]["enum"]) == set(typing.get_args(EvidenceTier))


def test_pydantic_run_record_accepts_demo_fixture():
    demo = json.loads((FIXTURES / "demo_run.json").read_text())
    run = RunRecord(**demo)
    assert run.run_id == "demo"
    assert run.measured is False
    assert len(run.verdicts) == 2
    assert all(v.verdict == "PENDING" for v in run.verdicts)
    assert all(v.evidence_tier == "E0" for v in run.verdicts)


def test_criterion_verdict_roundtrip():
    v = CriterionVerdict(
        criterion_id="AC-9",
        verdict="CERTIFIED",
        evidence_tier="E3",
        locations=["src/x.py:10"],
        rationale="probe evidence",
    )
    again = CriterionVerdict(**v.model_dump())
    assert again == v


def test_rationale_defaults_empty_characterization():
    """Contract *requires* rationale; the model defaults it to "" — strictness
    lives at the contract boundary, not the model (documented behavior)."""
    v = CriterionVerdict(criterion_id="AC-1", verdict="PENDING", evidence_tier="E0")
    assert v.rationale == ""


def test_demo_run_fixture_validates_against_run_contract():
    _validate_pair("run.schema.json", "demo_run.json")


def test_demo_traceability_fixture_validates():
    _validate_pair("traceability.schema.json", "demo_traceability.json")


def test_fixture_verdicts_satisfy_verdict_contract():
    """run.schema.json $refs verdict.schema.json — validate the items directly."""
    schema = json.loads((CONTRACTS / "verdict.schema.json").read_text())
    demo = json.loads((FIXTURES / "demo_run.json").read_text())
    validator = jsonschema.Draft7Validator(schema)
    for verdict in demo["verdicts"]:
        validator.validate(verdict)


def test_validator_script_exits_zero_as_ci_runs_it():
    """Wrap scripts/validate_contracts.py — the exact command CI executes."""
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_contracts.py")],
        capture_output=True,
        text=True,
        cwd=ROOT,
        timeout=60,
    )
    assert proc.returncode == 0, f"stdout={proc.stdout}\nstderr={proc.stderr}"
    assert "OK demo_run.json" in proc.stdout
    assert "OK demo_traceability.json" in proc.stdout
