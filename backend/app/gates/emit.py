"""Stage 6 — Emit + gate: run envelope, traceability matrix, derived exit_code.

Thin slice (R4): `exit_code` is DERIVED — `0` iff the run-level verdict is
CERTIFIED, `1` otherwise (the old always-1 was the correct fail-closed default;
this keeps it for every non-certified path). The stage output echoes the
adjudicate verdict and extends it into the servable run record, flat:
lowercase D9 `status` (D16: both keys are kept — the badge mismatch is M1/M15/
M16's to settle, not papered over here), `measured: False`, the verdicts
verbatim, the bidirectional traceability matrix, and an honestly-unmeasured
exposure stub (rate null + measured false, conforming to `exposure.schema.json`
— never a synthetic number).

Not this build (contracts frozen, D15 uncontracted): `run_id` (M10 attaches it
at persist — nothing here mints ids), the review-debt ledger, the cross-file
hash chain (M14's `prev_digest` seam waits for it), weighted exposure.
"""

_STATUS = {
    "CERTIFIED": "certified",
    "CONDITIONAL": "conditional",
    "REJECTED": "rejected",
    "PENDING": "pending",
}

_UNMEASURED_EXPOSURE = {"false_certified_rate": None, "measured": False, "by_operator": {}}


def _link(verdict: dict) -> dict:
    locations = verdict.get("locations", [])
    if not isinstance(locations, list):
        locations = []
    tier = verdict.get("evidence_tier", "E0")
    if tier not in ("E0", "E1", "E2", "E3", "E4", "E5", "E6"):
        tier = "E0"
    return {
        "criterion_id": verdict.get("criterion_id", "?"),
        "locations": [str(loc) for loc in locations],
        "evidence_tier": tier,
    }


def run(adjudicate_out: dict) -> dict:
    d = adjudicate_out if isinstance(adjudicate_out, dict) else {}
    verdict = d.get("verdict", "PENDING")
    if verdict not in _STATUS:  # M8 only emits the four; anything else blocks
        verdict = "PENDING"
    verdicts = d.get("verdicts", [])
    if not isinstance(verdicts, list):
        verdicts = []

    # The run record sits FLAT alongside the stage envelope, like every other
    # stage in the chain (extract/parse/adjudicate all return `stage`/`ok` plus
    # their payload inline). Session 25 seam fix: a nested `record` wrapper
    # made this the only non-flat stage, and three committed consumers read
    # these keys at the top level — `run.schema.json` (frozen, requires
    # status/verdicts/measured), M14's `project_run_payload`, and M15's
    # `runs.py`. The cold E2E caught it: the artifact was correct while the
    # served run showed `pending` + `[]`, hiding the whole audit trail.
    return {
        "stage": "emit",
        "ok": True,
        "exit_code": 0 if verdict == "CERTIFIED" else 1,
        "verdict": verdict,  # adjudicate echo (uppercase enum; D16 re: `status`)
        "status": _STATUS[verdict],
        "measured": False,
        "verdicts": verdicts,
        "traceability": {
            "links": [_link(v) for v in verdicts if isinstance(v, dict)],
            # `run_id` attaches at persist (M10) — D15's envelope is M1's
            # contract to write, and this stage mints no ids.
        },
        "exposure": dict(_UNMEASURED_EXPOSURE),
    }
