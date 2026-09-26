"""Scaffold smoke tests — every gate stub + pipeline path + policy guard."""
from app.attestor.policy import assert_read_only, GRANTS
from app.metrics.false_certified import false_certified_rate, OPERATORS
from app.orchestrator.pipeline import run_pipeline


def test_pipeline_stub_path():
    out = run_pipeline({"pr": 1})
    assert out["stage"] == "emit"
    assert out["exit_code"] == 1


def test_attestor_policy_ok():
    assert_read_only(GRANTS)


def test_metric_unmeasured_empty():
    res = false_certified_rate([])
    assert res["measured"] is False
    assert set(res["by_operator"]) == set(OPERATORS)
