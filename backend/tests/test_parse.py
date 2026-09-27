"""M6 — Stage 3 Deterministic parse, R4 pass-through (no real parse this build).

Per-stage shape file per the M4 restructure. Pinned here: criterion-anchored
`ast[]` with honest `unresolved` kinds, custody threading (§1.8.3), and the
headline control — no model in this loop, asserted from source (M6 AC).
"""
import ast as _ast
from pathlib import Path

from app.gates import parse

PARSE_SOURCE = Path(__file__).resolve().parents[1] / "app" / "gates" / "parse.py"


def test_parse_anchors_one_unresolved_entry_per_criterion():
    out = parse.run(
        {
            "stage": "extract",
            "ok": True,
            "criteria": [
                {"criterion_id": "AC-1", "text": "a.", "testable": True},
                {"criterion_id": "AC-2", "text": "b.", "testable": True},
            ],
        }
    )
    assert out["stage"] == "parse"
    assert out["ok"] is True
    assert out["ast"] == [
        {"criterion_id": "AC-1", "kind": "unresolved", "node": ""},
        {"criterion_id": "AC-2", "kind": "unresolved", "node": ""},
    ]


def test_parse_threads_criteria_files_and_workspace():
    """§1.8.3: M7's dict is the only carrier M8 reads, so `criteria` must
    survive M6; `files`/`workspace` survive for M6-real's hash re-verification."""
    files = [{"path": "src/refund.py", "sha256": "ab" * 32}]
    out = parse.run(
        {"stage": "extract", "ok": True, "criteria": [], "files": files, "workspace": "/w"}
    )
    assert out["criteria"] == []
    assert out["files"] == files
    assert out["workspace"] == "/w"


def test_parse_tolerates_a_bare_dict():
    out = parse.run({})
    assert out["ast"] == []
    assert out["criteria"] == []


def test_parse_imports_no_llm_client():
    """M6 AC, guarding a pitch claim ("no model in this loop") — same AST
    technique as M4/M5: docstrings cannot trip it, any genuine import can."""
    tree = _ast.parse(PARSE_SOURCE.read_text(encoding="utf-8"))
    imported = set()
    for node in _ast.walk(tree):
        if isinstance(node, _ast.Import):
            imported.update(a.asname or a.name for a in node.names)
        elif isinstance(node, _ast.ImportFrom):
            imported.add(node.module or "")
    assert not any(
        name == "app.llm" or name.startswith("app.llm.") or name == "llm"
        for name in imported
    ), imported
