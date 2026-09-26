"""Schemas + contracts — docs/architecture.md §3 (schemas row), §10.

Pydantic models mirror contracts/ (single source). Fixtures are the
frontend's API (convention 4) — both fixtures must validate against their
schemas, and the validator script itself is exercised exactly as CI runs it.
"""
import importlib.util
import json
import subprocess
import sys
import typing
from pathlib import Path

import jsonschema

from app.models.schemas import CriterionVerdict, EvidenceTier, RunRecord, Verdict

ROOT = Path(__file__).resolve().parents[2]
CONTRACTS = ROOT / "contracts"

# Module-level literal for the five probe names — parallels SEVEN_CLASSES in
# test_metric.py. This pins the probe vocabulary so a later session cannot
# rename or extend it silently; widening is M7's call, not M1's.
FIVE_PROBES = (
    "CODE_SEARCH",
    "LOGIC_TRACE",
    "STATE_CHECK",
    "ERROR_PATH",
    "ABSENCE_CHECK",
)


def _resolver_for(schema_name: str, schema: dict) -> jsonschema.RefResolver:
    store = {
        (CONTRACTS / p.name).as_uri(): json.loads(p.read_text())
        for p in CONTRACTS.glob("*.schema.json")
    }
    return jsonschema.RefResolver(
        base_uri=(CONTRACTS / schema_name).as_uri(), referrer=schema, store=store
    )


def _validate_pair(schema_name: str, fixture_name: str) -> None:
    """Declared change (Convention 10): fixture_name is now a repo-relative path
    resolved against ROOT, not against the old FIXTURES constant (removed)."""
    schema = json.loads((CONTRACTS / schema_name).read_text())
    fixture = json.loads((ROOT / fixture_name).read_text())
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
    demo = json.loads((ROOT / "fixtures" / "demo_run.json").read_text())
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
    _validate_pair("run.schema.json", "fixtures/demo_run.json")


def test_demo_traceability_fixture_validates():
    _validate_pair("traceability.schema.json", "fixtures/demo_traceability.json")


def test_fixture_verdicts_satisfy_verdict_contract():
    """run.schema.json $refs verdict.schema.json — validate the items directly."""
    schema = json.loads((CONTRACTS / "verdict.schema.json").read_text())
    demo = json.loads((ROOT / "fixtures" / "demo_run.json").read_text())
    validator = jsonschema.Draft7Validator(schema)
    for verdict in demo["verdicts"]:
        validator.validate(verdict)


def test_validator_script_exits_zero_as_ci_runs_it():
    """Wrap scripts/validate_contracts.py — the exact command CI executes.

    Declared change (Convention 10): the two stdout assertions now check the
    repo-relative paths printed by the updated validator.
    """
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_contracts.py")],
        capture_output=True,
        text=True,
        cwd=ROOT,
        timeout=60,
    )
    assert proc.returncode == 0, f"stdout={proc.stdout}\nstderr={proc.stderr}"
    assert "OK fixtures/demo_run.json" in proc.stdout
    assert "OK fixtures/demo_traceability.json" in proc.stdout


# ---------------------------------------------------------------------------
# New tests — orphan-closure + findings schema
# ---------------------------------------------------------------------------

def _load_validate_contracts_module():
    """Load scripts/validate_contracts.py as a module via importlib.
    The file is not an importable package, so we use spec_from_file_location."""
    spec = importlib.util.spec_from_file_location(
        "validate_contracts",
        ROOT / "scripts" / "validate_contracts.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_every_contract_schema_has_a_pair():
    """Assert PAIRS in the real validator covers every schema in contracts/.
    Asserts against the real producer — never re-declares the list here
    (test-suite.md Convention 7)."""
    mod = _load_validate_contracts_module()
    paired_schemas = {schema for schema, _ in mod.PAIRS}
    all_schemas = {p.name for p in CONTRACTS.glob("*.schema.json")}
    assert paired_schemas == all_schemas, (
        f"Orphan schemas (no PAIRS entry): {all_schemas - paired_schemas}; "
        f"Phantom entries (not on disk): {paired_schemas - all_schemas}"
    )


def test_verdict_example_validates():
    _validate_pair("verdict.schema.json", "contracts/examples/verdict.json")


def test_criterion_example_validates():
    _validate_pair("criterion.schema.json", "contracts/examples/criterion.json")


def test_exposure_example_validates():
    _validate_pair("exposure.schema.json", "contracts/examples/exposure.json")


def test_findings_example_validates():
    _validate_pair("findings.schema.json", "contracts/examples/findings.json")


def test_exposure_example_is_the_unmeasured_state():
    """Pins Convention 8 at the contract layer: the honest pre-measurement state
    is measured=False, a null rate, and no operators — never render it as a number."""
    example = json.loads((ROOT / "contracts" / "examples" / "exposure.json").read_text())
    assert example["measured"] is False
    assert example["false_certified_rate"] is None
    assert example["by_operator"] == {}


def test_findings_probe_enum_is_the_five_named_probes():
    """The five probe names are settled by the source proposal (architecture.md §3).
    FIVE_PROBES is the module-level literal; the schema is the authoritative source."""
    schema = json.loads((CONTRACTS / "findings.schema.json").read_text())
    schema_probes = tuple(schema["properties"]["probe"]["enum"])
    assert FIVE_PROBES == schema_probes


def test_uncovered_schemas_reports_a_missing_pair(tmp_path):
    """Pure function: build a synthetic contracts dir with two schemas,
    pass only one pair, assert the uncovered filename comes back."""
    mod = _load_validate_contracts_module()
    (tmp_path / "alpha.schema.json").write_text("{}")
    (tmp_path / "beta.schema.json").write_text("{}")
    result = mod.uncovered_schemas(tmp_path, [("alpha.schema.json", "some/example.json")])
    assert result == ["beta.schema.json"]


def test_uncovered_schemas_is_empty_when_all_covered(tmp_path):
    """Pure function: both schemas paired → empty list."""
    mod = _load_validate_contracts_module()
    (tmp_path / "alpha.schema.json").write_text("{}")
    (tmp_path / "beta.schema.json").write_text("{}")
    pairs = [
        ("alpha.schema.json", "contracts/examples/alpha.json"),
        ("beta.schema.json",  "contracts/examples/beta.json"),
    ]
    result = mod.uncovered_schemas(tmp_path, pairs)
    assert result == []


def test_findings_result_is_unenumerated_and_tier_is_not_required():
    """Pins two non-decisions so a later session cannot widen them silently.

    Widening `result`'s vocabulary is M7's call — the set of valid result
    strings belongs to the verification stage, not to the contract layer.
    Adding `evidence_tier` to required or properties is D1's call — the
    E0-E6 ladder is undefined in the source and must not be hard-coded here
    until D1 is ratified.
    """
    schema = json.loads((CONTRACTS / "findings.schema.json").read_text())
    properties = schema["properties"]
    required = schema["required"]
    assert "enum" not in properties["result"], (
        "result must stay unenumerated — its vocabulary is M7's call, not M1's"
    )
    assert "evidence_tier" not in required, (
        "evidence_tier must not be required until D1 is ratified"
    )
    assert "evidence_tier" not in properties, (
        "evidence_tier must not appear in properties until D1 is ratified"
    )
