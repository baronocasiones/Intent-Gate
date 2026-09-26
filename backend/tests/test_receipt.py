"""Receipt renderer — the artefact is the record, the receipt only reports it.

Guards the two invariants the module rests on (determinism, digest-preserving)
and the six honesty rules. Each honesty rule is asserted against the exact
wording the renderer is required to produce, not against incidental markup, so
a reworded document does not fail the suite and a *removed* claim does.

Zero live calls: the same send() spy as test_llm.py, plus an ast walk proving
the package never imports the llm layer. Everything writes to tmp_path — never
the repo working tree (the pre-commit cleanliness gate depends on this).
"""
import ast
import hashlib
import json
from pathlib import Path

import httpx
import pytest

import app.receipt.store as receipt_store
import app.store.artifacts as artifacts
from app.receipt.render import (
    GAP,
    NO_POLICY,
    RATIONALE_GAP,
    TAMPERED,
    UNMEASURED,
    UNSIGNED,
    canonical_digest,
    debt_entries,
    digest_state,
    exposure_measured,
    is_signed,
    missing_artefacts,
    render,
)

RECEIPT_DIR = Path(__file__).resolve().parents[1] / "app" / "receipt"


def _artefact() -> dict:
    """A non-stub run: mixed verdicts, real locations, tiers above E0.

    Deliberately not a demo stub — a receipt proved only against empty
    PENDING/E0 data proves it can render emptiness.
    """
    return {
        "run_id": "run-1a2b3c4d",
        "status": "rejected",
        "verdict": "REJECTED",
        "exit_code": 1,
        "measured": False,
        "verdicts": [
            {
                "criterion_id": "AC-1",
                "verdict": "CERTIFIED",
                "evidence_tier": "E4",
                "locations": ["src/refund.py:42"],
                "rationale": "supervisor approval enforced above the 100 boundary",
            },
            {
                "criterion_id": "AC-2",
                "verdict": "REJECTED",
                "evidence_tier": "E2",
                "locations": ["src/refund.py:88"],
                "rationale": "no retry path exists on the failure branch",
            },
        ],
        "traceability": {
            "run_id": "run-1a2b3c4d",
            "links": [
                {
                    "criterion_id": "AC-1",
                    "locations": ["src/refund.py:42"],
                    "evidence_tier": "E4",
                },
                {
                    "criterion_id": "AC-2",
                    "locations": ["src/refund.py:88"],
                    "evidence_tier": "E2",
                },
            ],
        },
        "ledger": [
            {"criterion_id": "AC-2", "debt": "retry path unproven", "owner": "payments"},
        ],
        "exposure": {
            "false_certified_rate": 0.25,
            "measured": True,
            "by_operator": {
                "boundary_drop": {"certified": 1, "total": 2},
                "comparison_inversion": {"certified": 0, "total": 1},
            },
        },
        "policy": ["read", "skill", "subagent", "workflow"],
    }


def _unmeasured_artefact() -> dict:
    """Pre-measurement state — the case that must never render as a number."""
    body = _artefact()
    body["exposure"] = {
        "false_certified_rate": None,
        "measured": False,
        "by_operator": {},
    }
    return body


def _content(out: str) -> str:
    """The document minus its stylesheet.

    Assertions about rendered content have to skip the CSS: a stylesheet
    legitimately contains `width: 100%`, and grepping the whole document for
    "0%" would collide with the renderer's own layout.
    """
    return out.split("</style>", 1)[-1]


# --- invariant 1: determinism ------------------------------------------------

def test_render_is_deterministic():
    """Same artefact in, byte-identical HTML out — no clock, no ordering."""
    assert render(_artefact()) == render(_artefact())


def test_render_does_not_depend_on_key_insertion_order():
    """Mirrors sort_keys=True in artifacts.py: ordering cannot move the bytes."""
    body = _artefact()
    reordered = dict(reversed(list(body.items())))
    assert render(reordered) == render(body)


def test_render_never_raises_on_a_malformed_artefact():
    """A receipt that crashes is worse than a receipt that reports a gap."""
    for junk in ({}, {"verdicts": "nope"}, {"verdicts": [1, 2]}, {"exposure": []}, None, []):
        assert render(junk).startswith("<!doctype html>")


# --- invariant 2: digest-preserving, never digest-computing ------------------

def test_receipt_reports_the_digest_write_artifact_stores(tmp_path, monkeypatch):
    """The round trip that matters: store a real artefact, read it back, and
    the receipt must print the digest write_artifact actually wrote."""
    monkeypatch.setattr(artifacts, "ARTIFACT_DIR", str(tmp_path))
    path = artifacts.write_artifact("run-1a2b3c4d", _artefact())
    stored = json.loads(Path(path).read_text())

    assert is_signed(stored)
    assert canonical_digest(stored) == stored["sha256"]
    assert stored["sha256"] in render(stored)


def test_canonical_digest_matches_the_write_artifact_computation():
    body = _artefact()
    expected = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
    assert canonical_digest(body) == expected


def test_receipt_does_not_hash_its_own_bytes():
    """Hashing the rendering would be circular, so it must never appear.

    The real property: the digest on the page is the artefact's, and the
    receipt's own bytes are nowhere in the document.
    """
    body = _artefact()
    signed = dict(body, sha256=canonical_digest(body))
    out = render(signed)
    assert signed["sha256"] in out
    assert hashlib.sha256(out.encode()).hexdigest() not in out


def test_unsigned_artefact_prints_no_signature_claim():
    body = _artefact()
    assert digest_state(body) == "absent"
    assert is_signed(body) is False
    out = render(body)
    assert UNSIGNED in out
    assert "sha256" not in out


def test_digest_mismatch_is_reported_not_hidden():
    body = _artefact()
    body["sha256"] = "0" * 64
    assert digest_state(body) == "mismatch"
    assert TAMPERED in render(body)


def test_tampered_body_fails_verification():
    """Flipping a verdict after signing must be detectable from the receipt."""
    body = _artefact()
    signed = dict(body, sha256=canonical_digest(body))
    assert is_signed(signed)
    tampered = dict(signed, status="certified")
    assert is_signed(tampered) is False
    assert digest_state(tampered) == "mismatch"
    assert TAMPERED in render(tampered)


# --- honesty rule: unmeasured never renders a number -------------------------

def test_unmeasured_exposure_never_renders_a_number():
    out = _content(render(_unmeasured_artefact()))
    assert UNMEASURED in out
    assert "0%" not in out


def test_measured_zero_rate_does_render_a_number():
    """Proves the guard is measured-aware, not simply suppressing every rate."""
    body = _artefact()
    body["exposure"] = {
        "false_certified_rate": 0.0,
        "measured": True,
        "by_operator": {},
    }
    assert exposure_measured(body["exposure"]) is True
    assert "= 0.0" in render(body)


def test_exposure_measured_requires_both_flag_and_value():
    assert exposure_measured({"measured": True, "false_certified_rate": None}) is False
    assert exposure_measured({"measured": False, "false_certified_rate": 0.0}) is False
    assert exposure_measured({"measured": True, "false_certified_rate": 0.1}) is True
    assert exposure_measured("not a dict") is False


def test_unweighted_exposure_is_labelled_unweighted():
    assert "unweighted" in render(_artefact())


# --- honesty rule: absent artefacts are named, not faked ---------------------

def test_missing_artefacts_are_named_not_faked():
    body = {"run_id": "r", "status": "pending", "verdicts": []}
    out = render(body)
    for name in ("traceability", "ledger", "exposure"):
        assert name in out
    assert missing_artefacts(body) == ["verdicts", "traceability", "ledger", "exposure"]
    assert out.count(GAP) >= 3


def test_complete_artefact_reports_nothing_absent():
    body = _artefact()
    assert missing_artefacts(body) == []
    assert "artefacts absent" not in render(body)


# --- honesty rule: PENDING is visibly undecided ------------------------------

def test_pending_is_styled_differently_from_certified():
    body = _artefact()
    body["verdicts"] = [
        {
            "criterion_id": "AC-1",
            "verdict": "CERTIFIED",
            "evidence_tier": "E4",
            "locations": ["a.py:1"],
            "rationale": "enforced",
        },
        {
            "criterion_id": "AC-3",
            "verdict": "PENDING",
            "evidence_tier": "E0",
            "locations": [],
            "rationale": "",
        },
    ]
    out = render(body)
    assert '<td class="ok">CERTIFIED</td>' in out
    assert '<td class="gap">PENDING</td>' in out
    assert "undecided, not passing" in out


def test_empty_rationale_renders_as_a_visible_gap():
    body = _artefact()
    body["verdicts"][0]["rationale"] = ""
    out = render(body)
    assert RATIONALE_GAP in out
    assert '<span class="gap">' in out


def test_conditional_criterion_implies_a_debt_entry():
    body = _artefact()
    del body["ledger"]
    body["verdicts"][0]["verdict"] = "CONDITIONAL"
    entries = debt_entries(body)
    assert entries[0]["criterion_id"] == "AC-1"


def test_explicit_ledger_wins_over_derived_entries():
    body = _artefact()
    body["verdicts"][0]["verdict"] = "CONDITIONAL"
    assert debt_entries(body) == [body["ledger"][0]]


# --- honesty rule: ladder and chain state are stated -------------------------

def test_ladder_renders_marked_provisional():
    out = render(_artefact())
    assert "provisional" in out
    assert "proposed, not ratified" in out


def test_chain_state_is_stated_plainly():
    assert "No cross-file hash chain is active" in render(_artefact())


def test_attestor_policy_is_visible_in_the_receipt():
    assert "read, skill, subagent, workflow" in render(_artefact())
    body = _artefact()
    del body["policy"]
    assert NO_POLICY in render(body)


# --- self-contained, offline -------------------------------------------------

def test_receipt_is_self_contained():
    """No network, ever: nothing to fetch, no script, styles inlined."""
    out = render(_artefact())
    assert "http://" not in out
    assert "https://" not in out
    assert "<script" not in out
    assert "<style>" in out
    assert "<!doctype html>" in out


def test_renderer_makes_no_network_call(monkeypatch):
    """Same send() spy as test_llm.py — assert send is never reached."""
    calls = {"send": 0}

    class _SpyClient:
        def __init__(self, *a, **kw):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

        async def send(self, *a, **kw):
            calls["send"] += 1
            raise AssertionError("network request attempted — receipt went online")

    monkeypatch.setattr(httpx, "AsyncClient", _SpyClient)
    render(_artefact())
    assert calls["send"] == 0


def test_receipt_package_never_reaches_the_llm_layer():
    """Rule 4: the receipt renders stored evidence, so no model is involved.

    Parsed rather than grepped — a docstring mentioning the model must not
    fail this, only an actual import of it.
    """
    offenders = []
    for path in sorted(RECEIPT_DIR.glob("*.py")):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.Import):
                offenders += [
                    f"{path.name}: import {a.name}"
                    for a in node.names
                    if "llm" in a.name or "watsonx" in a.name
                ]
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                offenders += [
                    f"{path.name}: from {mod} import {a.name}"
                    for a in node.names
                    if "llm" in mod or "watsonx" in mod
                    or "llm" in a.name or "watsonx" in a.name
                ]
    assert offenders == []


def test_rationale_is_escaped_not_interpreted():
    """Locations and rationales are untrusted text from the change under review."""
    body = _artefact()
    body["verdicts"][0]["rationale"] = "<script>alert(1)</script>"
    out = render(body)
    assert "<script>alert(1)</script>" not in out
    assert "&lt;script&gt;" in out


# --- receipt artefact on disk ------------------------------------------------

def test_write_receipt_lands_under_configured_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(receipt_store, "ARTIFACT_DIR", str(tmp_path))
    path = receipt_store.write_receipt("run-1a2b3c4d", _artefact())
    assert Path(path).name == "run-1a2b3c4d.receipt.html"
    assert Path(path).parent == tmp_path
    assert Path(path).read_text(encoding="utf-8") == render(_artefact())


def test_write_receipt_creates_missing_directories(tmp_path, monkeypatch):
    target = tmp_path / "nested" / "deep"
    monkeypatch.setattr(receipt_store, "ARTIFACT_DIR", str(target))
    path = receipt_store.write_receipt("run-9", _artefact())
    assert Path(path).exists()
    assert Path(path).parent == target


def test_write_receipt_renders_an_unsigned_artefact_honestly(tmp_path, monkeypatch):
    """A stub run must not produce a receipt that reads as a signed result."""
    monkeypatch.setattr(receipt_store, "ARTIFACT_DIR", str(tmp_path))
    path = receipt_store.write_receipt("demo", {"run_id": "demo", "verdicts": []})
    out = Path(path).read_text(encoding="utf-8")
    assert UNSIGNED in out
    assert out.count(GAP) >= 3


def test_receipt_and_artefact_coexist_in_the_same_dir(tmp_path, monkeypatch):
    """Both land under ARTIFACT_DIR; the JSON stays the signed record."""
    monkeypatch.setattr(artifacts, "ARTIFACT_DIR", str(tmp_path))
    monkeypatch.setattr(receipt_store, "ARTIFACT_DIR", str(tmp_path))
    body = _artefact()
    json_path = artifacts.write_artifact("run-7", body)
    html_path = receipt_store.write_receipt("run-7", body)

    assert Path(json_path).suffix == ".json"
    assert Path(html_path).suffix == ".html"
    assert Path(html_path).parent == Path(json_path).parent
    stored = json.loads(Path(json_path).read_text())
    assert is_signed(stored)
    assert stored["sha256"] in Path(html_path).read_text(encoding="utf-8")


def test_write_receipt_reports_the_stored_digest_not_the_argument(tmp_path, monkeypatch):
    """Regression: write_artifact then write_receipt with the same pre-digest
    payload used to render a receipt that said 'unsigned' for an artefact that
    was in fact signed on disk. The receipt must read the stored envelope."""
    monkeypatch.setattr(artifacts, "ARTIFACT_DIR", str(tmp_path))
    monkeypatch.setattr(receipt_store, "ARTIFACT_DIR", str(tmp_path))
    body = _artefact()
    artifacts.write_artifact("run-11", body)

    out = Path(receipt_store.write_receipt("run-11", body)).read_text(
        encoding="utf-8"
    )
    assert UNSIGNED not in out
    assert "verified" in out


def test_write_receipt_does_not_launder_a_tampered_artefact(tmp_path, monkeypatch):
    """The sharpest guard here. If write_receipt recomputed the digest instead
    of reading the stored one, an attacker who edits the JSON flips the status
    to 'certified', the recomputation matches, and the receipt certifies the
    tampering. It must report the mismatch instead."""
    monkeypatch.setattr(artifacts, "ARTIFACT_DIR", str(tmp_path))
    monkeypatch.setattr(receipt_store, "ARTIFACT_DIR", str(tmp_path))
    body = _artefact()
    json_path = artifacts.write_artifact("run-12", body)

    stored = json.loads(Path(json_path).read_text())
    stored["status"] = "certified"  # tamper after signing
    Path(json_path).write_text(json.dumps(stored, indent=2), encoding="utf-8")

    # Pass the ORIGINAL clean body as the argument — the tampered file wins,
    # because the receipt reports what is stored, not what it was handed.
    out = Path(receipt_store.write_receipt("run-12", body)).read_text(
        encoding="utf-8"
    )
    assert TAMPERED in out
    assert "certified" not in out.split("Integrity")[-1]


@pytest.mark.parametrize(
    "body",
    [
        {"verdicts": [{"verdict": "CONDITIONAL", "evidence_tier": "E2"}]},
        {"verdicts": [{"criterion_id": 7, "verdict": None, "locations": "x"}]},
        {"traceability": {"links": [{"locations": None}]}},
        {"ledger": "unexpectedly a string"},
        {"exposure": {"measured": True}},
    ],
)
def test_hostile_shapes_still_render(body):
    """Defensive render: a malformed artefact reports a gap, never a traceback."""
    assert render(body).startswith("<!doctype html>")
