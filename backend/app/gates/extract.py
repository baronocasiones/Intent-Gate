"""Stage 2 — Extract criteria: atomic acceptance criteria, ISO 29148 quality gate.

Deterministic by spec (R4 thin slice): split `requirement` on `AC-n:` markers,
quality-gate each candidate, emit `criteria[]` plus an auditable `rejected[]`.
No model is called here and none may be — see
`test_extract_imports_nothing_from_the_llm_package`. (The brief's MOCK_LLM
fixture-criteria AC is superseded: with no LLM in this stage both modes behave
identically, so there is no switch to guard — the no-import test is the
consumer control §11 gap 9 asks M5 for.)

Threading (§1.8.3 custody): `files` and `workspace` pass through verbatim. The
pipeline threads each stage's output verbatim into the next stage's input, so a
key dropped here is unrecoverable downstream — M6 needs both to re-verify M4's
hashes, and nothing downstream re-attaches them.
"""
import re

# `AC-n:` markers, in order. The lookahead stops each candidate's text at the
# next marker or end of input; DOTALL lets one criterion span lines.
_AC = re.compile(r"AC-(\d+)\s*:\s*(.*?)(?=\s*AC-\d+\s*:|\s*$)", re.DOTALL)

# Deterministic vagueness filter — the ISO 29148 gate, not a certification claim.
# A qualifier with no measurable threshold makes the criterion unverifiable as
# written. Deliberately short: common performance words ("fast", "reliable")
# appear in legitimate criteria, so only qualifiers that are *never* measurable
# as written are listed. A term added here must gain a test in the same change.
_VAGUE = (
    "user-friendly",
    "intuitive",
    "seamless",
    "robust",
    "scalable",
    "easy to use",
)


def _split_candidates(requirement: str) -> list[tuple[str, str]]:
    """`(criterion_id, text)` in marker order. Ids are the marker's own number
    (`AC-7` stays `AC-7`), so they are stable across reruns by construction."""
    return [(f"AC-{int(n)}", text.strip()) for n, text in _AC.findall(requirement)]


def _is_compound(text: str) -> bool:
    """Two non-trivial clauses joined by " and " is two criteria, not one
    ("Refunds work and are fast"). Each side needs ≥2 words so "terms and
    conditions" does not false-positive."""
    parts = re.split(r"\s+and\s+", text, flags=re.IGNORECASE)
    return len(parts) > 1 and all(len(p.split()) >= 2 for p in parts)


def _gate(cid: str, text: str, seen: set[str]) -> tuple[dict | None, dict | None]:
    """Returns `(criterion, rejection)` — exactly one of them is not None."""
    if not text:
        return None, {"text": f"{cid}:", "reason": "empty criterion text"}
    if cid in seen:
        return None, {"text": text, "reason": f"duplicate criterion_id {cid}"}
    if _is_compound(text):
        return None, {
            "text": text,
            "reason": "compound criterion — split into one verifiable claim each",
        }
    lowered = text.lower()
    for term in _VAGUE:
        if term in lowered:
            return None, {
                "text": text,
                "reason": f"unverifiable qualifier {term!r} has no measurable threshold",
            }
    return {"criterion_id": cid, "text": text, "testable": True}, None


def run(bundle: dict) -> dict:
    bundle = bundle if isinstance(bundle, dict) else {}
    requirement = bundle.get("requirement", "")
    if not isinstance(requirement, str):
        requirement = ""
    files = bundle.get("files", [])
    if not isinstance(files, list):
        files = []
    workspace = bundle.get("workspace", "")
    if not isinstance(workspace, str):
        workspace = ""

    criteria: list[dict] = []
    rejected: list[dict] = []
    seen: set[str] = set()
    for cid, text in _split_candidates(requirement):
        criterion, rejection = _gate(cid, text, seen)
        seen.add(cid)
        if criterion is not None:
            criteria.append(criterion)
        else:
            rejected.append(rejection)
    return {
        "stage": "extract",
        "ok": True,
        "criteria": criteria,
        "rejected": rejected,
        "files": files,
        "workspace": workspace,
    }
