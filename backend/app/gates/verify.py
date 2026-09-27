"""Stage 4 — Parallel verify: N independent workers, one per criterion group.

STUB (R4 thin slice): no real probes — M7 is XL and out of scope this build.
Under mock mode this emits the §1.7 demo findings for the demo criterion ids
and `undetermined` for anything else, so the chain is exercisable end to end
without a live call (Convention 4). Provenance is machine-readable
(`mode: "mock"`, `tokens_spent: 0`) and belongs in the runbook next to it —
never present these findings as live analysis. M7a/M7b replace the findings
assembly while keeping every key (rule 3); `criteria` is threaded because §1.8.3
requires M8 to enumerate criteria M7's dict is the only carrier of.
"""

# §1.7 demo findings, verbatim. AC-1 supported (exercised path, E4-worthy);
# AC-2 refuted by a positively observed contradicting construct (located, E2).
# The note texts are the demo contract's, not live observations.
_MOCK_FINDINGS = {
    "AC-1": {
        "probe": "ERROR_PATH",
        "result": "supported",
        "location": "src/refund.py:64",
        "note": "approval gate precedes capture",
    },
    "AC-2": {
        "probe": "ERROR_PATH",
        "result": "refuted",
        "location": "src/refund.py:88",
        "note": "no retry path",
    },
}


def run(parse_out: dict) -> dict:
    d = parse_out if isinstance(parse_out, dict) else {}
    criteria = d.get("criteria", [])
    if not isinstance(criteria, list):
        criteria = []
    findings = []
    for c in criteria:
        if not isinstance(c, dict) or not c.get("criterion_id"):
            continue
        cid = c["criterion_id"]
        if cid in _MOCK_FINDINGS:
            findings.append({"criterion_id": cid, **_MOCK_FINDINGS[cid]})
        else:
            findings.append(
                {
                    "criterion_id": cid,
                    "probe": "CODE_SEARCH",
                    "result": "undetermined",
                    "location": "",
                    "note": "stub: no probe ran (mock mode)",
                }
            )
    return {
        "stage": "verify",
        "ok": True,
        "findings": findings,
        "criteria": criteria,
        "mode": "mock",
        "tokens_spent": 0,
    }
