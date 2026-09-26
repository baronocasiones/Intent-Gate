"""Receipt renderer - a human-readable rendering of a signed run artefact.

The separation enforced here: the JSON artefact is signed, the HTML is only
a rendering. ``render`` never hashes its own bytes - it recomputes the digest
over the canonical body exactly as ``store/artifacts.py`` does and reports what
it finds. A missing digest, or one that does not match its body, is printed as
the absence of a signature however confident a badge would otherwise look.

Deterministic by construction: no clock, no randomness, no dict-order
dependence. The same artefact in produces byte-identical HTML out, so the
rendering can always be re-derived and re-checked against the artefact. The
receipt therefore carries no generation timestamp of its own - it reports only
times evidenced by the record.

Six honesty rules are enforced here as named predicates so each is testable on
its own: signed-ness is derived rather than asserted, the evidence ladder is
marked provisional while its semantics are unratified, the hash-chain state is
stated plainly, an unmeasured exposure never renders as a number, absent
artefacts are named instead of faked, and PENDING is never dressed as decided.
"""
import hashlib
import html
import json
from typing import Any

# The artefacts the spec's emitted-artefact list names, as keys looked up on
# the run artefact. The fifth - the signed evidence record - is the envelope
# itself, so it is not looked up here; it is the integrity footer.
DATA_ARTEFACTS = ("verdicts", "traceability", "ledger", "exposure")

VERDICTS = ("CERTIFIED", "CONDITIONAL", "REJECTED", "PENDING")
TIERS = ("E0", "E1", "E2", "E3", "E4", "E5", "E6")

# The source names the E0-E6 evidence ladder but never defines the tiers, so
# the ladder is proposed, not ratified. Until that is settled the receipt
# renders the tiers marked provisional and never offers one as a certified
# level of evidence. Flip to False only when the ladder is ratified.
LADDER_PROVISIONAL = True

# artifacts.py hashes a single file; there is no cross-file chain, so tampering
# across a run's artefacts cannot be detected from this receipt. State that
# rather than implying a chain. Flip to True when the chain format lands.
CHAIN_ACTIVE = False

# Wording for every gap the receipt can report. Named constants so a test can
# assert on the exact phrase rather than on incidental markup.
GAP = "not emitted"
UNMEASURED = "not measured"
UNSIGNED = "no digest recorded - this artefact is unsigned"
TAMPERED = "recorded digest does not match the artefact body"
RATIONALE_GAP = "no rationale recorded"
NO_LOCATIONS = "no locations recorded"
NO_POLICY = "no attestor policy recorded"
UNWEIGHTED = "unweighted - no decay curve applied"
PROVISIONAL_NOTE = (
    "Evidence tier semantics are proposed, not ratified. The source names the "
    "E0-E6 ladder but never defines the tiers, so a tier shown here is a "
    "label, not a certified level of evidence."
)
CHAIN_NOTE = (
    "Single-artefact digest only. No cross-file hash chain is active, so "
    "tampering across a run's artefacts cannot be detected from this receipt."
)

_CSS = """
:root { color-scheme: light; }
body { font: 14px/1.5 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
       color: #16181d; background: #fff; margin: 0; padding: 32px; }
main { max-width: 60rem; margin: 0 auto; }
h1 { font-size: 1.4rem; margin: 0 0 4px; }
h2 { font-size: 1rem; margin: 0 0 8px; text-transform: uppercase;
     letter-spacing: .08em; color: #444c57; }
section { border-top: 1px solid #d7dbe0; padding: 16px 0; }
table { border-collapse: collapse; width: 100%; margin: 4px 0; }
th, td { border: 1px solid #d7dbe0; padding: 5px 8px; text-align: left;
         vertical-align: top; }
th { background: #f4f6f8; font-weight: 600; }
.sub { color: #57606a; margin: 0 0 12px; }
dl { display: grid; grid-template-columns: max-content 1fr; gap: 2px 14px;
     margin: 0; }
dt { color: #57606a; }
dd { margin: 0; overflow-wrap: anywhere; }
.gap { color: #8a5a00; font-style: italic; }
.ok { color: #1a5e28; font-weight: 600; }
.bad { color: #a01b1b; font-weight: 600; }
.provisional { border: 1px solid #c9a227; background: #fdf8e6;
               padding: 8px 10px; margin: 8px 0; }
ul { margin: 4px 0; padding-left: 20px; }
@media print { body { padding: 0; } section { break-inside: avoid; } }
"""


# --- integrity ---------------------------------------------------------------

def canonical_digest(artifact: dict) -> str:
    """Digest of the artefact body with the stored digest removed.

    Mirrors write_artifact: the digest covers the payload, and is then stored
    alongside it. Verifying therefore means re-hashing with the stored digest
    excluded - hashing the envelope including its own digest is circular.
    """
    body = {k: v for k, v in artifact.items() if k != "sha256"}
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()


def digest_state(artifact: dict) -> str:
    """``verified``, ``mismatch`` or ``absent`` - never asserted."""
    recorded = artifact.get("sha256")
    if not recorded:
        return "absent"
    return "verified" if recorded == canonical_digest(artifact) else "mismatch"


def is_signed(artifact: dict) -> bool:
    """Signed means the digest verifies against the body, nothing else."""
    return digest_state(artifact) == "verified"


# --- gap predicates ----------------------------------------------------------

def missing_artefacts(artifact: dict) -> list[str]:
    """Absent artefacts named, so a gap reads as a gap and not as emptiness."""
    return [name for name in DATA_ARTEFACTS if not artifact.get(name)]


def exposure_measured(exposure: Any) -> bool:
    """A pre-measurement state must not render as a number."""
    if not isinstance(exposure, dict):
        return False
    return bool(exposure.get("measured")) and exposure.get(
        "false_certified_rate"
    ) is not None


def debt_entries(artifact: dict) -> list[dict]:
    """Ledger entries that record unproven remainder, per verdict semantics."""
    verdicts = _verdict_items(artifact)
    conditional = [v for v in verdicts if v.get("verdict") == "CONDITIONAL"]
    ledger = artifact.get("ledger")
    if isinstance(ledger, list) and ledger:
        return [e for e in ledger if isinstance(e, dict)]
    if isinstance(ledger, dict) and ledger:
        return [ledger]
    return [{"criterion_id": v.get("criterion_id", ""),
             "debt": RATIONALE_GAP} for v in conditional]


def _verdict_items(artifact: dict) -> list[dict]:
    items = artifact.get("verdicts")
    if not isinstance(items, list):
        return []
    return [i for i in items if isinstance(i, dict)]


def _esc(value: Any) -> str:
    """Escape every value that reaches the document.

    Locations and rationales are file paths and prose from the change under
    review, so they are untrusted text, not markup.
    """
    return html.escape(str(value), quote=True)


def _span(text: str) -> str:
    return f'<span class="gap">{_esc(text)}</span>'


def _open(inner: str) -> str:
    return f'<section><h2>{_esc(inner)}</h2>'


# --- sections ----------------------------------------------------------------

def _header(artifact: dict) -> str:
    run_id = artifact.get("run_id", "unknown run")
    rows = [
        ("run id", _esc(artifact.get("run_id", GAP))),
        ("status", _esc(artifact.get("status", GAP))),
        ("verdict", _esc(artifact.get("verdict", GAP))),
        ("exit code", _esc(artifact.get("exit_code", GAP))),
        ("metrics measured", _esc(artifact.get("measured", GAP))),
    ]
    body = "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in rows)
    return (
        f"<h1>Attestation receipt - {_esc(run_id)}</h1>"
        '<p class="sub">Rendering of the signed run artefact. The artefact is '
        "the record; this document is a rendering of it and carries no "
        "authority of its own.</p>"
        f"{_open('Run')}<dl>{body}</dl></section>"
    )


def _summary(artifact: dict) -> str:
    items = _verdict_items(artifact)
    counts = {v: 0 for v in VERDICTS}
    tiers = {t: 0 for t in TIERS}
    for item in items:
        verdict = item.get("verdict")
        tier = item.get("evidence_tier")
        if verdict in counts:
            counts[verdict] += 1
        if tier in tiers:
            tiers[tier] += 1

    verdict_rows = "".join(
        f"<tr><td>{_esc(v)}</td><td>{counts[v]}</td></tr>" for v in VERDICTS
    )
    tier_rows = "".join(
        f"<tr><td>{_esc(t)}</td><td>{tiers[t]}</td></tr>" for t in TIERS
    )

    banner = ""
    if LADDER_PROVISIONAL:
        banner = f'<p class="provisional">{_esc(PROVISIONAL_NOTE)}</p>'

    unexamined = counts["PENDING"]
    if unexamined:
        banner += (
            f'<p class="provisional">{unexamined} of {len(items)} criteria are '
            f"PENDING - undecided, not passing. {_esc(GAP)} is reported "
            "explicitly; a criterion with no evidence is never certified.</p>"
        )

    return (
        f"{_open('Summary')}"
        f"<table><thead><tr><th>verdict</th><th>criteria</th></tr></thead>"
        f"<tbody>{verdict_rows}</tbody></table>"
        f"<table><thead><tr><th>evidence tier</th><th>criteria</th></tr></thead>"
        f"<tbody>{tier_rows}</tbody></table>"
        f"{banner}</section>"
    )


def _verdicts(artifact: dict) -> str:
    items = _verdict_items(artifact)
    if not items:
        return (
            f"{_open('Per-criterion verdicts')}"
            f"<p>{_span(GAP)}</p></section>"
        )
    rows = []
    for item in items:
        locations = item.get("locations") or []
        loc_cell = (
            _esc(", ".join(str(x) for x in locations))
            if locations
            else _span(NO_LOCATIONS)
        )
        rationale = item.get("rationale") or ""
        rationale_cell = _esc(rationale) if rationale else _span(RATIONALE_GAP)
        verdict = item.get("verdict", GAP)
        rows.append(
            "<tr>"
            f"<td>{_esc(item.get('criterion_id', GAP))}</td>"
            f'<td class="{_verdict_class(verdict)}">{_esc(verdict)}</td>'
            f"<td>{_esc(item.get('evidence_tier', GAP))}</td>"
            f"<td>{loc_cell}</td>"
            f"<td>{rationale_cell}</td>"
            "</tr>"
        )
    return (
        f"{_open('Per-criterion verdicts')}"
        "<table><thead><tr><th>criterion</th><th>verdict</th><th>tier</th>"
        f"<th>locations</th><th>rationale</th></tr></thead><tbody>"
        f"{''.join(rows)}</tbody></table></section>"
    )


def _verdict_class(verdict: Any) -> str:
    """PENDING must never be styled like a decision."""
    if verdict == "CERTIFIED":
        return "ok"
    if verdict == "REJECTED":
        return "bad"
    if verdict == "PENDING":
        return "gap"
    return ""


def _traceability(artifact: dict) -> str:
    matrix = artifact.get("traceability")
    links = matrix.get("links") if isinstance(matrix, dict) else None
    if not isinstance(links, list) or not links:
        return f"{_open('Traceability matrix')}<p>{_span(GAP)}</p></section>"
    rows = []
    for link in links:
        if not isinstance(link, dict):
            continue
        locations = link.get("locations") or []
        # Escape each location, then join — escaping the joined string would
        # escape the <br> separators too.
        loc_cell = (
            "<br>".join(_esc(x) for x in locations)
            if locations
            else _span(NO_LOCATIONS)
        )
        rows.append(
            "<tr>"
            f"<td>{_esc(link.get('criterion_id', GAP))}</td>"
            f"<td>{_esc(link.get('evidence_tier', GAP))}</td>"
            f"<td>{loc_cell}</td>"
            "</tr>"
        )
    return (
        f"{_open('Traceability matrix')}"
        "<table><thead><tr><th>criterion</th><th>tier</th>"
        f"<th>locations</th></tr></thead><tbody>{''.join(rows)}</tbody>"
        "</table></section>"
    )


def _ledger(artifact: dict) -> str:
    entries = debt_entries(artifact)
    if not entries:
        return f"{_open('Review-debt ledger')}<p>{_span(GAP)}</p></section>"
    blocks = []
    for entry in entries:
        fields = "".join(
            f"<dt>{_esc(k)}</dt><dd>{_esc(entry[k])}</dd>" for k in sorted(entry)
        )
        blocks.append(f"<ul><li><dl>{fields}</dl></li></ul>")
    note = (
        "<p class=\"sub\">Unproven remainder recorded against this run. A "
        "conditional verdict without an entry here is a contract violation.</p>"
    )
    return (
        f"{_open('Review-debt ledger')}{note}{''.join(blocks)}</section>"
    )


def _exposure(artifact: dict) -> str:
    exposure = artifact.get("exposure")
    if not isinstance(exposure, dict) or not exposure:
        return f"{_open('Risk-weighted exposure')}<p>{_span(GAP)}</p></section>"

    measured = exposure_measured(exposure)
    if measured:
        headline = (
            "P(CERTIFIED | a spec violation was present) = "
            f"{_esc(exposure['false_certified_rate'])}"
        )
    else:
        headline = _span(UNMEASURED)

    rows = [
        ("false certified rate", headline),
        ("measurement state", "measured" if measured else _span(UNMEASURED)),
    ]

    weighted = exposure.get("weighted")
    if not weighted:
        rows.append(("weighting", _esc(UNWEIGHTED)))

    by_operator = exposure.get("by_operator")
    if isinstance(by_operator, dict) and by_operator:
        rows.append(("operator classes", _esc(len(by_operator))))

    fields = "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in rows)
    # Only claim the rate is withheld when it actually is — the note must never
    # contradict the measurement state printed above it.
    if measured:
        note = '<p class="sub">Low is good.</p>'
    else:
        note = (
            '<p class="sub">Low is good. Until a mutation run populates this, '
            f"the rate is {_esc(UNMEASURED)} and is not shown as a number.</p>"
        )

    table = ""
    if isinstance(by_operator, dict) and by_operator:
        op_rows = []
        for op in sorted(by_operator):
            entry = by_operator[op]
            if not isinstance(entry, dict):
                continue
            op_rows.append(
                f"<tr><td>{_esc(op)}</td>"
                f"<td>{_esc(entry.get('certified', GAP))}</td>"
                f"<td>{_esc(entry.get('total', GAP))}</td></tr>"
            )
        if op_rows:
            table = (
                "<table><thead><tr><th>operator</th><th>certified</th>"
                f"<th>total</th></tr></thead><tbody>{''.join(op_rows)}"
                "</tbody></table>"
            )

    return (
        f"{_open('Risk-weighted exposure')}{note}<dl>{fields}</dl>{table}"
        "</section>"
    )


def _integrity(artifact: dict) -> str:
    state = digest_state(artifact)
    if state == "verified":
        digest_cell = f'<span class="ok">verified</span> {_esc(canonical_digest(artifact))}'
    elif state == "mismatch":
        digest_cell = (
            f'<span class="bad">mismatch</span> {_esc(TAMPERED)} - recorded '
            f"{_esc(artifact.get('sha256'))}, recomputed "
            f"{_esc(canonical_digest(artifact))}"
        )
    else:
        digest_cell = f'<span class="gap">unsigned</span> {_esc(UNSIGNED)}'

    chain_cell = (
        "cross-file chain active"
        if CHAIN_ACTIVE
        else _esc(CHAIN_NOTE)
    )

    policy = artifact.get("policy") or artifact.get("capabilities")
    if isinstance(policy, (list, tuple, set)) and policy:
        policy_cell = _esc(", ".join(sorted(str(p) for p in policy)))
    elif isinstance(policy, dict) and policy:
        policy_cell = _esc(", ".join(f"{k}={policy[k]}" for k in sorted(policy)))
    else:
        policy_cell = _span(NO_POLICY)

    rows = [
        ("artefact digest", digest_cell),
        ("chain state", chain_cell),
        ("attestor policy", policy_cell),
        ("renderer", "receipt renderer - deterministic, offline, no network"),
    ]
    body = "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in rows)
    absent = missing_artefacts(artifact)
    if absent:
        body += (
            f"<dt>artefacts absent</dt><dd>{_span(', '.join(absent))}</dd>"
        )
    return f"{_open('Integrity')}<dl>{body}</dl></section>"


# --- document ----------------------------------------------------------------

def render(artifact: dict) -> str:
    """Render a run artefact as a self-contained, printable receipt.

    Pure: performs no I/O, reads no clock, and depends on no external
    resource. The output carries inline styles and no scripts, so it renders
    identically offline and in twenty years.
    """
    if not isinstance(artifact, dict):
        artifact = {}
    sections = "".join(
        [
            _header(artifact),
            _summary(artifact),
            _verdicts(artifact),
            _traceability(artifact),
            _ledger(artifact),
            _exposure(artifact),
            _integrity(artifact),
        ]
    )
    return (
        "<!doctype html>\n"
        '<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>Attestation receipt</title>\n"
        f"<style>{_CSS}</style>\n</head>\n<body>\n<main>\n{sections}\n</main>\n"
        "</body>\n</html>\n"
    )
