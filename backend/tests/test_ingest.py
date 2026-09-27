"""M4 Stage 1 Ingest — the bundle, and the path resolver that keeps it honest.

`docs/modules.md` §3 M4 asks for a deterministic `files[]` and a `sha256` that never
lies about having been measured. The second half is the whole reason this file is
mostly about refusals, because a payload arriving on `POST /webhooks/github` has no
signature check behind it (**D7** is undecided) and `diff_paths` is therefore
attacker-controlled text that this stage is about to `open()`.

So the tests are arranged around what the stage *refuses* and what it says when it
does. A resolver that returns the right path for a friendly input proves nothing; the
value is in `../`, an absolute path out of the tree, a symlink out of the tree, a FIFO
that would hang a naive `open()`, a file with no read bit, and a file too big to be
worth hashing. Each gets its own `note`, and one invariant test holds that every
`unreached` entry in a kitchen-sink payload has a non-empty reason and a `None` digest
— the defect this module exists to prevent is a `sha256: ""` that reads as a measurement.

Two environment hazards, both inherited from `test_policy.py` and handled the same way:
a `chmod 000` file is still readable as root, so the permission test skips with the
reason stated rather than failing in a way that looks like a product bug; and a
`chmod`-down file must be restored in a `finally` or `tmp_path` cleanup cannot unlink
it. Every path here is under `tmp_path` (test-suite.md Convention 3) — the repo tree
stays unpolluted, which the pre-commit cleanliness gate depends on.

The last test is the one worth reading first: M4 must import nothing from `app.llm`,
proven twice — statically from this module's own source, and dynamically in a
subprocess where importing the gate leaves `app.llm` out of `sys.modules` entirely.
The brief for M4 is explicit that a document path needing a model belongs to M5 behind
`MOCK_LLM`, and this stage is normalization; a stray import would be the first of the
several ways this codebase has of quietly acquiring a second model call site.
"""
import hashlib
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from app.gates import ingest
from app.gates.ingest import resolve_workspace_path

GATES_DIR = Path(__file__).resolve().parents[1] / "app" / "gates"
INGEST_SOURCE = GATES_DIR / "ingest.py"
# `backend/`, which is what the suite puts on `sys.path` via `backend/tests/__init__.py`.
BACKEND_DIR = GATES_DIR.parents[1]

# The cap as documented, written out here rather than imported. Importing
# `ingest.MAX_HASHABLE_BYTES` would make the size tests move with the constant, so
# raising it to 64 MiB would leave every one of them green — the same tautology M12 hit
# with `assert_read_only(GRANTS)`, where the assertion compared a constant to itself. A
# test that restates the number it expects is the only kind that can fail when the
# number changes.
DOCUMENTED_CAP = 2 * 1024 * 1024

# Root ignores the read bit, so a 0000 file is still readable and an unreadable-file
# expectation would fail for a reason that has nothing to do with the product. Stated
# rather than quietly passed.
IS_ROOT = hasattr(os, "geteuid") and os.geteuid() == 0
SKIP_AS_ROOT = pytest.mark.skipif(
    IS_ROOT,
    reason=(
        "running as root: the read bit is advisory, so a 0000 file opens anyway and "
        "the unreadable-path refusal has nothing honest to observe"
    ),
)


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    """A real workspace, wired in as the module's configured root.

    Patched on the consumer module rather than through `os.environ`, per test-suite.md
    Convention 2: `ingest.WORKSPACE_ROOT` is bound at import, so a `setenv` after
    import would be a no-op and the tests would quietly fingerprint the repo tree
    instead of the fixture.
    """
    root = tmp_path / "workspace"
    (root / "src").mkdir(parents=True)
    monkeypatch.setattr(ingest, "WORKSPACE_ROOT", str(root))
    return root


@pytest.fixture
def outside(tmp_path):
    """A file the workspace cannot reach. Lives beside the workspace, under the same
    `tmp_path`, so "outside" means outside the root and not merely somewhere odd."""
    victim = tmp_path / "outside" / "secret.txt"
    victim.parent.mkdir()
    victim.write_text("not yours\n", encoding="utf-8")
    return victim


def _bundle(workspace_root, **payload):
    """Run the stage against an explicit root and return just the `files` entry for
    one path, so each refusal test reads as one line of assertion."""
    files = _run(workspace_root, payload)["files"]
    return files[0]


def _run(workspace_root, payload):
    import app.gates.ingest as module

    original = module.WORKSPACE_ROOT
    module.WORKSPACE_ROOT = str(workspace_root)
    try:
        return module.run(payload)
    finally:
        module.WORKSPACE_ROOT = original


def _raise(exc):
    """A stand-in that raises, for exercising the belt at `_fingerprint`.

    The belt is unreachable from a payload — 0 hits across 60 000 hostile paths — so the
    only way to hold its output is to hand it an exception directly. That is the point:
    the belt is dead code, and dead code needs a test more than live code does.
    """
    def _raiser(*_args, **_kwargs):
        raise exc

    return _raiser


# --- the shape the §1.8.3 threading contract names ---------------------------------


def test_empty_payload_ingests_nothing():
    """The stage-order test calls all six gates with a bare `{}`, so this is the shape
    every stage has to survive: no keys, no requirement, no files, and a `workspace`
    that is still a string rather than an exception."""
    out = ingest.run({})
    assert out["stage"] == "ingest"
    assert out["input_keys"] == []
    assert out["requirement"] == ""
    assert out["files"] == []
    assert out["rejected_paths"] == []
    assert isinstance(out["workspace"], str) and out["workspace"]


def test_unrelated_payload_keys_do_not_raise_and_are_echoed():
    """A payload with no path list at all is the common case, not an error one."""
    out = ingest.run({"z": 1, "a": 2, "m": 3})
    assert out["input_keys"] == ["a", "m", "z"]
    assert out["files"] == []


def test_requirement_passes_through_unchanged():
    text = (
        "AC-1: refunds over $100 require supervisor approval. "
        "AC-2: refund failures must be retried 3 times."
    )
    assert ingest.run({"requirement": text})["requirement"] == text


def test_requirement_is_empty_when_absent():
    assert ingest.run({})["requirement"] == ""


def test_non_string_requirement_is_not_stringified(workspace):
    """A crafted body can put an object where the requirement belongs. `str()` of it
    would put an attacker-chosen rendering into the record that M5 would quote back as
    the requirement to verify, which is worse than admitting none arrived."""
    out = _run(workspace, {"requirement": {"text": ["AC-1: pay $1, refund $1000"]}})
    assert out["requirement"] == ""


def test_mixed_key_types_do_not_crash_the_sort():
    """`sorted()` alone raises `TypeError` on a dict with mixed key types, which an
    injected demo payload can carry. A stage that dies has certified nothing while
    looking as though it tried."""
    out = ingest.run({2: "b", "a": 1})
    assert out["input_keys"] == [2, "a"]
    assert ingest.run({"z": 1, "a": 2})["input_keys"] == ["a", "z"]


# --- files[]: deterministic, deduped, never invented -------------------------------


def test_files_are_sorted_and_deduped(workspace):
    """AC: `files[]` is derived deterministically from the payload's path list — sorted,
    deduped. Duplicates collapse rather than producing two entries claiming to be the
    same file, which would have M6 re-verify one digest against two entries."""
    (workspace / "src" / "refund.py").write_text("def refund():\n    pass\n", encoding="utf-8")
    out = _run(workspace, {"diff_paths": ["src/b.py", "src/refund.py", "src/b.py"]})
    assert [entry["path"] for entry in out["files"]] == ["src/b.py", "src/refund.py"]


def test_file_order_does_not_depend_on_payload_order(workspace):
    paths = ["src/z.py", "src/a.py", "src/m.py"]
    first = _run(workspace, {"diff_paths": paths})["files"]
    second = _run(workspace, {"diff_paths": list(reversed(paths))})["files"]
    assert first == second


def test_repeated_runs_are_identical(workspace):
    """No timestamps, no set iteration leaking into the output, no randomness. The same
    payload has to fingerprint the same way twice, or M6's re-verification is a coin
    flip."""
    (workspace / "src" / "refund.py").write_text("x = 1\n", encoding="utf-8")
    payload = {"diff_paths": ["src/refund.py", "src/refund.py", "nope.py"]}
    assert _run(workspace, payload) == _run(workspace, payload)


def test_absent_path_list_yields_no_files(workspace):
    for payload in ({}, {"diff_paths": []}, {"diff_paths": None}, {"files": ["src/refund.py"]}):
        assert _run(workspace, payload)["files"] == [], payload


def test_paths_are_stripped_but_not_respelled(workspace):
    """`path` is the payload's own identifier, whitespace aside. Re-spelling it would
    put a string in the record that nobody sent, and every later stage quotes this value
    back at the payload it came from."""
    (workspace / "src" / "refund.py").write_text("x = 1\n", encoding="utf-8")
    entry = _bundle(workspace, diff_paths=["  src/refund.py  "])
    assert entry["path"] == "src/refund.py"
    assert entry["status"] == "measured"


def test_a_path_that_normalises_back_inside_is_measured_and_echoed(workspace):
    """`..` that lands back inside the root is not an escape attempt, and the entry has
    to carry the path the payload sent rather than the tidier one. The tidier one is
    the trap: `os.path.normpath` would turn `src/../src/refund.py` into `src/refund.py`
    and the record would then claim the payload named a file it did not."""
    (workspace / "src" / "refund.py").write_text("x = 1\n", encoding="utf-8")
    entry = _bundle(workspace, diff_paths=["src/../src/refund.py"])
    assert entry["status"] == "measured"
    assert entry["sha256"] == hashlib.sha256(b"x = 1\n").hexdigest()
    assert entry["path"] == "src/../src/refund.py"
    assert os.path.normpath(entry["path"]) != entry["path"]


# --- sha256: measured, or visibly not ----------------------------------------------


def test_measured_entry_carries_the_digest_of_the_file_content(workspace):
    """The digest is checked against an independently computed one, not against "64
    characters" — a length assertion cannot tell the right hash from the right length."""
    content = b"def refund(amount):\n    return amount\n"
    (workspace / "src" / "refund.py").write_bytes(content)
    entry = _bundle(workspace, diff_paths=["src/refund.py"])
    assert entry["sha256"] == hashlib.sha256(content).hexdigest()
    assert entry["status"] == "measured"
    assert entry["note"] == ""


def test_measured_entry_reports_no_note(workspace):
    (workspace / "src" / "a.py").write_text("a = 1\n", encoding="utf-8")
    assert _bundle(workspace, diff_paths=["src/a.py"])["note"] == ""


def test_missing_path_is_unreached_and_says_so(workspace):
    entry = _bundle(workspace, diff_paths=["src/never_existed.py"])
    assert entry["status"] == "unreached"
    assert entry["sha256"] is None
    assert entry["note"].startswith("unstatable: ENOENT")


@pytest.mark.parametrize(
    "candidate",
    [
        "../outside/secret.txt",
        "../../etc/passwd",
        "src/../../outside/secret.txt",
        "./../outside/secret.txt",
    ],
)
def test_parent_traversal_out_of_the_root_is_refused(workspace, outside, candidate):
    """`..` in any spelling, including one that looks relative and normalises back
    inside, has to land outside the root and be refused there."""
    entry = _bundle(workspace, diff_paths=[candidate])
    assert entry["status"] == "unreached"
    assert entry["sha256"] is None
    assert entry["note"] == "escapes_workspace: resolves outside the workspace root"


def test_absolute_path_outside_the_root_is_refused(workspace, outside):
    """An absolute candidate is not sanitised by joining it to the root — `Path("/a") /
    "/etc/passwd"` is `/etc/passwd` — so the containment check is what stops it."""
    entry = _bundle(workspace, diff_paths=[str(outside)])
    assert entry["status"] == "unreached"
    assert entry["note"] == "escapes_workspace: resolves outside the workspace root"


def test_absolute_path_inside_the_root_is_measured(workspace):
    """The other side of that boundary, because a check that refuses everything would
    pass every refusal test above while being useless."""
    target = workspace / "src" / "refund.py"
    target.write_text("x = 1\n", encoding="utf-8")
    entry = _bundle(workspace, diff_paths=[str(target)])
    assert entry["status"] == "measured"
    assert entry["sha256"] == hashlib.sha256(b"x = 1\n").hexdigest()


def test_symlink_escaping_the_root_is_refused(workspace, outside):
    """Containment is decided on the resolved path, which is what a symlink defeats if
    you only normalise the string. The symlink sits *inside* the workspace and points
    out of it, which is the shape a compromised checkout would use."""
    (workspace / "innocent.py").symlink_to(outside)
    entry = _bundle(workspace, diff_paths=["innocent.py"])
    assert entry["status"] == "unreached"
    assert entry["note"] == "escapes_workspace: resolves outside the workspace root"


def test_symlinked_directory_escaping_the_root_is_refused(workspace, outside):
    (workspace / "pkg").symlink_to(outside.parent)
    entry = _bundle(workspace, diff_paths=["pkg/secret.txt"])
    assert entry["status"] == "unreached"
    assert entry["note"] == "escapes_workspace: resolves outside the workspace root"


def test_symlink_inside_the_root_is_measured(workspace):
    """A blanket ban on symlinks would be the easy way to pass the two tests above. It
    is also wrong: a symlink that resolves back inside the root is inside the root."""
    real = workspace / "src" / "refund.py"
    real.write_text("y = 2\n", encoding="utf-8")
    (workspace / "alias.py").symlink_to(real)
    entry = _bundle(workspace, diff_paths=["alias.py"])
    assert entry["status"] == "measured"
    assert entry["sha256"] == hashlib.sha256(b"y = 2\n").hexdigest()


def test_directory_is_unreached_and_named_as_one(workspace):
    entry = _bundle(workspace, diff_paths=["src"])
    assert entry["status"] == "unreached"
    assert entry["sha256"] is None
    assert entry["note"] == "not_a_regular_file: directory"


def test_fifo_is_refused_without_blocking(workspace):
    """A FIFO would make a naive `open()` hang forever, holding a run open with no
    verdict. The `stat` happens before the read for exactly this reason, so the test
    completes rather than hanging the suite."""
    os.mkfifo(workspace / "pipe")
    entry = _bundle(workspace, diff_paths=["pipe"])
    assert entry["status"] == "unreached"
    assert entry["note"] == "not_a_regular_file: fifo"


def test_broken_symlink_is_unreached(workspace):
    (workspace / "dangling.py").symlink_to(workspace / "gone.py")
    entry = _bundle(workspace, diff_paths=["dangling.py"])
    assert entry["status"] == "unreached"
    assert entry["sha256"] is None
    assert entry["note"].startswith("unstatable: ENOENT")


@SKIP_AS_ROOT
def test_unreadable_file_is_unreached_and_names_the_errno(workspace):
    """The mode is restored in a `finally` because `tmp_path` cleanup uses
    `shutil.rmtree` and an unlink inside a directory it may not write to errors the
    whole teardown — the same trap `test_policy.py` documents for a 0555 directory."""
    target = workspace / "src" / "secret.py"
    target.write_text("x = 1\n", encoding="utf-8")
    os.chmod(target, 0o000)
    try:
        entry = _bundle(workspace, diff_paths=["src/secret.py"])
    finally:
        os.chmod(target, 0o644)
    assert entry["status"] == "unreached"
    assert entry["sha256"] is None
    assert entry["note"] == "unreadable: EACCES"


def test_the_size_cap_is_the_documented_two_mib(workspace):
    """The number itself, pinned apart from the tests that exercise it. `ingest.py`'s
    comment argues for 2 MiB on the grounds that a diff carries source, specs and
    fixtures and nothing else; if the constant moves, this fails and the argument has
    to be made again rather than inherited."""
    assert ingest.MAX_HASHABLE_BYTES == DOCUMENTED_CAP


def test_oversized_file_is_refused(workspace):
    """Hashing a multi-gigabyte blob named by a `diff_paths` entry is a free denial of
    service, and the stage's whole output is a 64-character digest, so bytes past the
    cap buy nothing."""
    (workspace / "blob.bin").write_bytes(b"\0" * (DOCUMENTED_CAP + 1))
    entry = _bundle(workspace, diff_paths=["blob.bin"])
    assert entry["status"] == "unreached"
    assert entry["sha256"] is None
    assert entry["note"] == (
        f"too_large: {DOCUMENTED_CAP + 1} bytes past the {DOCUMENTED_CAP} byte cap"
    )


def test_file_exactly_at_the_cap_is_measured(workspace):
    """The boundary, so the cap is a documented threshold and not an off-by-one."""
    payload = b"\1" * DOCUMENTED_CAP
    (workspace / "exact.bin").write_bytes(payload)
    entry = _bundle(workspace, diff_paths=["exact.bin"])
    assert entry["status"] == "measured"
    assert entry["sha256"] == hashlib.sha256(payload).hexdigest()


def test_the_authoritative_fstat_catches_a_file_that_grew_after_approval(workspace):
    """The `fstat` size check, specifically — and it is not the same guard twice.

    `test_a_file_that_grew_before_the_read_is_refused_by_the_authoritative_fstat`
    grows the file *before* the call, so the resolver's own `stat` refuses it and the
    two size checks emit the **same message string**. That test therefore cannot tell
    which one fired, and a battery mutation that deleted the `fstat` check entirely
    survived the whole suite. This one grows the file *after* the resolver has
    approved it, so only a size check on the descriptor can catch it.
    """
    target = workspace / "grew.bin"
    target.write_bytes(b"\0" * 8)  # small: the resolver approves it
    approved, reason = ingest.resolve_workspace_path(str(workspace), "grew.bin")
    assert approved is not None and reason == "", (approved, reason)

    target.write_bytes(b"\2" * (DOCUMENTED_CAP + 1))  # grown, after approval

    digest, why = ingest._digest(approved)
    assert digest is None, (digest, why)
    assert why == f"too_large: {DOCUMENTED_CAP + 1} bytes past the {DOCUMENTED_CAP} byte cap"


def test_a_file_that_grew_before_the_read_is_refused(workspace):
    """The pre-call case, kept because it is the common one — and because it documents
    that the two size checks are indistinguishable by message alone (see above)."""
    grown = workspace / "grew.bin"
    grown.write_bytes(b"\2" * (DOCUMENTED_CAP + 1))
    entry = _bundle(workspace, diff_paths=["grew.bin"])
    assert entry["status"] == "unreached"
    assert entry["sha256"] is None
    assert entry["note"] == (
        f"too_large: {DOCUMENTED_CAP + 1} bytes past the {DOCUMENTED_CAP} byte cap"
    )


def test_the_read_loop_still_caps_a_file_that_grows_during_the_read(
    workspace, monkeypatch
):
    """Defence in depth against *concurrent* growth, which the `fstat` cannot catch.

    Reaches past `run()` on purpose, and simulates the race deterministically by
    reporting a small `st_size` from `os.fstat` while the file on disk is genuinely
    larger. Without this the in-loop cap is unreachable — the descriptor's size check
    always fires first — and an unreachable guard is not a guard, it is a comment that
    will be deleted by the next person who tidies up. A digest of the first 2 MiB of a
    3 MiB file is a real-looking 64 characters that certifies nothing, which is why the
    loop keeps its own cap rather than trusting the `fstat` it already did.
    """
    grown = workspace / "growing.bin"
    grown.write_bytes(b"\2" * (DOCUMENTED_CAP + 1))
    real_fstat = ingest.os.fstat

    def _underreporting_fstat(fd):
        info = real_fstat(fd)
        # Same object, smaller claim: exactly the shape of a file being appended to
        # between the `fstat` and the last `read`. Index 6 is `st_size` in the
        # `os.stat_result` sequence.
        return os.stat_result(
            (info.st_mode, info.st_ino, info.st_dev, 0, info.st_nlink, 0, 0, 0, 0, 0)
        )

    monkeypatch.setattr(ingest.os, "fstat", _underreporting_fstat)
    digest, reason = ingest._digest(str(grown))
    assert digest is None
    assert reason == f"too_large: read passed the {DOCUMENTED_CAP} byte cap"


# --- the caps: what a payload may not make this stage do ---------------------------
#
# Measured on 3.12.14 with every path absent (the cheapest possible attack — no file has
# to exist): 100 000 distinct paths in a 2.1 MB body cost 18.2 s of single-threaded CPU
# and produced a 10 MB record, a ~4.8x amplification, with no body-size limit anywhere in
# `backend/app`. The caps are what bound it; these tests are what hold the caps.
#
# `DOCUMENTED_*` restate the numbers rather than importing them, so raising a constant
# cannot drag its own test along with it. A battery caught exactly that: the size tests
# originally imported `MAX_HASHABLE_BYTES`, and moving it to 64 MiB left them green.

DOCUMENTED_PATH_CAP = 5_000
DOCUMENTED_REQUIREMENT_CAP = 64 * 1024
DOCUMENTED_KEY_CAP = 256


def test_the_caps_are_the_documented_values():
    """Pin the numbers, then let the behaviour tests use small ones.

    A battery caught the version of this that imported the constants: raising
    `MAX_HASHABLE_BYTES` to 64 MiB left every size test green, because the tests moved
    with the constant. So the *value* is asserted here against a literal in this file,
    and the tests below exercise behaviour with the module constant lowered to
    something a unit test can afford — 5 000 real `resolve()` calls cost more than the
    rest of the suite put together.
    """
    assert ingest.MAX_PATHS == DOCUMENTED_PATH_CAP
    assert ingest.MAX_REQUIREMENT_CHARS == DOCUMENTED_REQUIREMENT_CAP
    assert ingest.MAX_INPUT_KEYS == DOCUMENTED_KEY_CAP


def test_an_over_long_path_list_is_capped_and_the_cap_is_recorded(workspace, monkeypatch):
    """A cap recorded as a *rejection*, not as `unreached` — the distinction is the point.

    `unreached` says "we tried and could not". Marking a path unreached because it was
    never attempted would be a lie in the one field this module exists to keep honest.
    A rejection says "not attempted, and here is why", which is true — the same channel
    already used for a non-string entry.
    """
    monkeypatch.setattr(ingest, "MAX_PATHS", 10)
    payload = {"diff_paths": [f"src/f{i}.py" for i in range(35)]}
    out = _run(workspace, payload)
    assert len(out["files"]) == 10
    reasons = [r["reason"] for r in out["rejected_paths"]]
    assert any(r.startswith("over_path_cap:") for r in reasons), reasons
    # A capped path is *absent* from `files`, never present-and-unreached. This is the
    # assertion a mutation that appends the dropped paths as unreached would fail.
    assert len(out["files"]) + 25 == len(payload["diff_paths"])
    for entry in out["files"]:
        assert not entry["note"].startswith("over_path_cap"), entry


def test_a_path_list_at_the_cap_is_not_truncated(workspace, monkeypatch):
    monkeypatch.setattr(ingest, "MAX_PATHS", 10)
    out = _run(workspace, {"diff_paths": [f"src/f{i}.py" for i in range(10)]})
    assert len(out["files"]) == 10
    assert not [r for r in out["rejected_paths"] if "over_path_cap" in r["reason"]]


def test_an_over_long_requirement_is_truncated_and_the_truncation_is_recorded(
    workspace, monkeypatch
):
    """Truncate *and* say so. A run that verified the first N chars of a longer spec
    while the record shows only N is the same defect as an unreached entry for a path
    that was merely dropped."""
    monkeypatch.setattr(ingest, "MAX_REQUIREMENT_CHARS", 100)
    body = "A" * 250
    out = _run(workspace, {"requirement": body, "diff_paths": []})
    assert out["requirement"] == body[:100]
    assert any(t["field"] == "requirement" for t in out["truncated"]), out["truncated"]


def test_a_requirement_at_the_cap_is_untouched_and_untruncated(workspace, monkeypatch):
    monkeypatch.setattr(ingest, "MAX_REQUIREMENT_CHARS", 100)
    body = "A" * 100
    out = _run(workspace, {"requirement": body, "diff_paths": []})
    assert out["requirement"] == body
    assert out["truncated"] == []


def test_an_over_wide_key_set_is_capped_and_recorded(workspace, monkeypatch):
    monkeypatch.setattr(ingest, "MAX_INPUT_KEYS", 8)
    out = _run(workspace, {f"k{i}": i for i in range(20)})
    assert len(out["input_keys"]) == 8
    assert any(t["field"] == "input_keys" for t in out["truncated"]), out["truncated"]


def test_a_non_string_requirement_is_absent_and_never_stringified(workspace):
    """`str()` of a hostile object would put an attacker-chosen rendering into the
    record that M5 quotes back as the requirement to verify."""
    out = _run(workspace, {"requirement": {"a": 1}, "diff_paths": []})
    assert out["requirement"] == ""


def test_the_module_does_not_call_getcwd_when_the_root_is_configured():
    """`os.getenv(X, os.getcwd())` evaluates `getcwd()` before the call, so a process
    whose cwd was deleted crashed at *import* — taking `app.main` with it — even with
    `WORKSPACE_ROOT` set correctly. `or` short-circuits. Asserted in a subprocess with
    the cwd removed, because the defect is at import time and cannot be seen in-process.
    """
    gone = Path(os.environ.get("TMPDIR", "/tmp")) / "ingest-cwd-gone"
    gone.mkdir(parents=True, exist_ok=True)
    script = textwrap.dedent(
        f"""
        import os
        os.chdir({str(gone)!r})
        os.rmdir({str(gone)!r})
        os.environ["WORKSPACE_ROOT"] = {str(gone.parent)!r}
        import app.gates.ingest as m
        assert m.WORKSPACE_ROOT == {str(gone.parent)!r}, m.WORKSPACE_ROOT
        print("imported")
        """
    )
    proc = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).resolve().parents[1]),
        # `sys.path[0]` is '' for `-c`, which resolves against the *current* cwd — and
        # the script deletes that. So `app` has to be found by absolute path.
        env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1])},
    )
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    assert "imported" in proc.stdout


# --- the belt: the one place an internal bug becomes a false measurement -----------
#
# `_fingerprint` wraps the resolver in `except Exception`. It is the only construct in
# the module that can turn a mistake into a *reported measurement*, and it was entirely
# unguarded in both directions. A mutation battery found four that survived: make the
# belt re-raise (the stage then crashes on any surprise, which the module docstring
# says must never happen); blank the reason (an `unreached` entry with an empty `note`,
# "the place where an empty string would be worst"); set a fabricated 64-character
# digest (a **measured** entry with no file behind it); widen `_digest`'s except to
# `BaseException` (swallowing `KeyboardInterrupt`).
#
# `test_every_unreached_entry_names_a_reason` cannot see any of it, because the belt
# never fires on any constructable input — 0 hits across 60 000 random hostile paths and
# 169 structured combinations. The belt is dead code that was unverified dead code.


@pytest.mark.parametrize(
    "exc",
    [
        RuntimeError("boom"),
        KeyError("k"),
        AttributeError("a"),
        RecursionError("r"),
        NotImplementedError("n"),
        ValueError("embedded null character in path"),
    ],
)
def test_the_belt_never_turns_a_surprise_into_a_measurement(workspace, monkeypatch, exc):
    """Pin the belt's output. A belt that fabricated a digest would be the worst bug
    this module could have, and the invariant guard cannot see it."""
    monkeypatch.setattr(ingest, "resolve_workspace_path", _raise(exc))
    entry = ingest._fingerprint(str(workspace), "src/refund.py")
    assert entry["status"] == "unreached", entry
    assert entry["sha256"] is None, entry
    assert entry["note"].startswith("unexpected:"), entry
    assert entry["note"] != "", entry


def test_the_belt_swallow_does_not_reach_base_exception(workspace, monkeypatch):
    """`KeyboardInterrupt`/`SystemExit` must not be absorbed into a `note`.

    Catching `BaseException` in the belt would turn Ctrl-C into one file's worth of
    `unexpected: KeyboardInterrupt` and let the run carry on. The belt is `Exception`
    and that is a decision, not an accident.
    """
    for exc in (KeyboardInterrupt, SystemExit):
        monkeypatch.setattr(ingest, "resolve_workspace_path", _raise(exc("stop")))
        with pytest.raises(exc):
            ingest._fingerprint(str(workspace), "src/refund.py")


def test_the_belt_note_carries_no_server_path(workspace, monkeypatch):
    """The note is attacker-visible, so it must not quote a filesystem path.

    With the resolver raising `OSError("/srv/secret/db.sqlite")` a bare `str(exc)`
    put that path straight into the run record. Everything else in this module reports
    an errno *name* and never a path (`_why`); the belt was the one place that did not.
    """
    monkeypatch.setattr(
        ingest, "resolve_workspace_path", _raise(OSError("/srv/secret/db.sqlite"))
    )
    entry = ingest._fingerprint(str(workspace), "src/refund.py")
    assert "/srv/secret/db.sqlite" not in entry["note"], entry
    assert entry["note"] == "unexpected: OSError"


@pytest.mark.parametrize(
    "candidate",
    [
        "../../etc/passwd",
        "/etc/passwd",
        "src/../../escape.py",
        "a/b/../../../c.py",
        "nonexistent.py",
        "",
        "   ",
        "\x00null.py",
        "esc/../secret.txt",
        "//etc//passwd",
        "loop",
        "a" * 300 + ".py",
        "x/" * 400 + "y.py",
        "dir",
        "fifo",
        "dangling",
        "unreadable.py",
        "big.bin",
        "ok.py",
    ],
)
def test_the_resolver_never_defers_to_the_belt(workspace, candidate):
    """The belt stays the exception, not the rule.

    Every one of these is refused by `resolve_workspace_path` with a *named* reason, so
    none of them may arrive as `unexpected:`. This is what keeps the belt from quietly
    becoming the normal path — narrowing the resolver's own `except` tuple would
    otherwise still leave a green suite.
    """
    entry = ingest._fingerprint(str(workspace), candidate)
    assert not entry["note"].startswith("unexpected:"), (candidate, entry)


def test_containment_is_component_wise_and_not_a_string_prefix(workspace, tmp_path):
    """A sibling directory whose name *starts with* the root's name is OUTSIDE it.

    `str(resolved).startswith(str(base))` reads as equivalent to `is_relative_to` and is
    not: with the workspace `.../ws` and a candidate `../ws-sibling/secret.txt`, the
    string form returns True and hashes the sibling's content, while `is_relative_to`
    correctly refuses. A mutation swapping one for the other survived the whole suite,
    because every existing escape fixture used a target with no shared prefix. This is
    the only test that tells the two implementations apart.
    """
    sibling = tmp_path / f"{Path(workspace).name}-sibling"
    sibling.mkdir()
    (sibling / "secret.txt").write_text("x")
    absolute, reason = ingest.resolve_workspace_path(
        workspace, f"../{sibling.name}/secret.txt"
    )
    assert absolute is None, (absolute, reason)
    assert reason.startswith("escapes_workspace"), reason


def test_the_read_is_bound_to_the_approved_object_not_to_the_path(workspace):
    """A symlink substituted between the resolver and the read must not be followed.

    Deterministic, no race needed: approve a regular file, replace it with a symlink to
    a file outside the root, then hand the *approved absolute path* to `_digest`. A plain
    `open(resolved)` hashes the outside file and reports a measurement with an empty
    note; `O_NOFOLLOW` refuses with `ELOOP` and an `fstat` makes the descriptor the
    authority. This is the resolve/open gap, and the FIFO variant of it is worse — a
    FIFO substituted the same way blocks in `open()` forever, so a run never reaches a
    verdict at all.
    """
    outside = workspace.parent / "outside.bin"
    outside.write_bytes(b"secret-content")

    swap = workspace / "swap.bin"
    swap.write_bytes(b"\0" * 8)
    approved, reason = ingest.resolve_workspace_path(str(workspace), "swap.bin")
    assert approved is not None and reason == "", (approved, reason)

    # The substitution: same name, now a symlink pointing out of the root.
    swap.unlink()
    swap.symlink_to(outside)

    digest, why = ingest._digest(approved)
    assert digest is None, (digest, why)
    assert why.startswith("unreadable:"), why
    # And the belt must not have laundered it into a measurement either.
    assert "secret-content" not in why


def test_a_fifo_is_refused_before_the_read_rather_than_hanging(workspace):
    """The `S_ISREG` guard's failure mode is a hang, so assert it fires at all.

    A FIFO substituted for the approved file would block in `open()` forever, and a
    guard whose failure signature is a timeout is indistinguishable from CI flakiness —
    which is how a load-bearing guard gets disabled. No timeout marker is available
    (no new dependency), so the assertion is simply that the refusal is immediate and
    named. If this test ever hangs, the guard is gone.
    """
    fifo = workspace / "pipe"
    os.mkfifo(fifo)
    approved, reason = ingest.resolve_workspace_path(str(workspace), "pipe")
    assert approved is None, (approved, reason)
    assert reason == "not_a_regular_file: fifo", reason


# --- the invariant this module exists for -------------------------------------------


def test_every_unreached_entry_names_a_reason(workspace, outside):
    """One payload carrying every refusal at once, asserting the invariant across all of
    them rather than one class at a time: `unreached` implies a `None` digest and a
    non-empty reason, and `measured` implies a real digest and no note. A `sha256: ""`
    on an unmeasured file is the defect this stage exists to prevent, and an empty
    `note` is the same defect in the neighbouring field."""
    os.mkfifo(workspace / "pipe")
    (workspace / "innocent.py").symlink_to(outside)
    (workspace / "src" / "blob.bin").write_bytes(b"\0" * (DOCUMENTED_CAP + 1))
    (workspace / "src" / "refund.py").write_text("ok = True\n", encoding="utf-8")
    entries = _run(
        workspace,
        {
            "diff_paths": [
                "src/refund.py",
                "src/gone.py",
                "../outside/secret.txt",
                str(outside),
                "src",
                "pipe",
                "innocent.py",
                "blob.bin",
            ]
        },
    )["files"]

    assert len(entries) == 8
    for entry in entries:
        if entry["status"] == "measured":
            assert entry["note"] == "", entry
            assert entry["sha256"] is not None, entry
            assert len(entry["sha256"]) == 64, entry
        else:
            assert entry["status"] == "unreached", entry
            assert entry["note"], f"unreached entry with no reason: {entry}"
            assert entry["sha256"] is None, f"unreached entry with a digest: {entry}"
    # Exactly one of the eight is measurable, and it is the real file. Asserted by name
    # rather than by position: `files` is sorted, so position would pin the sort order
    # twice over and read as if the entries arrived in payload order.
    assert {entry["path"] for entry in entries if entry["status"] == "measured"} == {
        "src/refund.py"
    }


# --- the resolver is the one place containment is decided --------------------------


def test_resolver_refuses_a_traversal_attempt_directly(workspace, outside):
    """M6 re-verifies M4's digests and is forbidden from duplicating this logic, so the
    resolver is called as the public choke point M6 will use — not through the stage."""
    absolute, reason = resolve_workspace_path(workspace, "../outside/secret.txt")
    assert absolute is None
    assert reason == "escapes_workspace: resolves outside the workspace root"


def test_resolver_returns_a_path_and_an_empty_reason_for_a_good_path(workspace):
    target = workspace / "src" / "refund.py"
    target.write_text("x = 1\n", encoding="utf-8")
    absolute, reason = resolve_workspace_path(workspace, "src/refund.py")
    assert reason == ""
    assert absolute == str(target.resolve())


@pytest.mark.parametrize(
    "candidate",
    [None, 7, {"path": "src/refund.py"}, ["src/refund.py"], b"src/refund.py", "", "   "],
)
def test_resolver_never_raises_for_a_malformed_candidate(workspace, candidate):
    absolute, reason = resolve_workspace_path(workspace, candidate)
    assert absolute is None
    assert reason


def test_resolver_survives_a_hostile_workspace_root(workspace, outside):
    """The root is process configuration, so a bad one is an operator mistake rather
    than an attack — but it still must not raise, because the caller has a record to
    finish writing."""
    for root in (None, 7, "", "\x00bad", str(outside / "nope")):
        absolute, reason = resolve_workspace_path(root, "src/refund.py")
        assert absolute is None or isinstance(absolute, str)
        assert isinstance(reason, str)


def test_resolver_refuses_a_symlink_loop_without_raising(workspace):
    """`Path.resolve()` raises `RuntimeError` on a loop, which is neither `OSError` nor
    `ValueError`. A crafted payload can name a loop, so the resolver catches it."""
    (workspace / "loop").symlink_to(workspace / "loop")
    absolute, reason = resolve_workspace_path(workspace, "loop")
    assert absolute is None
    assert reason.startswith("unresolvable: ")


# --- the workspace root -----------------------------------------------------------


def test_missing_workspace_still_returns_and_every_file_says_why(tmp_path):
    """A misconfigured root must not turn into a stack trace mid-run; M6 would get
    nothing to re-verify and the stage would leave no bundle at all."""
    gone = tmp_path / "not_there"
    out = _run(gone, {"diff_paths": ["src/refund.py", "src/other.py"]})
    assert out["stage"] == "ingest"
    assert out["workspace"] == str(gone.resolve())
    assert [entry["status"] for entry in out["files"]] == ["unreached", "unreached"]
    for entry in out["files"]:
        assert entry["sha256"] is None
        assert entry["note"] == "workspace_missing: no such directory"


def test_workspace_that_is_a_file_is_not_a_workspace(tmp_path):
    not_a_dir = tmp_path / "workspace_file.txt"
    not_a_dir.write_text("x\n", encoding="utf-8")
    out = _run(not_a_dir, {"diff_paths": ["src/refund.py"]})
    assert out["workspace"] == str(not_a_dir.resolve())
    assert out["files"][0]["note"] == "workspace_not_a_directory: regular_file"


def test_workspace_is_configuration_not_a_payload_field(workspace, outside):
    """The payload may name a `workspace` key, and it is ignored.

    If the root came from the body, an attacker would set it to `/` and every
    containment check in this module would be theatre — the same failure M12 found in
    the policy, where `edit` was withheld while the directory was still writable. The
    blast radius of ignoring it is nil for the honest payload (§1.7's worked example
    carries no such key).
    """
    out = _run(
        workspace,
        {"workspace": str(outside.parent), "diff_paths": ["secret.txt"]},
    )
    assert out["workspace"] == str(workspace.resolve())
    # Unreached, because `secret.txt` is not in the *configured* root. The contrast is
    # the point: the same payload against a root that is `outside.parent` measures the
    # file, so the refusal below is the configured root holding and not a path that
    # could never have worked.
    assert out["files"][0]["status"] == "unreached"
    assert out["files"][0]["sha256"] is None
    honoured = _run(
        outside.parent,
        {"workspace": str(outside.parent), "diff_paths": ["secret.txt"]},
    )
    assert honoured["files"][0]["status"] == "measured"


# --- a payload that is not a payload ----------------------------------------------


@pytest.mark.parametrize(
    "diff_paths",
    [
        [None, 1, 2.5, True, {"a": 1}, ["nested"], b"bytes"],
        "src/refund.py",
        {"path": "src/refund.py"},
        42,
        [""],
        ["   "],
        ["\x00"],
        ["../" * 40 + "etc/passwd"],
    ],
)
def test_hostile_path_lists_never_raise(workspace, diff_paths):
    """The contract says never raise for a hostile input; a nested object in
    `diff_paths` is exactly the shape that makes `.strip()` raise `AttributeError` and
    takes the stage with it."""
    out = _run(workspace, {"diff_paths": diff_paths})
    assert out["stage"] == "ingest"
    assert out["ok"] is True
    assert isinstance(out["files"], list)
    assert isinstance(out["rejected_paths"], list)


def test_non_string_entries_are_reported_not_dropped(workspace):
    """A path the stage could not read is a fact about the run. Dropping it would leave
    M6 re-verifying a shorter list than the payload asked for, with nothing to tell it
    so. Only the index and reason are recorded: echoing a hostile object into
    `runs.json` would be the same denial of service by another route."""
    out = _run(workspace, {"diff_paths": ["src/a.py", {"evil": ["x"]}, 3]})
    assert out["files"] == [] or [e["path"] for e in out["files"]] == ["src/a.py"]
    assert out["rejected_paths"] == [
        {"index": 1, "reason": "not_a_string: dict"},
        {"index": 2, "reason": "not_a_string: int"},
    ]


def test_blank_entries_are_reported_separately_from_wrong_types(workspace):
    out = _run(workspace, {"diff_paths": ["", "   "]})
    assert out["files"] == []
    assert [item["reason"] for item in out["rejected_paths"]] == [
        "not_a_path: blank",
        "not_a_path: blank",
    ]


def test_a_non_list_diff_paths_is_one_rejection(workspace):
    out = _run(workspace, {"diff_paths": "src/refund.py"})
    assert out["files"] == []
    assert out["rejected_paths"] == [{"index": None, "reason": "not_a_list: str"}]


def test_the_whole_stage_survives_a_payload_that_is_not_a_dict():
    """An injected demo payload is a documented path, and JSON's top level is not
    always an object. A stage that raises here has certified nothing while looking as
    though it tried."""
    for payload in (None, [], "opened", 7):
        out = ingest.run(payload)
        assert out["stage"] == "ingest"
        assert out["input_keys"] == []


# --- M4 makes no LLM call ---------------------------------------------------------


def test_ingest_imports_nothing_from_the_llm_package():
    """M4's AC: normalization only, watsonx.ai belongs to M5.

    Proven from the source rather than from behaviour, because the failure being
    guarded is an import that exists but happens not to be called on the paths these
    tests exercise — a document path needing a model is the case the AC names, and
    nothing here would reach it. Walking the AST rather than grepping means a name
    inside a docstring or comment cannot trip the guard, and a genuine `import` in any
    form can.
    """
    import ast

    tree = ast.parse(INGEST_SOURCE.read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            # `level` is how many dots led the relative import: 1 is `app.gates`, 2 is
            # `app`, so `from ..llm import x` is level 2 and has to be counted.
            module = node.module or ""
            prefix = "." * node.level + module
            imported.add(prefix)
            imported.update(f"{prefix}.{alias.name}" for alias in node.names)
    assert not [name for name in imported if "llm" in name.split(".")], imported
    assert not [name for name in imported if "client" in name.split(".")], imported


def test_importing_the_gate_leaves_the_llm_package_unloaded():
    """The dynamic half of the same claim, in a subprocess so this suite's own
    `test_llm.py` imports of `app.llm` cannot make the check pass for the wrong reason.

    `sys.modules` is the strong form: a lazily-imported client would not appear in
    `ingest.py`'s AST either, and a module aliased under another name would still have
    to land in `sys.modules` to be used.
    """
    probe = textwrap.dedent(
        """
        import sys
        import app.gates.ingest  # noqa: F401
        assert not [m for m in sys.modules if m == "app.llm" or m.startswith("app.llm.")], \\
            sorted(m for m in sys.modules if "llm" in m)
        print("clean")
        """
    )
    env = {**os.environ, "PYTHONPATH": str(BACKEND_DIR)}
    result = subprocess.run(
        [sys.executable, "-c", probe],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(BACKEND_DIR),
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert "clean" in result.stdout


def test_ingest_does_not_reference_a_model_client_by_name():
    """Belt to the AST guard's braces: the two sanctioned client names and the
    selector, absent from the source as text. Cheap, and it fires on a
    `getattr`-style lookup that the AST walk would not see."""
    text = INGEST_SOURCE.read_text(encoding="utf-8")
    body = "\n".join(
        line for line in text.splitlines() if not line.lstrip().startswith("#")
    )
    for name in ("select_client", "mock_client", "watsonx_client", "MOCK_LLM", "httpx"):
        assert name not in body, name
