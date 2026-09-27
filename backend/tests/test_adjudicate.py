"""M8 — Stage 5 Adjudicate (R4 thin slice: real ladder, pure logic, no model).

Per-stage shape file per the M4 restructure. Pinned here: the §1.7 demo pair
(AC-1 CERTIFIED@E4, AC-2 REJECTED@E2), the D3 aggregation table, fail-closed
edges (`verdicts: []` → PENDING per §1.8.3; unrecognised results loud per
§1.8.1; unexamined criteria PENDING per rule 6), and contract conformance of
every verdict against `verdict.schema.json`.
"""
import json
from pathlib import Path

import jsonschema

from app.gates import adjudicate

ROOT = Path(__file__).resolve().parents[2]
VERDICT_SCHEMA = json.loads((ROOT / "contracts" / "verdict.schema.json").read_text())


def _finding(cid, probe, result, location, note="n"):
    return {
        "criterion_id": cid,
        "probe": probe,
        "result": result,
        "location": location,
        "note": note,
    }


def _run(findings, criteria):
    return adjudicate.run(
        {"stage": "verify", "ok": True, "findings": findings, "criteria": criteria}
    )


def _crit(cid):
    return {"criterion_id": cid, "text": f"{cid} text", "testable": True}


def _by_id(out):
    return {v["criterion_id"]: v for v in out["verdicts"]}


def test_adjudicate_demo_pair_certified_and_rejected():
    """§1.7 target: AC-1 supported-exercised → CERTIFIED@E4; AC-2 refuted-located
    → REJECTED@E2; run REJECTED."""
    out = _run(
        [
            _finding("AC-1", "ERROR_PATH", "supported", "src/refund.py:64", "gate precedes"),
            _finding("AC-2", "ERROR_PATH", "refuted", "src/refund.py:88", "no retry path"),
        ],
        [_crit("AC-1"), _crit("AC-2")],
    )
    assert out["stage"] == "adjudicate"
    assert out["ok"] is True
    assert out["verdict"] == "REJECTED"
    by_id = _by_id(out)
    assert by_id["AC-1"]["verdict"] == "CERTIFIED"
    assert by_id["AC-1"]["evidence_tier"] == "E4"
    assert by_id["AC-1"]["locations"] == ["src/refund.py:64"]
    assert by_id["AC-2"]["verdict"] == "REJECTED"
    assert by_id["AC-2"]["evidence_tier"] == "E2"
    assert by_id["AC-2"]["locations"] == ["src/refund.py:88"]


def test_adjudicate_empty_verdicts_is_pending_never_fail_open():
    """§1.8.3: M8 cannot enumerate a criterion it never saw, so `verdicts: []`
    must resolve to PENDING — a run with nothing to check reads as "no
    evidence gathered", never "no problems found"."""
    for out in (_run([], []), adjudicate.run({})):
        assert out["verdict"] == "PENDING"
        assert out["verdicts"] == []


def test_adjudicate_all_certified_certifies_the_run():
    out = _run(
        [
            _finding("AC-1", "ERROR_PATH", "supported", "a.py:1"),
            _finding("AC-2", "CODE_SEARCH", "supported", "b.py:2"),
            _finding("AC-2", "ERROR_PATH", "supported", "b.py:9"),
        ],
        [_crit("AC-1"), _crit("AC-2")],
    )
    assert out["verdict"] == "CERTIFIED"
    assert all(v["verdict"] == "CERTIFIED" for v in out["verdicts"])


def test_adjudicate_supported_below_e4_is_conditional():
    """D1: CERTIFIED requires E4; E2–E3 support is CONDITIONAL with the ledger
    remainder named in the rationale (the ledger itself is M9/out of scope)."""
    out = _run([_finding("AC-1", "CODE_SEARCH", "supported", "a.py:1")], [_crit("AC-1")])
    by_id = _by_id(out)
    assert by_id["AC-1"]["verdict"] == "CONDITIONAL"
    assert by_id["AC-1"]["evidence_tier"] == "E2"
    assert "E4" in by_id["AC-1"]["rationale"]
    assert out["verdict"] == "CONDITIONAL"


def test_adjudicate_rejected_dominates_conditional():
    out = _run(
        [
            _finding("AC-1", "CODE_SEARCH", "supported", "a.py:1"),
            _finding("AC-2", "CODE_SEARCH", "refuted", "b.py:2"),
        ],
        [_crit("AC-1"), _crit("AC-2")],
    )
    assert out["verdict"] == "REJECTED"


def test_adjudicate_undecided_probes_are_non_supporting():
    out = _run(
        [
            _finding("AC-1", "ABSENCE_CHECK", "undetermined", "", "absence undecidable"),
            _finding("AC-1", "CODE_SEARCH", "not_applicable", "", "n/a"),
        ],
        [_crit("AC-1")],
    )
    by_id = _by_id(out)
    assert by_id["AC-1"]["verdict"] == "PENDING"
    assert by_id["AC-1"]["evidence_tier"] == "E1"
    assert out["verdict"] == "PENDING"


def test_adjudicate_unrecognised_result_is_fail_closed_and_loud():
    """§1.8.1: non-supporting (never raises a tier or certifies), named in the
    rationale (never silently absorbed), tier capped at E1."""
    out = _run([_finding("AC-1", "CODE_SEARCH", "REFUTED", "a.py:1")], [_crit("AC-1")])
    by_id = _by_id(out)
    assert by_id["AC-1"]["verdict"] == "PENDING"
    assert by_id["AC-1"]["evidence_tier"] == "E1"
    assert "REFUTED" in by_id["AC-1"]["rationale"]
    assert out["verdict"] == "PENDING"


def test_adjudicate_criterion_with_no_findings_is_pending_not_examined():
    """Rule 6: no findings is not silent certification."""
    out = _run([], [_crit("AC-9")])
    by_id = _by_id(out)
    assert by_id["AC-9"]["verdict"] == "PENDING"
    assert by_id["AC-9"]["evidence_tier"] == "E0"
    assert "not examined" in by_id["AC-9"]["rationale"]


def test_adjudicate_locations_aggregate_everything_examined():
    """M8 AC: `locations[]` lists everything examined, not just the deciding one."""
    out = _run(
        [
            _finding("AC-1", "CODE_SEARCH", "supported", "a.py:1"),
            _finding("AC-1", "LOGIC_TRACE", "supported", "a.py:9"),
        ],
        [_crit("AC-1")],
    )
    assert _by_id(out)["AC-1"]["locations"] == ["a.py:1", "a.py:9"]


def test_adjudicate_rationales_are_criterion_specific():
    out = _run(
        [_finding("AC-1", "ERROR_PATH", "supported", "a.py:1")], [_crit("AC-1")]
    )
    for v in out["verdicts"]:
        assert v["rationale"]
        assert v["criterion_id"] in v["rationale"]
        assert v["verdict"] in v["rationale"]


def test_adjudicate_finding_for_unknown_criterion_is_loud_pending():
    out = _run([_finding("AC-99", "CODE_SEARCH", "supported", "a.py:1")], [_crit("AC-1")])
    by_id = _by_id(out)
    assert by_id["AC-99"]["verdict"] == "PENDING"
    assert "never extracted" in by_id["AC-99"]["rationale"]
    assert out["verdict"] == "PENDING"  # AC-1 unexamined + AC-99 anomalous


def test_adjudicate_verdicts_conform_to_the_verdict_contract():
    out = _run(
        [
            _finding("AC-1", "ERROR_PATH", "supported", "src/refund.py:64"),
            _finding("AC-2", "ERROR_PATH", "refuted", "src/refund.py:88"),
        ],
        [_crit("AC-1"), _crit("AC-2")],
    )
    for v in out["verdicts"]:
        jsonschema.validate(v, VERDICT_SCHEMA)


def test_adjudicate_threads_criteria_for_m9():
    """§1.8.3: M9 builds traceability for examined AND unexamined criteria, so
    M8 passes the enumeration on."""
    criteria = [_crit("AC-1"), _crit("AC-2")]
    assert _run([], criteria)["criteria"] == criteria
