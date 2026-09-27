"""Stage 3 — Deterministic parse: criterion-anchored AST. No model in this loop.

R4 pass-through (M6-real is out of scope this build): thread `criteria`,
`files` and `workspace` forward per the §1.8.3 chain of custody, and anchor one
`ast[]` entry per criterion with `kind: "unresolved"` — an honest marker that
no parse ran, not a fabricated location. M6-real replaces the kind/node while
keeping every key (rule 3).
"""


def run(extract_out: dict) -> dict:
    d = extract_out if isinstance(extract_out, dict) else {}
    criteria = d.get("criteria", [])
    if not isinstance(criteria, list):
        criteria = []
    files = d.get("files", [])
    if not isinstance(files, list):
        files = []
    workspace = d.get("workspace", "")
    if not isinstance(workspace, str):
        workspace = ""
    ast = [
        {"criterion_id": c["criterion_id"], "kind": "unresolved", "node": ""}
        for c in criteria
        if isinstance(c, dict) and c.get("criterion_id")
    ]
    return {
        "stage": "parse",
        "ok": True,
        "ast": ast,
        "criteria": criteria,
        "files": files,
        "workspace": workspace,
    }
