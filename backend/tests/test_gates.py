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


def test_extract_stub_shape():
    out = extract.run({"stage": "ingest", "ok": True, "input_keys": []})
    assert out == {"stage": "extract", "ok": True, "criteria": []}


def test_parse_stub_shape():
    out = parse.run({"stage": "extract", "ok": True, "criteria": []})
    assert out == {"stage": "parse", "ok": True, "ast": []}


def test_verify_stub_shape():
    out = verify.run({"stage": "parse", "ok": True, "ast": []})
    assert out == {"stage": "verify", "ok": True, "findings": []}


def test_adjudicate_returns_pending_verdict():
    out = adjudicate.run({"stage": "verify", "ok": True, "findings": []})
    assert out == {"stage": "adjudicate", "ok": True, "verdict": "PENDING"}


def test_emit_blocks_by_default():
    """Non-zero exit blocks the merge — the safe default for a gate (§4.4)."""
    out = emit.run({"stage": "adjudicate", "ok": True, "verdict": "PENDING"})
    assert out["stage"] == "emit"
    assert out["ok"] is True
    assert out["exit_code"] == 1
    assert out["exit_code"] != 0
    # emit echoes the adjudicate record through untouched
    assert out["record"]["stage"] == "adjudicate"
    assert out["record"]["verdict"] == "PENDING"


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
