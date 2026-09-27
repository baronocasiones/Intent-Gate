"""Stage gates — docs/architecture.md §3 rows 1-6: stub shapes + chain order.

Each gate is a fixture-shaped stub until the gate logic lands (§11.3). These
tests pin the *contract shape* so stubs can be replaced by real logic without
silently changing the interface the pipeline and frontend rely on.

**Flipped 2026-09-27 (M4 landed), deliberately, in M4's own change.** Five
exact-equality assertions here described the old three-key stubs and had to go as
each gate gained keys (AGENTS.md Convention 7). They are not simply relaxed —
per-stage shape is now owned by one test file per module, which is also what
§0.4's one-writer rule needs when four modules land at once:

    M4  -> test_ingest.py        M7a -> test_probes.py
    M5  -> (deferred)            M8  -> test_adjudicate.py
    M6  -> test_parse.py         M9  -> (deferred, contract-blocked)

What stays here is what no single stage owns: the six stage names and their
order, and the two envelope keys every stage must keep.
"""
from app.gates import adjudicate, emit, extract, ingest, parse, verify

GATE_ORDER = ("ingest", "extract", "parse", "verify", "adjudicate", "emit")

# The Stage 1 bundle, as of M4. Held here as well as in test_ingest.py because this
# is the *cross-module* view of the contract — §1.8.3's threading contract — and
# because it is the shape `pipeline.py` and everything downstream reads.
INGEST_BUNDLE_KEYS = {
    "stage",
    "ok",
    "input_keys",
    "requirement",
    "files",
    "workspace",
    "rejected_paths",
    "truncated",
}


def test_ingest_returns_sorted_input_keys():
    """Was `out == {"stage","ok","input_keys"}` — exact equality, deliberately dropped.

    It could not stay exact. M4's bundle carries `workspace`, the resolved absolute
    root, so an exact-equality assertion would have had to pin the *test runner's
    checkout path* into the test. Field-wise is the honest form: the keys are the
    contract, the values here are the stage's business.
    """
    out = ingest.run({"z": 1, "a": 2, "m": 3})
    assert out["stage"] == "ingest"
    assert out["ok"] is True
    assert out["input_keys"] == ["a", "m", "z"]
    assert set(out) == INGEST_BUNDLE_KEYS


def test_ingest_keeps_every_key_the_threading_contract_names():
    """§1.8.3. M6 consumes `workspace` and re-verifies `files[].sha256`; a stage that
    drops a key breaks a consumer that is not in this file and not in the stage's own
    tests."""
    out = ingest.run({"requirement": "x", "diff_paths": []})
    for key in ("workspace", "files", "requirement", "input_keys"):
        assert key in out, key
    assert isinstance(out["files"], list)
    assert isinstance(out["requirement"], str)


def test_ingest_handles_empty_payload():
    out = ingest.run({})
    assert out["input_keys"] == []
    assert out["requirement"] == ""
    assert out["files"] == []


def test_extract_emits_criteria_and_rejected_channels():
    """Flipped 2026-09-27 (M5 landed): exact equality could not survive — M5
    threads `files`/`workspace` (§1.8.3) whose values vary. Per-stage behaviour
    is now owned by `test_extract.py`; what stays here is the cross-module
    shape every downstream stage reads."""
    out = extract.run({"stage": "ingest", "ok": True, "input_keys": []})
    assert out["stage"] == "extract"
    assert out["ok"] is True
    assert out["criteria"] == []
    assert out["rejected"] == []


def test_parse_threads_criteria_and_anchors_unresolved_ast():
    """Flipped 2026-09-27 (M6 pass-through): the old exact-equality stub is
    gone — M6 now threads custody keys and anchors one unresolved entry per
    criterion. Detail owned by `test_parse.py`; the cross-module keys stay
    here."""
    out = parse.run(
        {"stage": "extract", "ok": True, "criteria": [], "files": [], "workspace": ""}
    )
    assert out["stage"] == "parse"
    assert out["ok"] is True
    assert out["ast"] == []
    assert out["criteria"] == []


def test_verify_emits_mock_findings_and_threads_criteria():
    """Flipped 2026-09-27 (R4 M7 stub): mock-backed §1.7 findings with
    machine-readable provenance, criteria threaded for M8 (§1.8.3)."""
    out = verify.run({"stage": "parse", "ok": True, "ast": [], "criteria": []})
    assert out["stage"] == "verify"
    assert out["ok"] is True
    assert out["findings"] == []
    assert out["criteria"] == []
    assert out["mode"] == "mock"


def test_criteria_survive_the_chain_from_extract_to_verify():
    """§1.8.3 chain of custody, end to end: `criteria` threaded twice is what
    lets M8 enumerate a criterion M7's dict is the only carrier of. A stage
    that drops the key breaks a consumer two stages away — this test sits here
    (not in a per-stage file) because no single stage owns the custody."""
    bundle = {
        "stage": "ingest",
        "ok": True,
        "input_keys": [],
        "requirement": (
            "AC-1: refunds over $100 require supervisor approval. "
            "AC-2: refund failures must be retried 3 times."
        ),
        "files": [],
        "workspace": "",
    }
    ids = ["AC-1", "AC-2"]
    parsed = parse.run(extract.run(bundle))
    assert [c["criterion_id"] for c in parsed["criteria"]] == ids
    verified = verify.run(parsed)
    assert [c["criterion_id"] for c in verified["criteria"]] == ids
    assert {f["criterion_id"] for f in verified["findings"]} == set(ids)


def test_demo_chain_end_to_end_certified_and_rejected_exit_1():
    """R4 thin slice, whole spine (§1.7): requirement → criteria → mock
    findings → ladder → derived exit. AC-1 CERTIFIED@E4, AC-2 REJECTED@E2,
    run REJECTED, exit 1. Manual chain (not `run_pipeline` — the orchestrator
    file is M10's; Cody owns the pipeline-level test)."""
    bundle = {
        "stage": "ingest",
        "ok": True,
        "input_keys": ["action", "diff_paths", "pr", "requirement"],
        "requirement": (
            "AC-1: refunds over $100 require supervisor approval. "
            "AC-2: refund failures must be retried 3 times."
        ),
        "files": [],
        "workspace": "",
    }
    emitted = emit.run(adjudicate.run(verify.run(parse.run(extract.run(bundle)))))
    assert emitted["exit_code"] == 1
    # flat run record (Session 25 seam fix — M14/M15/contract read it at top level)
    record = emitted
    assert record["verdict"] == "REJECTED"
    assert record["status"] == "rejected"
    by_id = {v["criterion_id"]: v for v in record["verdicts"]}
    assert by_id["AC-1"]["verdict"] == "CERTIFIED"
    assert by_id["AC-1"]["evidence_tier"] == "E4"
    assert by_id["AC-2"]["verdict"] == "REJECTED"
    assert by_id["AC-2"]["evidence_tier"] == "E2"
    links = {l["criterion_id"]: l for l in record["traceability"]["links"]}
    assert links["AC-1"]["locations"] == ["src/refund.py:64"]
    assert links["AC-2"]["locations"] == ["src/refund.py:88"]


def test_adjudicate_pending_without_findings():
    """Flipped 2026-09-27 (M8 landed): the old exact-equality stub is gone —
    M8 now emits `verdicts[]` + threaded `criteria`. What stays here is the
    fail-closed default the chain depends on; the ladder lives in
    `test_adjudicate.py`."""
    out = adjudicate.run({"stage": "verify", "ok": True, "findings": []})
    assert out["stage"] == "adjudicate"
    assert out["ok"] is True
    assert out["verdict"] == "PENDING"
    assert out["verdicts"] == []


def test_emit_blocks_by_default():
    """Non-zero exit blocks the merge — the safe default for a gate (§4.4).

    Still true after M9 landed (Session 25): `exit_code` is derived, and the
    derivation keeps 1 for every non-CERTIFIED path. Derivation cases live in
    `test_emit.py`; what stays here is the default plus the record echo."""
    out = emit.run({"stage": "adjudicate", "ok": True, "verdict": "PENDING"})
    assert out["stage"] == "emit"
    assert out["ok"] is True
    assert out["exit_code"] == 1
    assert out["exit_code"] != 0
    # emit echoes the adjudicate verdict through untouched (the record is flat,
    # so `stage` is emit's own per the stage convention — Session 25 seam fix)
    assert out["verdict"] == "PENDING"
    assert out["status"] == "pending"


def test_every_stage_keeps_the_stage_and_ok_envelope():
    """Rule 3 / §0.3: `stage` and `ok` survive every stage, and `pipeline.py` reads
    them. Asserted across all six rather than per-stage so a new stage cannot opt out
    of the envelope by being added to a list someone forgot to extend."""
    for module in (ingest, extract, parse, verify, adjudicate, emit):
        out = module.run({})
        assert out["stage"] in GATE_ORDER, module.__name__
        assert out["ok"] is True, module.__name__


def test_stage_names_follow_architecture_order():
    """The six gate modules must expose stages in the Figure-6 / §3 order.

    Also the reason every gate must tolerate a bare `{}`: this is a foreign empty dict,
    not any stage's real input shape. Surviving it without raising is fail-closed
    behaviour by construction — and it is why `enforce_worker_read_only` belongs at
    worker startup (D6) and never inside `verify.run()`, where an unset `ATTESTOR_CAPS`
    would raise `PermissionError` here, in CI.
    """
    stages = [
        ingest.run({})["stage"],
        extract.run({})["stage"],
        parse.run({})["stage"],
        verify.run({})["stage"],
        adjudicate.run({})["stage"],
        emit.run({})["stage"],
    ]
    assert stages == list(GATE_ORDER)
