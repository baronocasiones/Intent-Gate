"""FALSE CERTIFIED RATE — docs/architecture.md §9 + Figure 6 "THE NUMBER".

Output shape must conform to contracts/exposure.schema.json (§9 claim). The
7 operator classes are the publishable metric's taxonomy (§3.5 of the module
record) — changing OPERATORS is a spec change, not a refactor.
"""
import json
from pathlib import Path

import jsonschema

from app.metrics.false_certified import OPERATORS, false_certified_rate

ROOT = Path(__file__).resolve().parents[2]

SEVEN_CLASSES = (
    "boundary_drop",
    "comparison_inversion",
    "threshold_weakening",
    "error_path_deletion",
    "normative_demotion",
    "negative_constraint_removal",
    "untestability",
)


def test_operators_are_exactly_the_seven_mutation_classes():
    assert OPERATORS == SEVEN_CLASSES
    assert len(OPERATORS) == 7


def test_empty_input_is_unmeasured():
    res = false_certified_rate([])
    assert res["false_certified_rate"] is None
    assert res["measured"] is False


def test_empty_input_still_keys_all_seven_operators():
    res = false_certified_rate([])
    assert set(res["by_operator"]) == set(OPERATORS)
    for counts in res["by_operator"].values():
        assert counts == {"certified": 0, "total": 0}


def test_all_certified_gives_rate_one():
    results = [{"operator": op, "verdict": "CERTIFIED"} for op in OPERATORS]
    res = false_certified_rate(results)
    assert res["false_certified_rate"] == 1.0
    assert res["measured"] is True


def test_none_certified_gives_rate_zero():
    results = [{"operator": op, "verdict": "REJECTED"} for op in OPERATORS]
    res = false_certified_rate(results)
    assert res["false_certified_rate"] == 0.0
    assert res["measured"] is True


def test_mixed_verdicts_rate_is_ratio():
    results = [
        {"operator": "boundary_drop", "verdict": "CERTIFIED"},
        {"operator": "boundary_drop", "verdict": "REJECTED"},
        {"operator": "boundary_drop", "verdict": "CONDITIONAL"},
    ]
    res = false_certified_rate(results)
    assert res["false_certified_rate"] == 1 / 3
    assert res["by_operator"]["boundary_drop"] == {"certified": 1, "total": 3}


def test_per_operator_breakdown_is_independent():
    results = [
        {"operator": "boundary_drop", "verdict": "CERTIFIED"},
        {"operator": "untestability", "verdict": "REJECTED"},
    ]
    res = false_certified_rate(results)
    assert res["by_operator"]["boundary_drop"] == {"certified": 1, "total": 1}
    assert res["by_operator"]["untestability"] == {"certified": 0, "total": 1}
    assert res["false_certified_rate"] == 0.5


def test_unknown_operator_is_skipped():
    """Unknown operators must not inflate the denominator (or break the fn)."""
    results = [{"operator": "not_a_real_class", "verdict": "CERTIFIED"}]
    res = false_certified_rate(results)
    assert res["measured"] is False
    assert res["false_certified_rate"] is None


def test_missing_verdict_counts_in_total_not_certified():
    res = false_certified_rate([{"operator": "boundary_drop"}])
    assert res["by_operator"]["boundary_drop"] == {"certified": 0, "total": 1}
    assert res["false_certified_rate"] == 0.0


def test_output_validates_against_exposure_contract():
    """§9 claim: output shape matches contracts/exposure.schema.json."""
    schema = json.loads((ROOT / "contracts" / "exposure.schema.json").read_text())
    validator = jsonschema.Draft7Validator(schema)
    for res in (
        false_certified_rate([]),
        false_certified_rate([{"operator": "boundary_drop", "verdict": "CERTIFIED"}]),
        false_certified_rate(
            [{"operator": op, "verdict": "REJECTED"} for op in OPERATORS]
        ),
    ):
        validator.validate(res)
