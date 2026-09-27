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
import typing
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

    Note the file name and the `title` disagree for one contract
    (`traceability.schema.json` has `title: TraceabilityMatrix`), so the two
    lookups below are deliberately separate.
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


def _contract_properties(title: str) -> dict:
    """The `properties` object a mirror must reproduce — titled contract, or the
    inline object an INLINE_MIRRORS entry points at.

    Three guards need this and none should re-derive it: getting the inline
    lookup subtly wrong makes a guard vacuously true, which is the worst failure
    a guard has.
    """
    if title in INLINE_MIRRORS:
        schema_file, path = INLINE_MIRRORS[title]
        item = _contracts_by_file()[schema_file]
        for part in path:
            # A segment names a field (so look inside `properties`) unless the
            # schema has no `properties` of its own — then it is a plain key,
            # e.g. an array's `items`.
            item = item["properties"][part] if part in item.get("properties", {}) else item[part]
        return item["properties"]
    return _contract_titles()[title]["properties"]


CONTRACT_TITLES = sorted(_contract_titles())
MIRROR_NAMES = sorted(_mirrors())
# Every mirror a structural guard must cover: the six titled contracts plus the
# one inline exception. Parametrising over CONTRACT_TITLES alone would silently
# skip `TraceabilityLink`, whose `evidence_tier` enum is then unchecked — the
# guards below are only as good as the set they run over.
ALL_MIRRORS = sorted(set(CONTRACT_TITLES) | {"TraceabilityLink"})

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


@pytest.mark.parametrize("title", ALL_MIRRORS)
def test_mirror_declares_no_field_its_contract_does_not(title):
    """The other direction, and the one that was missing.

    `test_model_fields_cover_contract_properties` asserts `contract ⊆ model`.
    That permits a model to carry a field no contract declares — and a mutation
    battery showed that hole was live: adding `evidence_tier` to the `Finding`
    mirror, a key `findings.schema.json` deliberately does not declare, failed
    nothing. So the strict layer could accept a tier the interchange layer never
    validated, which is precisely the inversion the module docstring warns about
    ("contracts are permissive, models are strict" — strict about the contract's
    shape, not about inventing its own).

    Equality is the correct relation here, not superset. It holds for all six
    mirrors today, and a model-only convenience field has a correct route: add
    it to the contract (M1 owns `contracts/`) and the mirror picks it up on both
    sides at once. Anything else means the strict layer decided something the
    contract layer did not.
    """
    declared = set(_contract_properties(title))
    extra = set(_mirrors()[title].model_fields) - declared
    assert not extra, (
        f"{title} declares {sorted(extra)}, which its contract does not. A model-only "
        f"field is unvalidated at the interchange layer — add it to the contract instead."
    )


@pytest.mark.parametrize("title", ALL_MIRRORS)
def test_mirror_field_types_are_the_contract_field_types(title):
    """The model's *types* are the contract's types, not merely its field names.

    The two structural guards above check which fields exist. Nothing checked
    what they are typed as, and a mutation battery found the gap live: narrowing
    `Finding.probe` from five probes to four, while `findings.schema.json` still
    declared five, failed no test at all. M7a would then have had its
    `ERROR_PATH` findings rejected by their own mirror — a loud failure, so not
    dangerous, but pure drift with nothing watching it.

    Round-trip tests cannot catch this class of change (test-suite.md
    Convention 8: a test that pins a value is not a test that pins a type). A
    narrower Literal still round-trips every value the existing tests happen to
    use. So this asserts on the annotation itself:

      * a field the contract declares with an `enum` must be a `Literal` with
        exactly those members, in that order;
      * a field the contract declares as a bare `"string"` must be annotated
        `str` — which is also what keeps a contract's *unenumerated* string
        unenumerated in the mirror, the failure behind
        `test_finding_result_is_not_narrowed_to_a_vocabulary_the_contract_defers`.

    Deliberately scoped to those two cases. Array, object, boolean and nullable
    fields are left alone: the models type some of those more specifically than
    the contract does on purpose (`Exposure.by_operator`), and a
    contract ⊆ model relation is the correct stance there, not equality.
    """
    model = _mirrors()[title]
    for field, spec in _contract_properties(title).items():
        annotation = model.model_fields[field].annotation
        where = f"{title}.{field}"
        if "enum" in spec:
            expected = tuple(spec["enum"])
            assert typing.get_origin(annotation) is typing.Literal, (
                f"{where} is annotated {annotation!r}, but its contract enumerates "
                f"{list(expected)} — a mirror may not be vaguer than its contract"
            )
            assert typing.get_args(annotation) == expected, (
                f"{where} allows {list(typing.get_args(annotation))}, its contract "
                f"allows {list(expected)}"
            )
        elif spec.get("type") == "string":
            assert annotation is str, (
                f"{where} is annotated {annotation!r}, not str. Where the contract "
                f"declares a bare string the mirror must not narrow it into a "
                f"vocabulary the contract layer left open."
            )


def test_finding_result_is_not_narrowed_to_a_vocabulary_the_contract_defers():
    """`result` is unenumerated in the contract on purpose; the strict layer must
    not quietly decide it.

    Widening `result`'s vocabulary is M7's call, not the contract layer's, and
    the model is a *mirror*. A mutation battery showed that narrowing
    `Finding.result` to `Literal["refuted", "supported"]` failed no test: the
    round-trip tests still passed, because a narrower type still round-trips
    every value they happened to use.

    Asserted on the annotation rather than on behaviour, for the reason in
    docs/test-suite.md Convention 8 — a test that pins a value is not a test
    that pins a type, and a narrowed Literal is a type change that round-trip
    equality cannot see. `test_mirror_field_types_are_the_contract_field_types`
    now covers this generically; this test stays because it is the assertion
    that carries the *reason*, and a comment is not a guard.
    """
    annotation = Finding.model_fields["result"].annotation
    assert annotation is str, (
        f"Finding.result is annotated {annotation!r}, not str. The contract "
        f"deliberately leaves this vocabulary unenumerated; deciding it in the "
        f"strict layer is M7's call made in the wrong place."
    )
    # ...and the contract half of the same non-decision, so the two are pinned together.
    schema = _contracts_by_file()["findings.schema.json"]
    assert "enum" not in schema["properties"]["result"]


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


def test_finding_loads_the_contract_example():
    """Real data through the mirror, not just a shape check.

    The three parity guards above prove `Finding`'s fields and types match the
    contract. None of them proves it can be *constructed*. `contracts/examples/
    findings.json` was only ever validated by `jsonschema` against the contract —
    never loaded into the model — so the mirror added in Session 21 was never
    exercised against real data. A model that cannot be constructed is
    decoration, and the M3 docstring promises round trips for the new models.
    """
    data = json.loads((ROOT / "contracts" / "examples" / "findings.json").read_text())
    finding = Finding(**data)
    assert finding.criterion_id == "AC-2"
    assert finding.probe == "ERROR_PATH"
    assert finding.result == "refuted"
    assert finding.location == "src/refund.py:88"
    assert finding.note == "no retry path"


def test_finding_roundtrip():
    f = Finding(
        criterion_id="AC-1",
        probe="LOGIC_TRACE",
        result="supported",
        location="src/refund.py:64",
        note="approval guard precedes capture",
    )
    assert Finding(**f.model_dump()) == f
    assert json.loads(f.model_dump_json()) == f.model_dump()


def test_finding_requires_all_five_fields():
    """No defaults, for the same reason `Criterion` has none.

    A missing `location` is not a finding — M7's own acceptance criteria call a
    finding with no location inadmissible evidence, so a default of `""` here
    would let an unlocated probe result validate as a well-formed one.
    """
    complete = {
        "criterion_id": "AC-1",
        "probe": "CODE_SEARCH",
        "result": "supported",
        "location": "src/refund.py:1",
        "note": "x",
    }
    assert Finding(**complete).location == "src/refund.py:1"
    for dropped in complete:
        incomplete = {k: v for k, v in complete.items() if k != dropped}
        with pytest.raises(ValidationError):
            Finding(**incomplete)


def test_finding_rejects_a_probe_outside_the_five():
    with pytest.raises(ValidationError):
        Finding(
            criterion_id="AC-1",
            probe="VIBE_CHECK",
            result="supported",
            location="src/refund.py:1",
            note="x",
        )


def test_finding_result_stays_an_open_string_and_the_example_uses_a_documented_value():
    """Two halves of the same non-decision, pinned together.

    The model half (`result` is a bare `str`, not a narrowed Literal) is asserted
    by `test_finding_result_is_not_narrowed_to_a_vocabulary_the_contract_defers`.
    This asserts the *documented* vocabulary is real rather than aspirational:
    the contract's own example must use one of the four values
    `docs/modules.md` 1.8.1 names. If M7 later introduces a fifth, this fails
    and the doc has to be updated with it — which is the point. M7 owns the
    vocabulary (its schema says so) and will define it as a module constant;
    until that lands this is the only mechanical anchor it has.
    """
    documented = {"refuted", "supported", "undetermined", "not_applicable"}
    data = json.loads((ROOT / "contracts" / "examples" / "findings.json").read_text())
    assert data["result"] in documented, (
        f"contracts/examples/findings.json uses result={data['result']!r}, which is "
        f"not one of the four values docs/modules.md 1.8.1 documents"
    )
    # ...and the mirror accepts all four, because its type is the open string the
    # contract specifies rather than a copy of the list.
    for value in documented:
        assert Finding(
            criterion_id="AC-1",
            probe="CODE_SEARCH",
            result=value,
            location="src/refund.py:1",
            note="x",
        ).result == value


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
    """Flipped 2026-09-27: assert the two copies of the demo run AGREE, rather
    than re-pinning M2's literals.

    This test asserted every link was `E0` with no locations — the all-stub
    matrix that predated Session 19 — written on a branch still holding the old
    fixture. M2 rewrote both fixtures to a real mixed run (AC-1 CERTIFIED/E4,
    AC-2 REJECTED/E2, both located) and correctly flipped its own guard in
    `test_schemas_contracts.py`, but not this one. The assertion was stale; the
    fixture was right. Convention 7 is the case where a guard is not flipped in
    the same change as the behaviour it pins.

    Cross-checking against `demo_run.json` is the shape
    `test_schemas_contracts.py::test_traceability_fixture_describes_the_same_run_as_the_run_fixture`
    already uses, and it is what makes this guard unable to go stale the same way
    twice: a future fixture rewrite moves both files together or fails here.
    """
    run = json.loads((ROOT / "fixtures" / "demo_run.json").read_text())
    data = json.loads((ROOT / "fixtures" / "demo_traceability.json").read_text())
    matrix = TraceabilityMatrix(**data)
    assert matrix.run_id == run["run_id"] == "demo"
    assert [link.criterion_id for link in matrix.links] == ["AC-1", "AC-2"]

    by_criterion = {v["criterion_id"]: v for v in run["verdicts"]}
    for link in matrix.links:
        verdict = by_criterion[link.criterion_id]
        assert link.evidence_tier == verdict["evidence_tier"]
        assert link.locations == verdict["locations"]

    # Agreement alone would be satisfied by two identical stubs, which is the
    # state this test previously pinned. These two lines are the property M2
    # actually landed: a real matrix, with a tier above E0 and real locations.
    assert any(link.evidence_tier != "E0" for link in matrix.links)
    assert all(link.locations for link in matrix.links)
