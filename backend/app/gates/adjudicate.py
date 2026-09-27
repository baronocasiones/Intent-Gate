"""Stage 5 — Adjudicate: findings → E0–E6 tiers → per-criterion + run verdicts.

Pure logic over M7's output (no model in this stage either): the tier is
DERIVED here, never carried on a finding (D1, ratified — §1.4; §1.8.4).
Result vocabulary is §1.8.1's four values; `undetermined` and
`not_applicable` never support (rule 6); absence is never refutation (§1.8.2).

Tier interpretation this stage commits to (demo-anchored, recorded in the
Session 25 log because §1.8.4's table is silent on the cell): higher tiers
measure confidence in a *satisfying* implementation. A `refuted` finding with a
location is a located contradiction — E2, matching the shipped `demo_run.json`
(AC-2 REJECTED at E2 on one located contradiction and no more). A refutation
never climbs to E3/E4 on probe strength.
"""

# Probe ceilings for *supporting* observations (§1.8.4). ABSENCE_CHECK is
# absent on purpose: E5 needs the adversarial pass M7b owns, and a bare
# absence claim is not decidable deterministically (§1.8.2) — it contributes
# E1, like any other ran-but-undecided observation.
CEILINGS = {"CODE_SEARCH": 2, "LOGIC_TRACE": 3, "STATE_CHECK": 3, "ERROR_PATH": 4}

_TIERS = ("E0", "E1", "E2", "E3", "E4", "E5", "E6")

_RECOGNIZED = ("refuted", "supported", "undetermined", "not_applicable")


def _tier_of(findings: list[dict]) -> tuple[int, list[str]]:
    """Highest justified tier index + loud notes (unrecognised results are
    named here so the caller can put them in the rationale — §1.8.1)."""
    notes: list[str] = []
    best = 0
    seen_any = False
    for f in findings:
        if not isinstance(f, dict):
            continue
        seen_any = True
        result = f.get("result")
        probe = f.get("probe")
        located = bool(f.get("location"))
        if result not in _RECOGNIZED:
            notes.append(f"probe reported {result!r}, which is not a value this gate understands")
            best = max(best, 1)
        elif result in ("undetermined", "not_applicable"):
            best = max(best, 1)
        elif not located:
            best = max(best, 1)
        elif result == "refuted":
            best = max(best, 2)  # located contradiction — never higher
        elif probe in CEILINGS:
            best = max(best, CEILINGS[probe])
        else:  # ABSENCE_CHECK or unknown probe with a determinate claim
            notes.append(f"determinate {result!r} from {probe!r} carries no tier without its pass")
            best = max(best, 1)
    if not seen_any:
        return 0, notes
    return max(best, 1), notes


def _adjudicate_one(cid: str, findings: list[dict], examined: bool) -> dict:
    tier_idx, notes = _tier_of(findings)
    tier = _TIERS[tier_idx]
    locations = sorted({f["location"] for f in findings if isinstance(f, dict) and f.get("location")})
    refuted = [f for f in findings if isinstance(f, dict) and f.get("result") == "refuted"]
    supported = [f for f in findings if isinstance(f, dict) and f.get("result") == "supported"]

    if refuted:
        verdict = "REJECTED"
        why = f"{refuted[0].get('probe')} refuted at {refuted[0].get('location') or 'no location'}"
        detail = (refuted[0].get("note") or "").strip()
        rationale = f"{cid} REJECTED at {tier}: {why}" + (f" ({detail})" if detail else "")
    elif tier_idx >= 4 and supported:
        verdict = "CERTIFIED"
        by = sorted({f.get("probe") for f in supported if f.get("probe") in CEILINGS})
        rationale = f"{cid} CERTIFIED at {tier}: {', '.join(by)} supported at {', '.join(locations)}"
    elif supported and tier_idx >= 2:
        verdict = "CONDITIONAL"
        rationale = (
            f"{cid} CONDITIONAL at {tier}: supported but not exercised — "
            f"E4 check outstanding (ledger remainder)"
        )
    elif not examined:
        verdict = "PENDING"
        rationale = f"{cid} PENDING at {tier}: criterion not examined"
    else:
        verdict = "PENDING"
        rationale = f"{cid} PENDING at {tier}: probes ran but decided nothing"
    if notes:
        rationale += "; " + "; ".join(notes)
    return {
        "criterion_id": cid,
        "verdict": verdict,
        "evidence_tier": tier,
        "locations": locations,
        "rationale": rationale,
    }


def run(verify_out: dict) -> dict:
    d = verify_out if isinstance(verify_out, dict) else {}
    findings = d.get("findings", [])
    if not isinstance(findings, list):
        findings = []
    criteria = d.get("criteria", [])
    if not isinstance(criteria, list):
        criteria = []

    by_criterion: dict[str, list[dict]] = {}
    for f in findings:
        if isinstance(f, dict) and f.get("criterion_id"):
            by_criterion.setdefault(f["criterion_id"], []).append(f)

    verdicts: list[dict] = []
    seen: set[str] = set()
    for c in criteria:
        if not isinstance(c, dict) or not c.get("criterion_id"):
            continue
        cid = c["criterion_id"]
        seen.add(cid)
        fs = by_criterion.get(cid, [])
        verdicts.append(_adjudicate_one(cid, fs, examined=bool(fs)))
    for cid in sorted(by_criterion):
        if cid not in seen:  # finding for a criterion never extracted — loud PENDING
            v = _adjudicate_one(cid, by_criterion[cid], examined=True)
            v["verdict"] = "PENDING"
            v["rationale"] = (
                f"{cid} PENDING at {v['evidence_tier']}: "
                f"finding references a criterion that was never extracted"
            )
            verdicts.append(v)

    if any(v["verdict"] == "REJECTED" for v in verdicts):
        overall = "REJECTED"
    elif all(v["verdict"] == "CERTIFIED" for v in verdicts) and verdicts:
        overall = "CERTIFIED"
    elif any(v["verdict"] == "CONDITIONAL" for v in verdicts):
        overall = "CONDITIONAL"
    else:
        overall = "PENDING"  # verdicts == [] lands here (§1.8.3: never fail-open)
    return {
        "stage": "adjudicate",
        "ok": True,
        "verdict": overall,
        "verdicts": verdicts,
        "criteria": criteria,
    }
