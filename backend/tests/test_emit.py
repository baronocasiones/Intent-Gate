"""M9 — Stage 6 Emit + gate (R4 thin slice: derived exit_code, envelope,
traceability, honest unmeasured exposure).

Per-stage shape file per the M4 restructure. Pinned here: `exit_code` is
derived not hard-coded (0 iff CERTIFIED), the record echoes adjudicate and
extends it (D9 status beside the D16 verdict echo), traceability links cover
every verdict in both directions and conform to the contract's link shape, and
the exposure stub is unmeasured-never-zero. Out of scope: run_id (M10),
ledger, hash chain, weighted exposure.
"""
import json
from pathlib import Path

import jsonschema

from app.gates import emit

ROOT = Path(__file__).resolve().parents[2]
TRACEABILITY_SCHEMA = json.loads((ROOT / "contracts" / "traceability.schema.json").read_text())
EXPOSURE_SCHEMA = json.loads((ROOT / "contracts" / "exposure.schema.json").read_text())


def _adjudicated(verdict, verdicts):
    return {"stage": "adjudicate", "ok": True, "verdict": verdict, "verdicts": verdicts}


def _verdict(cid, verdict, tier, locations):
    return {
        "criterion_id": cid,
        "verdict": verdict,
        "evidence_tier": tier,
        "locations": locations,
        "rationale": f"{cid} {verdict} at {tier}",
    }


def test_emit_exit_code_is_derived_not_hard_coded():
    """The only merge signal: 0 for CERTIFIED, 1 for anything else — including
    verdicts this stage has never seen (fail-closed default survives)."""
    yes = [_verdict("AC-1", "CERTIFIED", "E4", ["a.py:1"])]
    assert emit.run(_adjudicated("CERTIFIED", yes))["exit_code"] == 0
    for verdict in ("REJECTED", "CONDITIONAL", "PENDING", "BOGUS", None):
        v = [_verdict("AC-1", "PENDING", "E0", [])]
        assert emit.run(_adjudicated(verdict, v))["exit_code"] == 1


def test_emit_record_echoes_adjudicate_and_extends_it():
    """Brief AC: extend alongside, do not replace. `stage` + uppercase
    `verdict` echo M8; lowercase D9 `status` sits beside them (D16 — the badge
    mismatch is recorded, not fixed here)."""
    out = emit.run(_adjudicated("REJECTED", [_verdict("AC-2", "REJECTED", "E2", ["b.py:8"])]))
    record = out["record"]
    assert record["stage"] == "adjudicate"
    assert record["verdict"] == "REJECTED"
    assert record["status"] == "rejected"
    assert record["measured"] is False
    assert record["verdicts"] == [_verdict("AC-2", "REJECTED", "E2", ["b.py:8"])]


def test_emit_traceability_covers_every_verdict_in_both_directions():
    """A reviewer goes requirement→code and code→requirement: every verdict
    has exactly one link, every link matches its verdict's tier+locations."""
    verdicts = [
        _verdict("AC-1", "CERTIFIED", "E4", ["a.py:1"]),
        _verdict("AC-2", "REJECTED", "E2", ["b.py:8"]),
    ]
    links = emit.run(_adjudicated("REJECTED", verdicts))["record"]["traceability"]["links"]
    assert [(l["criterion_id"], l["evidence_tier"], l["locations"]) for l in links] == [
        ("AC-1", "E4", ["a.py:1"]),
        ("AC-2", "E2", ["b.py:8"]),
    ]


def test_emit_traceability_links_conform_to_the_contract():
    """`run_id` attaches at persist (M10/D15), so what is asserted here is the
    link shape M9 owns — validated with a scaffolding id that stands in for
    M10's, never as a product claim."""
    verdicts = [_verdict("AC-1", "CERTIFIED", "E4", ["a.py:1"])]
    links = emit.run(_adjudicated("CERTIFIED", verdicts))["record"]["traceability"]["links"]
    jsonschema.validate({"run_id": "m10-attaches-this", "links": links}, TRACEABILITY_SCHEMA)


def test_emit_exposure_is_unmeasured_never_zero():
    """Harness dropped (D-a): no number at all rather than a synthetic one.
    `measured: false` + null rate must stay visibly distinct from a measured
    0.0 — and conform to the contract while at it."""
    exposure = emit.run(_adjudicated("PENDING", []))["record"]["exposure"]
    assert exposure["false_certified_rate"] is None
    assert exposure["measured"] is False
    jsonschema.validate(exposure, EXPOSURE_SCHEMA)


def test_emit_tolerates_a_bare_dict():
    out = emit.run({})
    assert out["exit_code"] == 1
    assert out["record"]["verdict"] == "PENDING"
    assert out["record"]["status"] == "pending"
    assert out["record"]["verdicts"] == []
    assert out["record"]["traceability"] == {"links": []}
