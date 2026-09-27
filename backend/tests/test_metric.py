"""FALSE CERTIFIED RATE — docs/architecture.md §9 + Figure 6 "THE NUMBER".

Output shape must conform to contracts/exposure.schema.json (§9 claim). The
7 operator classes are the publishable metric's taxonomy (§3.5 of the module
record) — changing OPERATORS is a spec change, not a refactor.
"""
import json
from pathlib import Path

import jsonschema
import pytest

from app.metrics.false_certified import OPERATORS, false_certified_rate
from app.metrics.mutation_harness import (
    MutationRequest,
    mutate_criterion,
    run_mutation_suite,
)
from app.models.schemas import Criterion, Exposure

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


# M13's provisional operator corpus is deliberately explicit. D4 must replace
# these examples with genuine acceptance criteria before publishing a number.
MUTATION_EXAMPLES = {
    "boundary_drop": ("Refunds over $100 require approval", "Refunds require approval"),
    "comparison_inversion": (
        "Refunds over $100 require approval",
        "Refunds under $100 require approval",
    ),
    "threshold_weakening": ("Retry 3 times on failure", "Retry 2 times on failure"),
    "error_path_deletion": (
        "Approve refunds; on failure, retry 3 times",
        "Approve refunds",
    ),
    "normative_demotion": (
        "Refunds must require approval",
        "Refunds should require approval",
    ),
    "negative_constraint_removal": (
        "Approve refunds; never disclose card data",
        "Approve refunds",
    ),
    "untestability": (
        "Refunds over $100 require approval",
        "Refunds over $100 require approval",
    ),
}


def _requests():
    return [
        MutationRequest(
            operator=operator,
            criterion={"criterion_id": "AC-1", "text": source, "testable": True},
            context={"repo": "demo"},
        )
        for operator, (source, _) in MUTATION_EXAMPLES.items()
    ]


@pytest.mark.parametrize("operator", SEVEN_CLASSES)
def test_each_operator_changes_only_its_intended_criterion(operator):
    source, expected_text = MUTATION_EXAMPLES[operator]
    original = {"criterion_id": "AC-1", "text": source, "testable": True}
    copy = dict(original)
    mutated = mutate_criterion(original, operator)

    assert original == copy
    assert mutated["criterion_id"] == original["criterion_id"]
    assert mutated["text"] == expected_text
    assert mutated["testable"] is (operator != "untestability")
    assert mutated != original
    assert Criterion.model_validate(mutated).model_dump() == mutated
    schema = json.loads((ROOT / "contracts" / "criterion.schema.json").read_text())
    jsonschema.Draft7Validator(schema).validate(mutated)


def test_unsupported_operator_raises():
    with pytest.raises(ValueError, match="unsupported"):
        mutate_criterion(_requests()[0].criterion, "not_an_operator")


def test_threshold_change_skips_a_criterion_label_in_the_text():
    original = {"criterion_id": "AC-2", "text": "AC-2: retry 3 times", "testable": True}
    assert mutate_criterion(original, "threshold_weakening")["text"] == "AC-2: retry 2 times"


def test_comparison_inversion_requires_a_numeric_comparison():
    original = {"criterion_id": "AC-1", "text": "Recover over time", "testable": True}
    with pytest.raises(ValueError, match="comparison"):
        mutate_criterion(original, "comparison_inversion")


@pytest.mark.parametrize("operator", SEVEN_CLASSES)
def test_operator_without_a_target_fails_closed(operator):
    source = {"criterion_id": "AC-1", "text": "Log completed requests", "testable": True}
    if operator == "untestability":
        source["testable"] = False
    with pytest.raises(ValueError):
        mutate_criterion(source, operator)


def test_suite_runs_each_operator_once_in_declared_order_and_aggregates():
    requests = list(reversed(_requests()))
    original_criteria = [dict(request.criterion) for request in requests]
    calls = []
    verdicts = {
        "boundary_drop": "CERTIFIED",
        "comparison_inversion": "CONDITIONAL",
        "threshold_weakening": "REJECTED",
        "error_path_deletion": "PENDING",
        "normative_demotion": "REJECTED",
        "negative_constraint_removal": "REJECTED",
        "untestability": "REJECTED",
    }

    def runner(case):
        calls.append(case)
        verdict = verdicts[case.operator]
        assert case.context == {"repo": "demo"}
        assert case.mutated != case.original
        return {
            "stage": "emit",
            "ok": True,
            "exit_code": 0 if verdict == "CERTIFIED" else 1,
            "record": {"stage": "adjudicate", "verdict": verdict},
        }

    exposure = run_mutation_suite(requests, runner)
    assert [case.operator for case in calls] == list(OPERATORS)
    assert [dict(request.criterion) for request in requests] == original_criteria
    assert exposure["measured"] is True
    assert exposure["false_certified_rate"] == 1 / 7
    assert set(exposure["by_operator"]) == set(OPERATORS)
    assert exposure["by_operator"]["boundary_drop"] == {"certified": 1, "total": 1}
    assert all(
        exposure["by_operator"][op] == {"certified": 0, "total": 1}
        for op in OPERATORS[1:]
    )
    assert Exposure.model_validate(exposure).model_dump() == exposure
    schema = json.loads((ROOT / "contracts" / "exposure.schema.json").read_text())
    jsonschema.Draft7Validator(schema).validate(exposure)


def test_suite_accepts_top_level_verdict_from_an_injected_test_runner():
    exposure = run_mutation_suite(
        _requests(), lambda _case: {"verdict": "REJECTED"}
    )
    assert exposure["measured"] is True
    assert exposure["false_certified_rate"] == 0.0
    assert exposure != false_certified_rate([])


def test_suite_rejects_empty_missing_and_duplicate_cases_before_running():
    calls = []
    runner = lambda case: calls.append(case) or {"verdict": "REJECTED"}
    for requests in ([], _requests()[:-1], _requests()[:-1] + [_requests()[0]]):
        assert run_mutation_suite(requests, runner) == false_certified_rate([])
    assert calls == []


def test_unapplicable_case_prevents_all_runner_calls():
    requests = _requests()
    requests[3] = MutationRequest(
        "error_path_deletion",
        {"criterion_id": "AC-1", "text": "Log completed requests", "testable": True},
    )
    calls = []
    assert run_mutation_suite(requests, lambda case: calls.append(case)) == false_certified_rate([])
    assert calls == []


@pytest.mark.parametrize(
    "bad_run",
    [
        {},
        {"verdict": "MAYBE"},
        {"record": {}},
        {"record": {"verdict": "CERTIFIED"}, "exit_code": 1},
        {"record": {"verdict": "REJECTED"}, "exit_code": 0},
        {"record": {"verdict": "REJECTED"}, "exit_code": None},
        {"record": {"verdict": "CERTIFIED"}, "ok": False},
        {"record": {"verdict": "CERTIFIED"}, "ok": None},
    ],
)
def test_missing_invalid_or_conflicting_verdict_never_publishes_partial_metric(bad_run):
    calls = []

    def runner(case):
        calls.append(case)
        return {"verdict": "REJECTED"} if len(calls) < 3 else bad_run

    assert run_mutation_suite(_requests(), runner) == false_certified_rate([])
    assert len(calls) == 3


def test_runner_exception_never_publishes_partial_metric():
    calls = []

    def runner(case):
        calls.append(case)
        if len(calls) == 3:
            raise RuntimeError("pipeline unavailable")
        return {"verdict": "CERTIFIED"}

    assert run_mutation_suite(_requests(), runner) == false_certified_rate([])
    assert len(calls) == 3
