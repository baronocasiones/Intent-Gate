"""Schemas + contracts — docs/architecture.md §3 (schemas row), §10.

Pydantic models mirror contracts/ (single source). Fixtures are the
frontend's API (convention 4) — both fixtures and all four examples in
contracts/examples/ must validate against their schemas, every schema on disk
must have a pair, the served copy under frontend/public/ must stay
byte-identical to its canonical one, and the validator script itself is
exercised exactly as CI runs it.
"""
import importlib.util
import json
import subprocess
import sys
import typing
from pathlib import Path

import jsonschema

from app.metrics.false_certified import OPERATORS
from app.models.schemas import CriterionVerdict, EvidenceTier, RunRecord, Verdict

ROOT = Path(__file__).resolve().parents[2]
CONTRACTS = ROOT / "contracts"
PUBLIC_FIXTURES = ROOT / "frontend" / "public" / "fixtures"

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


def _validate_path(schema_name: str, fixture_path: Path) -> None:
    """Validate an artifact at an explicit path against its contract. Takes a Path
    rather than a repo-relative name because M2's served copy lives outside
    fixtures/, under frontend/public/."""
    schema = json.loads((CONTRACTS / schema_name).read_text())
    fixture = json.loads(fixture_path.read_text())
    resolver = _resolver_for(schema_name, schema)
    jsonschema.Draft7Validator(schema, resolver=resolver).validate(fixture)


def _validate_pair(schema_name: str, fixture_name: str) -> None:
    """Declared change (Convention 10, M1): fixture_name is a repo-relative path
    resolved against ROOT, not against the old FIXTURES constant (removed)."""
    _validate_path(schema_name, ROOT / fixture_name)


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
    """Flipped 2026-09-27 (M2): the demo run is no longer the all-PENDING/E0 stub
    (docs/modules.md M2 criterion 4). Pins the concrete §1.7 worked-example values."""
    demo = json.loads((ROOT / "fixtures" / "demo_run.json").read_text())
    run = RunRecord(**demo)
    assert run.run_id == "demo"
    assert run.status == "rejected"  # D9 default — the §1.2 lifecycle is lowercase
    assert run.measured is False
    assert len(run.verdicts) == 2
    ac1, ac2 = run.verdicts
    assert (ac1.criterion_id, ac1.verdict, ac1.evidence_tier) == ("AC-1", "CERTIFIED", "E4")
    assert ac1.locations == ["src/refund.py:64"]
    assert (ac2.criterion_id, ac2.verdict, ac2.evidence_tier) == ("AC-2", "REJECTED", "E2")
    assert ac2.locations == ["src/refund.py:88"]


def test_demo_run_fixture_is_not_a_stub():
    """M2 criterion 4, self-enforcing: the corpus must keep mixing outcomes, keep real
    locations, and keep a tier above E0 — a dashboard that only ever renders emptiness
    proves nothing."""
    verdicts = json.loads((ROOT / "fixtures" / "demo_run.json").read_text())["verdicts"]
    assert {v["verdict"] for v in verdicts} == {"CERTIFIED", "REJECTED"}
    assert all(v["locations"] for v in verdicts)
    assert any(v["evidence_tier"] != "E0" for v in verdicts)
    # A placeholder rationale is a stub with extra steps.
    assert all("stub" not in v["rationale"].lower() for v in verdicts)


def test_public_demo_run_is_byte_identical_to_canonical_fixture():
    """The public/ copy is what Vite serves at /fixtures/demo_run.json. It held the
    traceability payload under a run filename (M2 finding 3); byte-equality is what stops
    the two copies drifting apart again."""
    public = (PUBLIC_FIXTURES / "demo_run.json").read_bytes()
    assert public == (ROOT / "fixtures" / "demo_run.json").read_bytes()


def test_public_demo_run_validates_against_run_contract():
    """The served copy is not in the validator's PAIRS — that list pairs run.schema.json
    with fixtures/demo_run.json only — so the contract is checked here."""
    _validate_path("run.schema.json", PUBLIC_FIXTURES / "demo_run.json")


def test_traceability_fixture_describes_the_same_run_as_the_run_fixture():
    """The matrix and the run are one run. M2's traceability fixture said E0 with no
    locations while the run said E4/E2 — two copies of one run disagreeing."""
    run = json.loads((ROOT / "fixtures" / "demo_run.json").read_text())
    matrix = json.loads((ROOT / "fixtures" / "demo_traceability.json").read_text())
    assert matrix["run_id"] == run["run_id"]
    assert {link["criterion_id"]: link["evidence_tier"] for link in matrix["links"]} == {
        v["criterion_id"]: v["evidence_tier"] for v in run["verdicts"]
    }


def test_demo_exposure_validates_against_exposure_contract():
    """Since M1 landed, exposure.schema.json has a PAIRS entry — but it points at
    contracts/examples/exposure.json, the unmeasured null stub that pins the honest
    pre-measurement state. This fixture is a different artifact carrying a real measured
    rate, and it is not in PAIRS, so it is still validated here."""
    _validate_pair("exposure.schema.json", "fixtures/demo_exposure.json")


def test_demo_exposure_is_measured_with_a_rate_pointing_the_good_way():
    """Low is good (§1.7): a rate near 1.0 would show a gate that certifies violated
    specs, which is the failure this product exists to prevent."""
    exposure = json.loads((ROOT / "fixtures" / "demo_exposure.json").read_text())
    assert exposure["measured"] is True
    assert exposure["false_certified_rate"] is not None
    assert 0.0 < exposure["false_certified_rate"] < 0.5


def test_demo_exposure_keys_every_operator_with_counts():
    """Generated by false_certified_rate(), which always keys all 7 OPERATORS — keep the
    fixture in step with the code's actual output shape, not the 2-key sample in §1.7."""
    exposure = json.loads((ROOT / "fixtures" / "demo_exposure.json").read_text())
    assert set(exposure["by_operator"]) == set(OPERATORS)
    for counts in exposure["by_operator"].values():
        assert set(counts) == {"certified", "total"}
        assert all(isinstance(n, int) and n >= 0 for n in counts.values())


def test_demo_exposure_shows_a_false_certified_and_an_unexercised_operator():
    """M2 criterion 5 needs a real number to render, and honest zeros: an operator the
    mutation run never touched must read 0/0, not a fabricated count."""
    by_operator = json.loads((ROOT / "fixtures" / "demo_exposure.json").read_text())["by_operator"]
    assert any(c["certified"] > 0 and c["total"] > 0 for c in by_operator.values())
    assert any(c["total"] == 0 for c in by_operator.values())


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
    # The gate's self-reported coverage must come from the schemas on disk, not
    # from len(PAIRS) — a duplicate pair entry must not be able to overstate it.
    n_schemas = len(list(CONTRACTS.glob("*.schema.json")))
    assert f"OK {n_schemas}/{n_schemas} schemas covered" in proc.stdout


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

    Adding `evidence_tier` to required or properties was D1's call. **D1 is now
    ratified** (docs/modules.md 1.4, this session), so the original reason for
    this guard — "the E0-E6 ladder is undefined in the source" — no longer holds,
    and the guard would otherwise read as a claim that D1 is still open. It
    survives on different and better grounds: the tier is derived by **M8 from
    which probe ran**, not carried on the finding. A finding states what a probe
    observed; a verdict states how far the evidence reached. So the honest
    contract for `findings` still has no tier field, and this assertion is now
    testing a design position rather than a deferral.

    Consequence to carry, not to act on: if M1 ever adds `evidence_tier` here
    for M7b, M3 must add it to the `Finding` mirror in the same change or M7's
    own output is rejected by its own strict mirror.
    """
    schema = json.loads((CONTRACTS / "findings.schema.json").read_text())
    properties = schema["properties"]
    required = schema["required"]
    assert "enum" not in properties["result"], (
        "result must stay unenumerated — its vocabulary is M7's call, not M1's"
    )
    assert "evidence_tier" not in required, (
        "evidence_tier does not belong on a finding — the tier is derived by M8 "
        "from which probe ran, not carried on the probe's observation"
    )
    assert "evidence_tier" not in properties, (
        "evidence_tier does not belong on a finding — D1 is ratified, and the "
        "tier is M8's to derive; see this test's docstring"
    )
