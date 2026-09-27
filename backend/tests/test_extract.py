"""M5 — Stage 2 Extract criteria (R4 thin slice, deterministic, no model).

Per-stage shape file per the M4 restructure (`test_gates.py` keeps only the
cross-module custody assertions). Behaviour pinned here: §1.7 demo split,
quality-gate rejections with reasons, stable ids, bundle threading (§1.8.3),
and the no-LLM control (§11 gap 9: the consumer half of dual-mode is M5
asserting it takes no client).
"""
import ast as _ast
from pathlib import Path

from app.gates import extract

DEMO_REQUIREMENT = (
    "AC-1: refunds over $100 require supervisor approval. "
    "AC-2: refund failures must be retried 3 times."
)

EXTRACT_SOURCE = Path(__file__).resolve().parents[1] / "app" / "gates" / "extract.py"


def _bundle(requirement="", **kw):
    base = {"stage": "ingest", "ok": True, "input_keys": []}
    base["requirement"] = requirement
    base.update(kw)
    return base


def test_extract_splits_the_demo_requirement_into_two_testable_criteria():
    """§1.7 target: AC-1 + AC-2, verbatim text, testable true, nothing rejected."""
    out = extract.run(_bundle(DEMO_REQUIREMENT))
    assert out["stage"] == "extract"
    assert out["ok"] is True
    assert out["criteria"] == [
        {
            "criterion_id": "AC-1",
            "text": "refunds over $100 require supervisor approval.",
            "testable": True,
        },
        {
            "criterion_id": "AC-2",
            "text": "refund failures must be retried 3 times.",
            "testable": True,
        },
    ]
    assert out["rejected"] == []


def test_extract_empty_requirement_is_a_valid_empty_result():
    """No findings is a valid result (chain rule) — never raise for empty."""
    for bundle in ({}, {"stage": "ingest"}, _bundle(""), _bundle(None), _bundle(42)):
        out = extract.run(bundle)
        assert out["criteria"] == []
        assert out["rejected"] == []


def test_extract_empty_criterion_text_is_rejected_with_a_reason():
    out = extract.run(_bundle("AC-1: refunds need approval. AC-2:   "))
    assert out["criteria"] == [
        {
            "criterion_id": "AC-1",
            "text": "refunds need approval.",
            "testable": True,
        }
    ]
    assert len(out["rejected"]) == 1
    assert "empty" in out["rejected"][0]["reason"]


def test_extract_compound_criterion_is_rejected_not_split():
    """"Refunds work and are fast" is two criteria, or one rejected criterion
    (brief §M5) — this stage rejects; splitting is the author's job."""
    out = extract.run(_bundle("AC-1: refunds work and are fast."))
    assert out["criteria"] == []
    assert len(out["rejected"]) == 1
    assert "compound" in out["rejected"][0]["reason"]
    assert out["rejected"][0]["text"] == "refunds work and are fast."


def test_extract_compound_rule_does_not_fire_on_short_joins():
    out = extract.run(_bundle("AC-1: terms and conditions apply."))
    assert out["criteria"] != []


def test_extract_vague_qualifier_is_rejected_naming_the_term():
    out = extract.run(_bundle("AC-1: the dashboard is user-friendly."))
    assert out["criteria"] == []
    assert len(out["rejected"]) == 1
    assert "user-friendly" in out["rejected"][0]["reason"]


def test_extract_duplicate_marker_rejects_the_second_occurrence():
    out = extract.run(_bundle("AC-1: first claim. AC-1: second claim."))
    assert [c["criterion_id"] for c in out["criteria"]] == ["AC-1"]
    assert out["criteria"][0]["text"] == "first claim."
    assert len(out["rejected"]) == 1
    assert "duplicate" in out["rejected"][0]["reason"]


def test_extract_ids_come_from_the_markers_and_are_stable_across_reruns():
    req = "AC-7: seventh. AC-2: second."
    first = extract.run(_bundle(req))
    second = extract.run(_bundle(req))
    assert [c["criterion_id"] for c in first["criteria"]] == ["AC-7", "AC-2"]
    assert first == second


def test_extract_threads_files_and_workspace_for_m6():
    """§1.8.3 custody: the pipeline threads verbatim, so M5 carries what M6
    needs to re-verify M4's hashes. A stage that drops a key breaks a consumer
    that is not in this file."""
    files = [{"path": "src/refund.py", "sha256": "ab" * 32}]
    out = extract.run(_bundle("AC-1: x.", files=files, workspace="/w"))
    assert out["files"] == files
    assert out["workspace"] == "/w"


def test_extract_defaults_threading_keys_when_upstream_is_a_stub():
    """Today's M4 always emits both, but the old stub bundle does not — M5
    must still return a well-formed stage, never KeyError."""
    out = extract.run({"stage": "ingest", "ok": True, "input_keys": []})
    assert out["files"] == []
    assert out["workspace"] == ""


def test_extract_imports_nothing_from_the_llm_package():
    """§11 gap 9, consumer half: M5 is deterministic, so the durable control is
    M5 asserting it takes no client. AST walk (M4's technique): a name in a
    docstring cannot trip it, a genuine import in any form can."""
    tree = _ast.parse(EXTRACT_SOURCE.read_text(encoding="utf-8"))
    imported = set()
    for node in _ast.walk(tree):
        if isinstance(node, _ast.Import):
            imported.update(a.asname or a.name for a in node.names)
        elif isinstance(node, _ast.ImportFrom):
            imported.add(node.module or "")
    assert not any(
        name == "app.llm" or name.startswith("app.llm.") or name == "llm"
        for name in imported
    ), imported
