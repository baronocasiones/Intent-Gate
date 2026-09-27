"""M9 — Stage 6 Emit + gate (R4 thin slice: derived exit_code, envelope,
traceability, honest unmeasured exposure).

Per-stage shape file per the M4 restructure. Pinned here: `exit_code` is
derived not hard-coded (0 iff CERTIFIED), the record echoes adjudicate and
extends it (D9 status beside the D16 verdict echo), traceability links cover
every verdict in both directions and conform to the contract's link shape, and
the exposure stub is unmeasured-never-zero. Out of scope: run_id (M10),
ledger, hash chain, weighted exposure.

**Seam guard added after the cold E2E (2026-09-27, Session 25):** the record is
flat, because three committed consumers read it flat — the frozen
`run.schema.json`, M14's `project_run_payload`, and M15's `runs.py`. The first
version of this file pinned a nested `record` wrapper, which every one of those
consumers missed: the artifact was correct while `GET /api/runs/{id}` served
`pending` + `[]`, hiding every verdict. Pinned here against the consumers, not
against a private design.
"""
import json
from pathlib import Path

import jsonschema

from app.gates import emit
from app.store.records import project_run_payload

ROOT = Path(__file__).resolve().parents[2]
CONTRACTS = ROOT / "contracts"
TRACEABILITY_SCHEMA = json.loads((ROOT / "contracts" / "traceability.schema.json").read_text())
EXPOSURE_SCHEMA = json.loads((ROOT / "contracts" / "exposure.schema.json").read_text())
RUN_SCHEMA = json.loads((ROOT / "contracts" / "run.schema.json").read_text())


def _validate_run_record(instance: dict) -> None:
    """Validate against `run.schema.json` with its relative `$ref` resolved —
    the same Draft7Validator + resolver treatment `test_schemas_contracts.py`
    applies (M17's pattern; a bare `jsonschema.validate` cannot resolve
    `verdict.schema.json` and raises `unknown url type` instead of reporting a
    schema problem)."""
    store = {
        (CONTRACTS / p.name).as_uri(): json.loads(p.read_text())
        for p in CONTRACTS.glob("*.schema.json")
    }
    resolver = jsonschema.RefResolver(
        base_uri=(CONTRACTS / "run.schema.json").as_uri(), referrer=RUN_SCHEMA, store=store
    )
    jsonschema.Draft7Validator(RUN_SCHEMA, resolver=resolver).validate(instance)


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
    """Brief AC: extend alongside, do not replace. The uppercase `verdict`
    echoes M8 (D16 — the badge mismatch is recorded, not fixed here); `stage`
    is emit's own per the stage convention, and the record is FLAT (Session 25
    seam fix — see `test_emit_output_is_readable_by_the_committed_consumers`)."""
    out = emit.run(_adjudicated("REJECTED", [_verdict("AC-2", "REJECTED", "E2", ["b.py:8"])]))
    assert out["stage"] == "emit"  # flipped 2026-09-27 (Session 25 seam fix)
    assert out["verdict"] == "REJECTED"
    assert out["status"] == "rejected"
    assert out["measured"] is False
    assert out["verdicts"] == [_verdict("AC-2", "REJECTED", "E2", ["b.py:8"])]


def test_emit_traceability_covers_every_verdict_in_both_directions():
    """A reviewer goes requirement→code and code→requirement: every verdict
    has exactly one link, every link matches its verdict's tier+locations."""
    verdicts = [
        _verdict("AC-1", "CERTIFIED", "E4", ["a.py:1"]),
        _verdict("AC-2", "REJECTED", "E2", ["b.py:8"]),
    ]
    links = emit.run(_adjudicated("REJECTED", verdicts))["traceability"]["links"]
    assert [(l["criterion_id"], l["evidence_tier"], l["locations"]) for l in links] == [
        ("AC-1", "E4", ["a.py:1"]),
        ("AC-2", "E2", ["b.py:8"]),
    ]


def test_emit_traceability_links_conform_to_the_contract():
    """`run_id` attaches at persist (M10/D15), so what is asserted here is the
    link shape M9 owns — validated with a scaffolding id that stands in for
    M10's, never as a product claim."""
    verdicts = [_verdict("AC-1", "CERTIFIED", "E4", ["a.py:1"])]
    links = emit.run(_adjudicated("CERTIFIED", verdicts))["traceability"]["links"]
    jsonschema.validate({"run_id": "m10-attaches-this", "links": links}, TRACEABILITY_SCHEMA)


def test_emit_exposure_is_unmeasured_never_zero():
    """Harness dropped (D-a): no number at all rather than a synthetic one.
    `measured: false` + null rate must stay visibly distinct from a measured
    0.0 — and conform to the contract while at it."""
    exposure = emit.run(_adjudicated("PENDING", []))["exposure"]
    assert exposure["false_certified_rate"] is None
    assert exposure["measured"] is False
    jsonschema.validate(exposure, EXPOSURE_SCHEMA)


def test_emit_tolerates_a_bare_dict():
    out = emit.run({})
    assert out["exit_code"] == 1
    assert out["verdict"] == "PENDING"
    assert out["status"] == "pending"
    assert out["verdicts"] == []
    assert out["traceability"] == {"links": []}


def test_emit_output_is_readable_by_the_committed_consumers():
    """The seam guard. M9's stage output IS the artifact payload M14 writes, so
    every consumer of a run record must find the record's keys where it looks.

    Three of them, none of them mine: the frozen `run.schema.json` (required
    keys), M14's `project_run_payload` (the strict-read projection), and M15's
    `runs.py` (a flat `artifact.get(...)` per key). A nested `record` wrapper
    passes every M9-only assertion and fails all three — which is what the cold
    E2E measured as a served run with `pending` and no verdicts.
    """
    verdicts = [
        _verdict("AC-1", "CERTIFIED", "E4", ["src/refund.py:64"]),
        _verdict("AC-2", "REJECTED", "E2", ["src/refund.py:88"]),
    ]
    out = emit.run(_adjudicated("REJECTED", verdicts))

    # 1. The contract's required keys, minus `run_id` (M10 attaches it at
    #    persist — asserted absent rather than silently tolerated).
    for key in ("status", "verdicts", "measured"):
        assert key in out, f"run record key {key!r} is not at the artifact top level"
    assert "run_id" not in out

    # 2. M14's projection finds the record (it drops only the superset extras).
    projected = project_run_payload(out)
    assert projected["status"] == "rejected"
    assert projected["verdicts"] == verdicts
    assert projected["measured"] is False

    # 3. The served shape validates once M10's id is attached, so the
    #    superset M9 emits is a conforming run record and not merely a
    #    look-alike.
    _validate_run_record({**out, "run_id": "m10-attaches-this"})
