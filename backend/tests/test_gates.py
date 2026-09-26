"""Stage gates — docs/architecture.md §3 rows 1-6: stub shapes + chain order.

Each gate is a fixture-shaped stub until the gate logic lands (§11.3). These
tests pin the *contract shape* so stubs can be replaced by real logic without
silently changing the interface the pipeline and frontend rely on.
"""
from app.gates import adjudicate, emit, extract, ingest, parse, verify

GATE_ORDER = ("ingest", "extract", "parse", "verify", "adjudicate", "emit")


def test_ingest_returns_sorted_input_keys():
    out = ingest.run({"z": 1, "a": 2, "m": 3})
    assert out == {"stage": "ingest", "ok": True, "input_keys": ["a", "m", "z"]}


def test_ingest_handles_empty_payload():
    out = ingest.run({})
    assert out["input_keys"] == []


def test_extract_stub_shape():
    out = extract.run({"stage": "ingest", "ok": True, "input_keys": []})
    assert out == {"stage": "extract", "ok": True, "criteria": []}


def test_parse_stub_shape():
    out = parse.run({"stage": "extract", "ok": True, "criteria": []})
    assert out == {"stage": "parse", "ok": True, "ast": []}


def test_verify_stub_shape():
    out = verify.run({"stage": "parse", "ok": True, "ast": []})
    assert out == {"stage": "verify", "ok": True, "findings": []}


def test_adjudicate_returns_pending_verdict():
    out = adjudicate.run({"stage": "verify", "ok": True, "findings": []})
    assert out == {"stage": "adjudicate", "ok": True, "verdict": "PENDING"}


def test_emit_blocks_by_default():
    """Non-zero exit blocks the merge — the safe default for a gate (§4.4)."""
    out = emit.run({"stage": "adjudicate", "ok": True, "verdict": "PENDING"})
    assert out["stage"] == "emit"
    assert out["ok"] is True
    assert out["exit_code"] == 1
    assert out["exit_code"] != 0
    # emit echoes the adjudicate record through untouched
    assert out["record"]["stage"] == "adjudicate"
    assert out["record"]["verdict"] == "PENDING"


def test_stage_names_follow_architecture_order():
    """The six gate modules must expose stages in the Figure-6 / §3 order."""
    stages = [
        ingest.run({})["stage"],
        extract.run({})["stage"],
        parse.run({})["stage"],
        verify.run({})["stage"],
        adjudicate.run({})["stage"],
        emit.run({})["stage"],
    ]
    assert stages == list(GATE_ORDER)
