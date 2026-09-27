"""M3 — pydantic mirror parity with contracts/ (docs/modules.md §M3, AC 1).

The join key is the contract's JSON Schema `title`, reused verbatim as the
class name. That makes parity a *mechanical* assertion rather than a convention
anyone has to remember: the moment M1 adds a schema (e.g. the
`findings.schema.json` its own AC 2 calls for), this file fails until M3
mirrors it. **That failure is the contracts-first rule working — do not
suppress it, mirror the schema.**

Deliberately non-overlapping with `test_schemas_contracts.py`, which already pins
the `Verdict` / `EvidenceTier` literals against the contract enums, the
`RunRecord`-from-fixture load, and the `CriterionVerdict` round trip. This file
adds only what is missing: the parity bijection, field coverage, round trips
for the three new models, the strictness pin, and the honesty pin.
"""
import inspect
import json
from pathlib import Path

import pytest
from pydantic import BaseModel, ValidationError

from app.metrics.false_certified import false_certified_rate
from app.models import schemas
from app.models.schemas import (
    ContractModel,
    Criterion,
    CriterionVerdict,
    Exposure,
    Finding,
    Probe,
    RunRecord,
    TraceabilityLink,
    TraceabilityMatrix,
)

ROOT = Path(__file__).resolve().parents[2]
CONTRACTS = ROOT / "contracts"

# `BaseModel` is imported into app.models.schemas, so it shows up as a class
# member of that module and would otherwise satisfy "is a BaseModel subclass".
# `ContractModel` is the shared strict base, which mirrors no contract.
_NOT_A_MIRROR = (BaseModel, ContractModel)


def _contract_titles() -> dict[str, dict]:
    """Contract JSON Schema `title` -> the schema itself."""
    out: dict[str, dict] = {}
    for path in sorted(CONTRACTS.glob("*.schema.json")):
        schema = json.loads(path.read_text())
        out[schema["title"]] = schema
    return out


def _contracts_by_file() -> dict[str, dict]:
    """Contract file name -> the schema itself.

    The file name and the `title` disagree for three of the six contracts --
    `run`/`RunRecord`, `traceability`/`TraceabilityMatrix` and
    `verdict`/`CriterionVerdict`. (`criterion`, `exposure` and `findings` differ
    only in case.) So the two lookups below are deliberately separate: one joins
    on the `title`, which is the parity key, and this one addresses contracts by
    the name on disk. Do not "tidy" this by renaming -- `contracts/` is M1's
    alone, and the file name is contract identity.
    """
    return {
        path.name: json.loads(path.read_text())
        for path in sorted(CONTRACTS.glob("*.schema.json"))
    }


def _mirrors() -> dict[str, type[BaseModel]]:
    """Class name -> model, for every mirror defined in app.models.schemas."""
    return {
        name: obj
        for name, obj in inspect.getmembers(schemas, inspect.isclass)
        if issubclass(obj, BaseModel) and obj not in _NOT_A_MIRROR
    }


CONTRACT_TITLES = sorted(_contract_titles())
MIRROR_NAMES = sorted(_mirrors())

# The one mirror with no `title` to join on: `traceability.schema.json` declares
# the link object *inline* under `properties.links.items`, so it has no schema
# file of its own. Its SHAPE is still entirely contract-derived and is checked
# against that inline object by
# `test_inline_mirror_matches_its_inline_contract_object` below — only the name
# is M3's.
#
# M3 cannot fix this itself: `contracts/` is M1's alone (modules.md 0.4). The
# clean fix is for M1 to promote it to `traceability-link.schema.json` with a
# `title`, and `test_contract_model_parity_is_a_bijection` will then *demand*
# that this entry be deleted. Do not silence it; retire it.
INLINE_MIRRORS = {
    # mirror name -> (contract schema name, path of field names to the inline object)
    "TraceabilityLink": ("traceability.schema.json", ("links", "items")),
}


def test_contract_model_parity_is_a_bijection():
    """AC 1: a model for every schema, and a schema behind every model."""
    titles, inline, mirrors = set(CONTRACT_TITLES), set(INLINE_MIRRORS), set(MIRROR_NAMES)

    # Self-invalidating: an exception that has been promoted to a real contract
    # must be removed, or it silently exempts a contract that no longer needs it.
    assert not (titles & inline), (
        f"{sorted(titles & inline)} now has a titled contract — delete it from INLINE_MIRRORS"
    )

    assert titles | inline == mirrors, (
        "M3 parity broken — "
        f"only in contracts/ (add a model in app/models/schemas.py): "
        f"{sorted((titles | inline) - mirrors)}; "
        f"only in models (add or retire a contract in contracts/): {sorted(mirrors - (titles | inline))}"
    )


def test_inline_mirror_matches_its_inline_contract_object():
    """The exception above is about the NAME only — the shape is still checked."""
    for name, (schema_file, path) in INLINE_MIRRORS.items():
        contract = _contracts_by_file()[schema_file]
        item = contract
        for part in path:
            # A segment names a field (so look inside `properties`) unless the
            # schema has no `properties` of its own — then it is a plain key,
            # e.g. an array's `items`.
            item = item["properties"][part] if part in item.get("properties", {}) else item[part]
        fields = set(_mirrors()[name].model_fields)
        where = f"{schema_file} -> {'.'.join(path)}"
        assert set(item["properties"]) <= fields, (
            f"{name} is missing {sorted(set(item['properties']) - fields)} from {where}"
        )
        assert set(item.get("required", [])) <= fields


@pytest.mark.parametrize("title", CONTRACT_TITLES)
def test_model_fields_cover_contract_properties(title):
    """Every key a contract declares must exist as a model field.

    Superset, not equality: a mirror may carry fields the contract does not
    require, but it may not be missing one it does.
    """
    model = _mirrors()[title]
    declared = set(_contract_titles()[title]["properties"])
    assert declared <= set(model.model_fields), (
        f"{title} is missing model field(s) for contract key(s): "
        f"{sorted(declared - set(model.model_fields))}"
    )


@pytest.mark.parametrize("title", CONTRACT_TITLES)
def test_required_contract_fields_are_model_fields(title):
    schema = _contract_titles()[title]
    fields = set(_mirrors()[title].model_fields)
    missing = set(schema.get("required", [])) - fields
    assert not missing, f"{title} contract requires {sorted(missing)}, absent from the model"


def test_every_model_forbids_unknown_keys():
    """The strictness is a design position, not a default that may drift.

    Contracts are the permissive interchange layer; these models are the strict
    trust layer, so an undeclared key is a loud violation rather than a silently
    dropped field (see the module docstring in schemas.py).
    """
    for name, model in _mirrors().items():
        assert model.model_config.get("extra") == "forbid", f"{name} is not strict"

    with pytest.raises(ValidationError):
        CriterionVerdict(
            criterion_id="AC-1",
            verdict="PENDING",
            evidence_tier="E0",
            sha256="not a contract key",
        )


def test_criterion_roundtrip():
    c = Criterion(criterion_id="AC-1", text="refunds over $100 need approval", testable=True)
    assert Criterion(**c.model_dump()) == c


def test_criterion_requires_all_three_fields():
    """No defaults here, unlike CriterionVerdict — see the model docstring.

    `testable=False` would silently drop an untestable criterion, and an
    untestable criterion must be rejected outright, never verified
    (docs/modules.md 1.3).
    """
    for incomplete in (
        {"criterion_id": "AC-1", "text": "x"},
        {"criterion_id": "AC-1", "testable": True},
        {"text": "x", "testable": True},
    ):
        with pytest.raises(ValidationError):
            Criterion(**incomplete)


def test_finding_roundtrip():
    f = Finding(
        criterion_id="AC-2",
        probe="ERROR_PATH",
        result="refuted",
        location="src/refund.py:88",
        note="no retry path",
    )
    assert Finding(**f.model_dump()) == f


def test_finding_accepts_the_contracts_own_example():
    """Cross-check the mirror against corpus data, not just constructed values.

    `contracts/examples/findings.json` is the value the validator gate checks,
    so the example -- not a hand-written literal -- is what the mirror has to
    survive. Only `criterion` and `exposure` still lack a fixture pair
    (docs/test-suite.md, Known gaps).
    """
    example = json.loads((ROOT / "contracts" / "examples" / "findings.json").read_text())
    assert Finding(**example).model_dump() == example


def test_finding_requires_all_five_fields():
    """No defaults, for the same reason `Criterion` has none.

    A probe that defaulted its `note` or `location` to "" would attest that
    something was examined when it was not. All five keys are in the contract's
    `required`, so every one of them is the finding's identity.
    """
    full = {
        "criterion_id": "AC-1",
        "probe": "CODE_SEARCH",
        "result": "confirmed",
        "location": "src/refund.py:88",
        "note": "found",
    }
    for dropped in full:
        with pytest.raises(ValidationError):
            Finding(**{k: v for k, v in full.items() if k != dropped})


def test_finding_rejects_an_unknown_probe():
    """Negative assertion, per Convention 8 -- a round trip cannot catch this.

    A finding attributed to a probe nobody ran is a fabricated evidence
    location, so the enum has to bite. The alias contents themselves are pinned
    to the contract enum by `test_schemas_contracts.py::FIVE_PROBES`; this pins
    the other half of the pair -- that the field actually *uses* the alias --
    which is the wiring `architecture.md` 11.12 records as unguarded for
    `Verdict` / `EvidenceTier`. Re-typing `probe` to `str` fails both.
    """
    assert Finding.model_fields["probe"].annotation is Probe

    with pytest.raises(ValidationError):
        Finding(
            criterion_id="AC-1",
            probe="TELEPATHY",  # not one of the five
            result="confirmed",
            location="src/refund.py:88",
            note="found",
        )


def test_finding_does_not_encode_d1_tier_semantics():
    """D1 is unratified, so no tier may appear on the mirror (rule 6, fail-closed).

    `contracts/findings.schema.json` says in its own `description` that a tier
    is *expected* alongside a finding but must NOT be added until the E0-E6
    ladder is decided. That instruction had no mechanical guard: adding
    `evidence_tier` to this model kept the whole suite green while the mirror
    silently started encoding a ladder nobody has ratified. This pins the
    absence, so the failure lands on whoever tries.

    If D1 is ratified, delete this test in the same change that adds the tier --
    do not quietly widen the allowance.
    """
    assert "evidence_tier" not in Finding.model_fields, (
        "D1 is unratified -- Finding must not carry a tier. Ratify D1 first, then "
        "add it to contracts/findings.schema.json and delete this test."
    )


def test_finding_result_stays_unenumerated():
    """`result`'s vocabulary belongs to M7, not to M1 or M3.

    The contract declares `result` a bare string on purpose, and enumerating it
    here would let the mirror invent a vocabulary no contract ratified. When M7
    agrees one, M3 changes in the same commit and this test flips deliberately
    (docs/test-suite.md Convention 4).
    """
    assert Finding.model_fields["result"].annotation is str


def test_traceability_matrix_roundtrip():
    matrix = TraceabilityMatrix(
        run_id="run-1a2b3c4d",
        links=[
            TraceabilityLink(
                criterion_id="AC-1",
                locations=["src/refund.py:88"],
                evidence_tier="E4",
            )
        ],
    )
    assert TraceabilityMatrix(**matrix.model_dump()) == matrix


def test_traceability_link_defaults_empty_locations():
    """The contract requires `locations`; the model defaults it, as CriterionVerdict does."""
    link = TraceabilityLink(criterion_id="AC-1", evidence_tier="E0")
    assert link.locations == []


def test_exposure_roundtrip():
    e = Exposure(
        false_certified_rate=0.25,
        measured=True,
        by_operator={"boundary_drop": {"certified": 1, "total": 2}},
    )
    assert Exposure(**e.model_dump()) == e


def test_exposure_default_is_unmeasured_not_zero():
    """The honesty pin (docs/modules.md 1.7).

    `measured: false` with a `null` rate must stay visibly distinct from a real
    `0.0` — a pre-measurement dashboard must never be able to imply a good
    number. These defaults are the honest pre-measurement state, matching the
    `GET /api/metrics` stub, so they are pinned here rather than left implicit.
    """
    e = Exposure()
    assert e.model_dump() == {
        "false_certified_rate": None,
        "measured": False,
        "by_operator": {},
    }
    assert e.false_certified_rate is not 0.0

    # ...and the measured 0.0 remains representable and distinct from it.
    measured_zero = Exposure(measured=True, false_certified_rate=0.0)
    assert measured_zero.measured is True
    assert measured_zero.false_certified_rate == 0.0
    assert measured_zero.model_dump() != e.model_dump()


def test_exposure_accepts_metric_function_output():
    """Bind the mirror to its real producer, not to an assumption about it.

    `by_operator` is typed more specifically than the contract's bare
    `{"type": "object"}`; this asserts that the specificity actually fits what
    `metrics.false_certified_rate` returns, for both the empty and measured
    cases. If M13 changes that return shape, this fails rather than lying.
    """
    unmeasured = false_certified_rate([])
    assert Exposure(**unmeasured).model_dump() == unmeasured

    # Worst case: the gate certified a spec that had been mutated underneath it.
    worst_case = false_certified_rate(
        [{"operator": "boundary_drop", "verdict": "CERTIFIED"}]
    )
    exposure = Exposure(**worst_case)
    assert exposure.model_dump() == worst_case
    assert exposure.false_certified_rate == 1.0
    assert exposure.measured is True
    assert exposure.by_operator["boundary_drop"] == {"certified": 1, "total": 1}

    # The specific typing is what earns its keep over the contract's bare
    # `{"type": "object"}`: a malformed count is a producer bug and must not
    # pass silently into a published number. (An earlier draft of this test
    # asserted only the round-trip, so de-typing the field to a bare `dict`
    # still passed — the type was never actually pinned.)
    with pytest.raises(ValidationError):
        Exposure(
            measured=True,
            false_certified_rate=1.0,
            by_operator={"boundary_drop": {"certified": "one", "total": 2}},
        )


def test_demo_traceability_fixture_loads_into_model():
    data = json.loads((ROOT / "fixtures" / "demo_traceability.json").read_text())
    matrix = TraceabilityMatrix(**data)
    assert matrix.run_id == "demo"
    assert [link.criterion_id for link in matrix.links] == ["AC-1", "AC-2"]
    assert all(link.evidence_tier == "E0" for link in matrix.links)
    assert all(link.locations == [] for link in matrix.links)
