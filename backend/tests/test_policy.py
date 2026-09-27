"""Read-only attestor policy — the documented attestor capability set
(docs/intent-attestation-gate.md §3.3, docs/architecture.md §8) and the evidence
that the policy was applied.

The read-only grant set is the product's differentiator (governance by
construction). These tests are load-bearing: they fail if anyone widens the
policy — never weaken it in demo shortcuts (standing convention).

The middle covers the M12/D6 worker-startup path: resolve the capabilities a
worker declares for itself, assert on that, and prove the check is not the
tautology `assert_read_only(GRANTS)`.

The lower half covers the workspace layer. A capability declaration is a claim
about what a worker was told, and withholding `edit` while the workspace is still
a writable directory is theatre. So the tests below make the kernel answer instead:
every "refused" case uses a real directory with the write bit removed and the
write genuinely attempted. There is no mocking of `os.access` anywhere in this
file, on purpose. The whole value of the probe is that the kernel refused.

Five OS interactions are substituted in this file, and each test's name says which:

  * `Path.write_text` -> EROFS, **once**, in
    `test_refusal_witness_is_the_errno_the_kernel_gave`. A real read-only mount
    needs root, so this box can only provoke EACCES.
  * `os.statvfs` -> a fabricated `f_flag`, **four times** (three claiming
    ST_RDONLY, one raising). Same root problem, plus `tmp_path` is never on a
    read-only mount — the positive mount reading is simply not reachable here.
  * `os.ST_RDONLY` deleted, **once**, to prove the platform-without-the-constant
    path degrades to `undetermined` instead of raising or guessing.

Everything else runs against the real filesystem. That includes the fail-open
direction, which is the one that matters most: a genuinely writable directory is
read for real, its write is genuinely refused by a real 0555 mode, and the mount
flag is genuinely read from the kernel in both cases. No mock is involved in any
assertion about a real workspace.

Three environment hazards, handled by fixtures rather than by luck:
  * A 0555 directory defeats pytest's tmp_path cleanup, which uses
    shutil.rmtree and cannot unlink inside a directory it may not write to. Any
    test that chmods down restores the mode, or the entire run errors during
    teardown.
  * Root ignores the write bit, so under root a 0555 directory stays writable and
    every read-only expectation would fail for a reason that looks like a product
    bug. Those tests skip, with the reason stated, instead of failing confusingly.
  * Windows does not enforce the read-only attribute on directories, so a 0555
    directory there also still accepts a file. ro_workspace attempts the write
    before yielding and skips — with the reason stated — when the platform takes
    it, because a directory the kernel would write to is not read-only and the
    failure would read as a product bug. Where the kernel refuses, it still
    refuses for real: the write is genuinely attempted every time, and Linux CI
    runs every refusal case.

The ELOOP case needs a symlink, which Windows grants only with the symlink
privilege; that test skips when the privilege is missing, with the reason
stated.


`llm_egress` is the fifth grant. Option (b) puts the watsonx.ai call in each M7b
worker, so a worker needs outbound network. The tests below declare the complete
five-token set everywhere, including in the leak tests: assert_read_only checks
leaks before gaps, so a four-token leak test would have passed for the wrong
reason.
"""
import errno
import inspect
import json
import os
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from app.attestor.policy import (
    ATTESTOR_CAPS_ENV,
    DENIES,
    GRANTS,
    HARNESS_GROUPS,
    NOT_PROBED_WITNESS,
    OS_PROPERTIES,
    assert_read_only,
    enforce_worker_read_only,
    policy_record,
    resolve_worker_caps,
)
from app.attestor.sandbox import (
    MECHANISM_MOUNT,
    MECHANISM_NO_WRITE_BIT,
    MECHANISM_UNDETERMINED,
    MECHANISM_WRITABLE,
    PROBE_NAME,
    REFUSAL_ERRNOS,
    UNDETERMINED_ERRNOS,
    WriteProof,
    enforce_workspace_readonly,
    probe_workspace_readonly,
)

# A worker's raw launch declaration, in the comma/whitespace form M10 supplies.
# Complete: all five grants, because a short declaration now fails closed and
# every test below that declares capabilities should isolate one failure mode.
DECLARED = "read, subagent skill,workflow,llm_egress"

# The two errno names that mean the write did not land. A 0555 directory gives
# EACCES; a read-only mount gives EROFS. Which one you get is the platform's
# choice, so tests assert membership rather than one exact name.
REFUSAL_NAMES = {"EROFS", "EACCES"}

# Root cannot be tested against permission bits, and pretending otherwise produces
# a failure that reads as a product bug. Stated rather than silently passed.
IS_ROOT = hasattr(os, "geteuid") and os.geteuid() == 0
SKIP_AS_ROOT = pytest.mark.skipif(
    IS_ROOT,
    reason=(
        "running as root: the write bit is advisory, so a 0555 directory still "
        "accepts a write and the read-only probe has nothing honest to observe"
    ),
)


@pytest.fixture
def rw_workspace(tmp_path):
    """An ordinary writable directory, which is the state this policy exists to
    catch. Also the argument for the capability-rejection tests, where the
    workspace is deliberately not the subject: those assert on the error message,
    which pins which check fired."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    return workspace


@pytest.fixture
def ro_workspace(tmp_path):
    """A directory the kernel has genuinely refused to write to, with the mode
    restored on the way out.

    The chmod alone is a promise, not a proof: root ignores the write bit and
    Windows does not enforce it on directories, so the fixture attempts the
    probe's own write first. A refusal means the promise holds and the tests
    below get the real observation they exist for. An accepted write means this
    platform cannot express read-only at all, so they skip with that stated
    rather than fail looking like a product bug."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    original = os.stat(workspace).st_mode
    os.chmod(workspace, 0o555)
    try:
        probe = workspace / PROBE_NAME
        refused = False
        try:
            probe.touch()
        except OSError as exc:
            if exc.errno in REFUSAL_ERRNOS:
                refused = True
            else:
                raise
        if not refused:
            probe.unlink()
            pytest.skip(
                "platform cannot make a directory read-only: a 0555 directory "
                "here still accepted a write, so there is no kernel refusal to "
                "observe (root and Windows both behave this way); Linux CI runs "
                "these tests"
            )
        yield workspace
    finally:
        os.chmod(workspace, original & 0o7777)


@pytest.fixture
def ro_mode_workspace(tmp_path):
    """A directory with the read-only mode applied but not verified, for the
    tests whose subject is consistency rather than refusal: two probes agreeing,
    no residue left behind, and a proof rejected regardless of what it says all
    hold on any platform, and none of them asserts that the kernel said no."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    original = os.stat(workspace).st_mode
    os.chmod(workspace, 0o555)
    try:
        yield workspace
    finally:
        os.chmod(workspace, original & 0o7777)


def test_grants_match_documented_attestor_capability_set():
    """Five tokens: the four Bob-harness permission groups plus llm_egress.

    The old name pointed at Figure 6, which is stale: the figure and
    intent-attestation-gate.md §3.3 still show four. Both need a docs update, and
    the generator is the other half of that. This pins the code, which is the
    part that must not drift.
    """
    assert GRANTS == frozenset({"read", "subagent", "skill", "workflow", "llm_egress"})


def test_denies_edit_and_execute():
    assert DENIES == frozenset({"edit", "execute"})


def test_grants_and_denies_disjoint():
    """The policy must never overlap — a cap cannot be granted and denied."""
    assert set(GRANTS) & set(DENIES) == set()


def test_exact_policy_passes():
    assert_read_only(GRANTS)  # must not raise


def test_leaked_edit_raises_permission_error():
    with pytest.raises(PermissionError, match="denied caps granted"):
        assert_read_only(GRANTS | {"edit"})


def test_leaked_execute_raises_permission_error():
    with pytest.raises(PermissionError, match="denied caps granted"):
        assert_read_only(GRANTS | {"execute"})


def test_missing_grant_fails_closed():
    """Incomplete policy fails closed, not open (§8: fails on leak OR gap)."""
    with pytest.raises(PermissionError, match="missing"):
        assert_read_only({"read"})


def test_empty_grants_fail_closed():
    with pytest.raises(PermissionError):
        assert_read_only(frozenset())


def test_edit_only_fails_on_leak_first():
    """Leak is checked before incompleteness — error names the leak."""
    with pytest.raises(PermissionError, match="denied caps granted"):
        assert_read_only({"edit"})


# --- the two layers of GRANTS are separate constants, not one flat list ---


def test_grants_is_exactly_the_union_of_the_two_layers():
    """docs/modules.md §1.6: do not conflate the harness groups with the
    OS-level property. Making that structural means the union is checkable."""
    assert GRANTS == HARNESS_GROUPS | OS_PROPERTIES
    assert HARNESS_GROUPS & OS_PROPERTIES == frozenset()


def test_llm_egress_is_an_os_property_not_a_harness_group():
    """The split earns its keep only if llm_egress lands on the OS side of it. If
    someone renames the token to `network` or files it under the harness groups,
    this fails — and a reader of the code can no longer be misled about which
    layer grants it."""
    assert OS_PROPERTIES == frozenset({"llm_egress"})
    assert "llm_egress" in OS_PROPERTIES
    assert "llm_egress" not in HARNESS_GROUPS
    assert HARNESS_GROUPS == frozenset({"read", "subagent", "skill", "workflow"})


# --- resolving what the worker was actually launched with (fail closed) ---


def test_attestor_caps_env_name_is_the_wiring_contract():
    """M10 launches workers with this variable. Renaming it disconnects the
    worker from the check without failing anything else."""
    assert ATTESTOR_CAPS_ENV == "ATTESTOR_CAPS"


def test_resolve_worker_caps_from_external_declaration():
    """The worker's own declaration is the source of truth, not GRANTS."""
    caps = resolve_worker_caps(DECLARED)
    assert caps == GRANTS
    assert isinstance(caps, frozenset)


def test_resolve_worker_caps_tolerates_separators_and_order():
    """The declared format is M10's to produce, so pin what we accept."""
    assert resolve_worker_caps(" workflow\tread  ,, llm_egress\nskill, subagent ") == GRANTS


def test_resolve_worker_caps_fails_closed_when_source_absent():
    with pytest.raises(PermissionError, match="ATTESTOR_CAPS absent"):
        resolve_worker_caps(None)


def test_resolve_worker_caps_fails_closed_on_empty_declaration():
    with pytest.raises(PermissionError, match="empty capability declaration"):
        resolve_worker_caps("")


def test_resolve_worker_caps_fails_closed_on_whitespace_only_declaration():
    with pytest.raises(PermissionError, match="empty capability declaration"):
        resolve_worker_caps("   \t\n  ")


def test_llm_egress_is_genuinely_in_the_vocabulary():
    """The grant under test has to parse. The next two tests assert rejection,
    and a resolver that rejected everything would satisfy both."""
    assert "llm_egress" in GRANTS
    assert "llm_egress" in resolve_worker_caps(DECLARED)


def test_resolve_worker_caps_rejects_capability_outside_the_vocabulary():
    """'reed' is a typo of a grant. Admitting it would leave the worker
    ungranted, and the typo would sit in the emitted record looking official."""
    with pytest.raises(PermissionError, match="not in policy vocabulary"):
        resolve_worker_caps("reed, subagent, skill, workflow, llm_egress")


def test_resolve_worker_caps_rejects_blanket_network_grant(rw_workspace):
    """A blanket egress grant is the widening to refuse: a worker with open
    egress can exfiltrate the source it reads, which is the read-only claim.
    llm_egress names the kind of egress and the OS allowlist pins the
    destination. Swapping one for the other fails here. The workspace is
    writable on purpose — the declaration is the subject, and the matched message
    is what pins that."""
    with pytest.raises(PermissionError, match="not in policy vocabulary"):
        enforce_worker_read_only("read, subagent, skill, workflow, network", rw_workspace)


def test_resolve_worker_caps_rejects_malformed_token():
    with pytest.raises(PermissionError, match="not in policy vocabulary"):
        resolve_worker_caps("read, subagent, skill, workflow, llm_egress;drop table")


def test_resolve_worker_caps_rejects_non_string_declaration():
    for junk in (123, ["read"], ("read", "skill")):
        with pytest.raises(PermissionError, match="must be str"):
            resolve_worker_caps(junk)


def test_resolve_worker_caps_never_falls_back_to_grants():
    """Fail closed means raising. No unusable source may resolve to something
    safe-looking, which is the one way a bad declaration could pass unnoticed."""
    for bad in (
        None,
        "",
        "   ",
        "reed, subagent, skill, workflow, llm_egress",
        "read, subagent, skill, workflow, llm_egress;drop",
        123,
    ):
        with pytest.raises(PermissionError):
            resolve_worker_caps(bad)


# --- worker startup: the single call M7/M10 makes ---


@SKIP_AS_ROOT
def test_enforce_worker_read_only_accepts_declared_caps(ro_workspace):
    policy = enforce_worker_read_only(DECLARED, ro_workspace)
    assert policy.enforcement_applied is True
    assert policy.capabilities == tuple(sorted(GRANTS))


@SKIP_AS_ROOT
def test_worker_declaring_all_five_caps_starts(ro_workspace):
    """The option-(b) happy path, spelled out: read, subagent, skill, workflow
    and llm_egress together, enforcement really applied, against a workspace that
    really refused a write. This is the declaration M7b will actually launch
    with, so if it stops passing M7b does not start."""
    policy = enforce_worker_read_only("read subagent skill workflow llm_egress", ro_workspace)
    assert policy.enforcement_applied is True
    assert policy.granted == ("llm_egress", "read", "skill", "subagent", "workflow")
    assert policy.denied == ("edit", "execute")
    assert policy.workspace_readonly is True


def test_worker_omitting_only_llm_egress_fails_closed(rw_workspace):
    """The new grant is a requirement, not a note in a comment. The four-group
    declaration that used to launch a worker is now refused, and the error names
    the one capability it left out."""
    with pytest.raises(PermissionError, match=r"missing: \['llm_egress'\]"):
        enforce_worker_read_only("read subagent skill workflow", rw_workspace)


def test_enforce_worker_read_only_rejects_declared_edit(rw_workspace):
    """The control, not the claim. A worker declaring `edit` cannot start, and
    an `assert_read_only(GRANTS)` implementation would return a record here
    instead of raising, failing this test. That is the tautology guard."""
    with pytest.raises(PermissionError, match="denied caps granted"):
        enforce_worker_read_only("read subagent skill workflow llm_egress edit", rw_workspace)


def test_enforce_worker_read_only_rejects_declared_execute(rw_workspace):
    with pytest.raises(PermissionError, match="denied caps granted"):
        enforce_worker_read_only(
            "execute,read subagent skill workflow llm_egress", rw_workspace
        )


def test_enforce_worker_read_only_rejects_missing_grant(rw_workspace):
    with pytest.raises(PermissionError, match="missing"):
        enforce_worker_read_only("read subagent skill", rw_workspace)


def test_enforce_worker_read_only_refuses_without_an_external_declaration(rw_workspace):
    """No external source, no proof of read-only, so no record is minted at all.
    A tautological `assert_read_only(GRANTS)` would hand one back here."""
    with pytest.raises(PermissionError, match="ATTESTOR_CAPS absent"):
        enforce_worker_read_only(None, rw_workspace)


# --- the workspace probe: the observation behind the declaration ---


def test_probe_file_name_cannot_collide_with_real_content():
    """A dotfile, so a probe can neither overwrite workspace content nor show up
    in someone's `ls`. The name is a contract with the residue tests below, which
    look for exactly this file."""
    assert PROBE_NAME.startswith(".")
    assert "attestor" in PROBE_NAME


@SKIP_AS_ROOT
def test_probe_reports_refused_on_a_read_only_directory(ro_workspace):
    """The core observation. A 0555 directory gives EACCES; a read-only mount
    gives EROFS. Either counts, and the witness is the kernel's own name for it,
    so the emitted record carries evidence rather than our summary of it."""
    proof = probe_workspace_readonly(ro_workspace)
    assert proof.writable is False
    assert proof.undetermined is False
    assert proof.witness in REFUSAL_NAMES
    assert proof.path == str(ro_workspace)


@SKIP_AS_ROOT
def test_two_probes_of_the_same_read_only_workspace_agree(ro_mode_workspace):
    """Evidence is worth nothing if it flickers. Two probes of one unchanged
    workspace must produce the same witness, so a record is reproducible."""
    assert probe_workspace_readonly(ro_mode_workspace).to_dict() == (
        probe_workspace_readonly(ro_mode_workspace).to_dict()
    )


@SKIP_AS_ROOT
def test_probe_reports_writable_on_a_normal_directory(rw_workspace):
    """The failure the whole module is aimed at. A plain writable directory
    accepts the forbidden write, and the probe says so rather than implying
    safety from the absence of an error."""
    proof = probe_workspace_readonly(rw_workspace)
    assert proof.writable is True
    assert proof.undetermined is False
    assert proof.witness == "writable"


def test_probe_leaves_no_residue_when_the_write_succeeds(rw_workspace):
    """A probe that leaves a file in the tree it is probing has contaminated the
    run it was supposed to be observing, and a worker about to be denied `edit`
    must not find an unexpected dotfile in the workspace."""
    probe_workspace_readonly(rw_workspace)
    assert not (rw_workspace / PROBE_NAME).exists()
    assert list(rw_workspace.iterdir()) == []


@SKIP_AS_ROOT
def test_probe_leaves_no_residue_after_a_refusal(ro_mode_workspace):
    """A refusal writes nothing by definition, so the workspace must come out
    exactly as it went in. Worth pinning because the probe is a write attempt."""
    probe_workspace_readonly(ro_mode_workspace)
    assert list(ro_mode_workspace.iterdir()) == []


def test_probe_on_a_missing_path_is_a_visible_failure(tmp_path):
    """A workspace that does not exist is not a read-only workspace. The probe
    must not report it as refused-with-witness, because a caller checking only
    `writable` would read a missing path as a pass."""
    proof = probe_workspace_readonly(tmp_path / "no-such-workspace")
    assert proof.writable is False
    assert proof.undetermined is True
    assert "undetermined" in proof.witness
    assert errno.ENOENT in UNDETERMINED_ERRNOS


def test_probe_on_a_file_rather_than_a_directory_is_a_visible_failure(rw_workspace):
    """Same reasoning for a path that exists but is not a directory."""
    not_a_dir = rw_workspace / "regular-file.txt"
    not_a_dir.write_text("content", encoding="utf-8")
    proof = probe_workspace_readonly(not_a_dir)
    assert proof.writable is False
    assert proof.undetermined is True
    assert "undetermined" in proof.witness


def test_probe_does_not_raise_for_an_ordinary_refusal(ro_workspace):
    """A refusal is a successful answer to the question, so it comes back as
    data. Raising here would make 'the workspace is read-only' indistinguishable
    from 'the probe is broken'.

    CHANGED THIS SESSION: the exact-dict assertion below gained `mechanism`,
    `mount_readonly` and `mount_witness`. The old four-key shape no longer
    describes what a proof carries, and a shape test that only checks the old keys
    is how a record quietly stops being evidence."""
    proof = probe_workspace_readonly(ro_workspace)
    assert isinstance(proof, WriteProof)
    assert proof.to_dict() == {
        "path": str(ro_workspace),
        "writable": False,
        "witness": proof.witness,
        "undetermined": False,
        "mechanism": MECHANISM_NO_WRITE_BIT,
        "mount_readonly": False,
        "mount_witness": proof.mount_witness,
    }
    # and the corroboration is a real reading, not a placeholder
    assert proof.mount_witness and "ST_RDONLY" in proof.mount_witness


def test_write_proof_is_frozen_and_json_ready(rw_workspace):
    """The witness is auditor-visible, so it must not be editable after the fact
    and must survive being embedded in the run record."""
    proof = probe_workspace_readonly(rw_workspace)
    with pytest.raises(FrozenInstanceError):
        proof.writable = False
    assert json.loads(json.dumps(proof.to_dict())) == proof.to_dict()


def test_refusal_errnos_cover_both_read_only_mechanisms():
    """EROFS is a read-only mount and EACCES is a missing write bit; the module
    has to accept either, or the mechanism that is actually deployed in M10 gets
    reported as an unknown malfunction. This pins the constant, not the behaviour
    — a real EROFS needs a bind mount and root, so the behaviour is covered by the
    substitution in the next test instead."""
    assert errno.EROFS in REFUSAL_ERRNOS
    assert errno.EACCES in REFUSAL_ERRNOS
    assert errno.EROFS not in UNDETERMINED_ERRNOS
    assert errno.EACCES not in UNDETERMINED_ERRNOS


def test_refusal_witness_is_the_errno_the_kernel_gave(monkeypatch, rw_workspace):
    """The witness is the kernel's own name for the refusal, not a constant we
    typed. This substitutes the OS call for one reason: a real EROFS needs a
    read-only mount, which needs root, so this box can only provoke EACCES. Every
    other refused case above attempts the write for real.

    Without it, hardcoding the witness to "EACCES" passes the whole suite and then
    mislabels the read-only mount M10 actually deploys — which is the one thing an
    auditor reads this field for.

    CHANGED THIS SESSION: it is no longer the only substitution in this file (see
    the module docstring), and it now also pins the mechanism, because EROFS and
    EACCES stopped being the same finding."""
    def refuse(self, *args, **kwargs):
        raise OSError(errno.EROFS, "Read-only file system")

    monkeypatch.setattr(Path, "write_text", refuse)
    proof = probe_workspace_readonly(rw_workspace)
    assert proof.writable is False
    assert proof.undetermined is False
    assert proof.witness == "EROFS"
    assert proof.mechanism == MECHANISM_MOUNT


# --- which control answered: a refused write is two findings, not one ---


def test_mechanism_names_are_distinct_and_none_of_them_blurs_the_weak_one():
    """The strings that reach the run record. A missing write bit is a permission
    on one inode, reversible by whoever owns the directory; a read-only mount is
    the D6 boundary, a process inside the workspace cannot lift it. Calling the
    first one `read_only` — or anything containing that phrase — would hand an
    auditor the stronger control's name on the weaker control's evidence, which is
    the one substitution this module exists to refuse. Pinned as a string rule
    because no behavioural test can tell you a label reads well."""
    assert MECHANISM_MOUNT == "read_only_mount"
    assert MECHANISM_NO_WRITE_BIT == "no_write_bit"
    assert MECHANISM_WRITABLE == "writable"
    assert MECHANISM_UNDETERMINED == "undetermined"
    assert "read_only" not in MECHANISM_NO_WRITE_BIT
    assert "mount" not in MECHANISM_NO_WRITE_BIT
    assert len({MECHANISM_MOUNT, MECHANISM_NO_WRITE_BIT, MECHANISM_WRITABLE, MECHANISM_UNDETERMINED}) == 4


@SKIP_AS_ROOT
def test_a_missing_write_bit_is_named_as_such_and_not_as_a_mount(ro_workspace):
    """The load-bearing new finding. A 0555 directory gives EACCES, and the record
    now says `no_write_bit` — while independently reporting that the mount holding
    it has no ST_RDONLY. So the auditor learns both halves: the write was refused,
    and the refusal is a permission rather than a mount. No substitution here; the
    write is genuinely attempted and the mount flag is genuinely read."""
    proof = probe_workspace_readonly(ro_workspace)
    assert proof.writable is False
    assert proof.mechanism == MECHANISM_NO_WRITE_BIT
    assert proof.mount_readonly is False
    assert "no ST_RDONLY" in proof.mount_witness


@SKIP_AS_ROOT
def test_a_writable_workspace_reports_a_writable_mount_too(rw_workspace):
    """The same real reading on the ordinary directory, so the corroboration is
    known to work in both directions rather than only returning False by accident.
    This is also the fail-open guard: a real writable workspace must never come
    back with mount_readonly True, which would be a claim nobody can act on."""
    proof = probe_workspace_readonly(rw_workspace)
    assert proof.writable is True
    assert proof.mechanism == MECHANISM_WRITABLE
    assert proof.mount_readonly is False
    assert "no ST_RDONLY" in proof.mount_witness


def test_the_write_is_the_authority_and_the_mount_flag_cannot_override_it(
    monkeypatch, rw_workspace
):
    """The precedence invariant, tested where it would be violated.

    Here the forbidden write genuinely lands on a genuinely writable directory,
    and the mount is made to claim ST_RDONLY. A module that let the flag win would
    report `writable: False` here and let a worker start on a directory that just
    accepted a write — the fail-open inversion of everything this module claims.
    The finding must follow the write.

    The statvfs substitution is named as one: `tmp_path` is never on a read-only
    mount, and manufacturing one needs root."""
    class _ReadOnlyMount:
        f_flag = os.ST_RDONLY

    monkeypatch.setattr(os, "statvfs", lambda path: _ReadOnlyMount())
    proof = probe_workspace_readonly(rw_workspace)
    assert proof.writable is True, "the mount flag overrode a write that landed"
    assert proof.mechanism == MECHANISM_WRITABLE
    # the flag is still reported, honestly, as what it claimed
    assert proof.mount_readonly is True


@SKIP_AS_ROOT
def test_an_unaskable_mount_is_undetermined_and_does_not_fail_the_refused_write(
    monkeypatch, ro_workspace
):
    """Corroboration never gates. A platform that cannot answer leaves the record
    less informed, not the worker unstarted: the refused write is the control, and
    it stands alone. If this raised, the module would refuse to start wherever
    `statvfs` is unavailable — including any platform we have not thought about —
    and the refusal would say nothing about whether the control held."""
    def refuse_statvfs(path):
        raise OSError(errno.EPERM, "Operation not permitted")

    monkeypatch.setattr(os, "statvfs", refuse_statvfs)
    proof = probe_workspace_readonly(ro_workspace)
    assert proof.writable is False
    assert proof.witness in REFUSAL_NAMES
    assert proof.mount_readonly is None
    assert proof.mount_witness.startswith("undetermined")
    # the gate still returns the proof rather than raising
    assert enforce_workspace_readonly(ro_workspace).writable is False


@SKIP_AS_ROOT
def test_a_platform_without_st_read_only_records_undetermined_never_false(
    monkeypatch, ro_workspace
):
    """The absent constant is the trap. Reading `os.ST_RDONLY` unguarded raises
    AttributeError out of the worker gate; rounding the absence down to False
    would instead assert a fact about a mount nobody asked. Undetermined is the
    only honest answer, and `is None` is asserted rather than `not ...` so the
    test cannot be satisfied by the falsy value."""
    monkeypatch.delattr(os, "ST_RDONLY", raising=False)
    proof = probe_workspace_readonly(ro_workspace)
    assert proof.writable is False, "the refusal must not depend on the flag"
    assert proof.mount_readonly is None
    assert "ST_RDONLY" in proof.mount_witness


@SKIP_AS_ROOT
def test_a_read_only_mount_is_reported_as_one_when_the_kernel_says_so(
    monkeypatch, ro_workspace
):
    """The positive case for the corroboration. `os.statvfs` is substituted because a
    real read-only mount needs root; the write itself is **not** substituted — it is
    genuinely attempted on a 0555 directory and genuinely refused, which is why
    `mechanism` stays `no_write_bit` while the mount says otherwise. That pairing is
    synthetic and is not meant to look like a deployment: a real read-only mount
    returns EROFS and this test would then be asserting the same two fields from a
    real reading, which is `test_refusal_witness_is_the_errno_the_kernel_gave`'s job.

    What is being proven is narrow and worth having: the mount answer is reported
    from the mount, and reported True, rather than being inferred from the errno."""
    class _ReadOnlyMount:
        f_flag = os.ST_RDONLY

    monkeypatch.setattr(os, "statvfs", lambda path: _ReadOnlyMount())
    proof = probe_workspace_readonly(ro_workspace)
    assert proof.writable is False
    assert proof.mechanism == MECHANISM_NO_WRITE_BIT
    assert proof.mount_readonly is True
    assert "ST_RDONLY on the mount" in proof.mount_witness


@SKIP_AS_ROOT
def test_the_two_deployments_are_told_apart_by_the_mount_reading(
    monkeypatch, ro_workspace
):
    """A 0555 directory on a writable mount, and a 0555 directory on a read-only
    one, are different deployments and must not produce the same fragment.

    The mechanism field is identical in both — correctly, the write was refused the
    same way in each — so the mount reading is the only thing that tells them
    apart. That is the whole argument for carrying it, and a test asserting on
    `mechanism` alone would pass both deployments without noticing they are not
    the same claim."""
    permissive = probe_workspace_readonly(ro_workspace)

    class _ReadOnlyMount:
        f_flag = os.ST_RDONLY

    monkeypatch.setattr(os, "statvfs", lambda path: _ReadOnlyMount())
    mounted = probe_workspace_readonly(ro_workspace)

    assert permissive.mechanism == mounted.mechanism == MECHANISM_NO_WRITE_BIT
    assert permissive.mount_readonly is False
    assert mounted.mount_readonly is True
    assert permissive.mount_witness != mounted.mount_witness


def test_probe_propagates_an_unrecognised_errno_instead_of_inventing_a_witness(rw_workspace):
    """A refusal we cannot name is a malfunction, not a finding, and it escapes as
    an exception. Handing back a witness we made up would be the single lie this
    module is not allowed to tell. A symlink loop yields ELOOP for real, which is
    in neither accepted set, so the write is genuinely attempted and genuinely
    fails the interesting way.

    It also covers the cleanup on the raising path: nothing the failed attempt
    left behind survives, so a malfunction cannot litter the workspace either.

    Windows grants the right to create symlinks only to privileged or
    developer-mode sessions, and ELOOP has no other honest spelling here, so a
    session without the privilege skips with the reason stated instead."""
    probe = rw_workspace / PROBE_NAME
    try:
        os.symlink(probe, probe)  # self-referential, so open() gives ELOOP
    except OSError as exc:
        pytest.skip(
            f"symlink privilege unavailable ({exc.strerror or exc}); ELOOP cannot "
            "be provoked on this session; Linux CI runs this test"
        )
    with pytest.raises(OSError) as caught:
        probe_workspace_readonly(rw_workspace)
    assert caught.value.errno == errno.ELOOP
    assert not os.path.lexists(probe)


# --- the gate in front of the gate ---


@SKIP_AS_ROOT
def test_enforce_workspace_readonly_returns_the_proof_on_a_read_only_workspace(ro_workspace):
    """It hands back the proof rather than just a bool, so the caller has
    something to put in the record."""
    proof = enforce_workspace_readonly(ro_workspace)
    assert proof.writable is False
    assert proof.witness in REFUSAL_NAMES


def test_enforce_workspace_readonly_raises_on_a_writable_workspace(rw_workspace):
    """Fails closed. A writable workspace is exactly the state the policy is
    supposed to exclude, so the function that guards worker startup must refuse
    rather than return.

    CHANGED THIS SESSION: the message now carries the mount's own answer as well
    as the errno. The operator's next move depends on which mechanism is missing —
    a workspace that is merely chmodded will keep accepting writes the moment that
    bit is restored, and the message should not leave them guessing between a
    chmod and a bind mount."""
    with pytest.raises(PermissionError) as caught:
        enforce_workspace_readonly(rw_workspace)
    message = str(caught.value)
    assert "accepted a write" in message
    assert "no ST_RDONLY" in message


def test_enforce_workspace_readonly_raises_on_an_unprobeable_path(tmp_path):
    """Undeterminable is a failure, not a pass. `writable` is False here, so a
    caller that checked only that flag would wave a nonexistent workspace
    through; the undetermined branch is what stops it."""
    with pytest.raises(PermissionError, match="undetermined"):
        enforce_workspace_readonly(tmp_path / "no-such-workspace")


# --- the load-bearing pair: a real worker startup ---


@SKIP_AS_ROOT
def test_enforce_worker_read_only_succeeds_against_a_read_only_workspace(ro_workspace):
    """The wiring M7b ships, end to end: declare the five caps, prove the
    workspace, get a record that says both happened."""
    policy = enforce_worker_read_only(DECLARED, ro_workspace)
    assert policy.enforcement_applied is True
    assert policy.workspace_readonly is True
    assert policy.workspace_witness in REFUSAL_NAMES
    assert policy.capabilities == tuple(sorted(GRANTS))


def test_enforce_worker_read_only_raises_on_a_writable_workspace(rw_workspace):
    """The load-bearing test. A correct capability set and a writable workspace
    must still refuse to start. This is the whole claim of the module: the
    attestation is architecture, not policy, so the workspace has to be able to
    veto a worker whose declaration is perfect. An implementation that resolves
    caps, checks the set, and returns without ever touching the filesystem fails
    here and nowhere else that matters."""
    with pytest.raises(PermissionError, match="writable"):
        enforce_worker_read_only(DECLARED, rw_workspace)


def test_enforce_worker_read_only_raises_on_an_unprobeable_workspace(tmp_path):
    """A workspace path that does not exist cannot be attested to, so the worker
    does not start."""
    with pytest.raises(PermissionError, match="undetermined"):
        enforce_worker_read_only(DECLARED, tmp_path / "no-such-workspace")


def test_enforce_worker_read_only_requires_a_workspace_argument():
    """Required, not defaulted. A default is precisely the bug this change
    exists to prevent, because forgetting the argument would then look exactly
    like passing it."""
    parameters = inspect.signature(enforce_worker_read_only).parameters
    assert parameters["workspace"].default is inspect.Parameter.empty
    with pytest.raises(TypeError):
        enforce_worker_read_only(DECLARED)


# --- the auditor-visible fragment: the payload M9 embeds (AC#3) ---


def test_policy_record_capabilities_reflect_the_given_set_not_the_constant():
    """`capabilities` is a function of the resolved set, never GRANTS baked in.
    A build-the-record-from-GRANTS implementation returns all five grants here
    and fails this test."""
    ungated = policy_record(frozenset({"read"}), enforcement_applied=False)
    assert ungated.capabilities == ("read",)
    assert ungated.granted == tuple(sorted(GRANTS))
    assert ungated.denied == tuple(sorted(DENIES))


def test_policy_record_cannot_claim_enforcement_for_leaked_caps():
    """enforcement_applied=True has to mean assert_read_only would have passed,
    or the record advertises a control the capabilities do not support. The
    capability check runs before the proof check, so the leak is the reported
    reason and the matched message proves it."""
    with pytest.raises(PermissionError, match="denied caps granted"):
        policy_record(GRANTS | {"execute"}, enforcement_applied=True)


def test_policy_record_cannot_claim_enforcement_without_a_read_only_proof():
    """A record may never advertise a control it does not have. Before the
    workspace layer existed, enforcement_applied=True was a claim with nothing
    behind it; now it requires a witness, and omitting the proof is the mistake
    that has to be loud rather than default."""
    with pytest.raises(PermissionError, match="no workspace read-only proof"):
        policy_record(GRANTS, enforcement_applied=True)


@SKIP_AS_ROOT
def test_policy_record_cannot_claim_readonly_for_a_writable_proof(rw_workspace):
    """The proof contradicts the claim. Handing a writable proof to the record
    builder must not launder it into workspace_readonly=True."""
    proof = probe_workspace_readonly(rw_workspace)
    assert proof.writable is True
    with pytest.raises(PermissionError, match="does not support the claim"):
        policy_record(GRANTS, enforcement_applied=True, proof=proof)


def test_policy_record_cannot_claim_readonly_for_an_undetermined_proof(tmp_path):
    """writable is False here, so a builder that only checked that flag would mint
    a read-only claim out of a workspace that does not exist."""
    proof = probe_workspace_readonly(tmp_path / "no-such-workspace")
    with pytest.raises(PermissionError, match="does not support the claim"):
        policy_record(GRANTS, enforcement_applied=True, proof=proof)


@SKIP_AS_ROOT
def test_policy_record_embeds_the_observation_from_the_proof(ro_workspace):
    """The witness travels with the record verbatim, rather than being restated
    in our own words. An auditor reading the run record should be able to see
    which of the two refusal mechanisms produced the answer."""
    proof = probe_workspace_readonly(ro_workspace)
    record = policy_record(GRANTS, enforcement_applied=True, proof=proof)
    assert record.workspace_readonly is True
    assert record.workspace_witness == proof.witness
    assert record.workspace_witness in REFUSAL_NAMES


def test_ungated_record_reports_the_workspace_as_not_readonly():
    """A run that never gated says so in the record, which is what makes an
    ungated demo shortcut visible to an auditor instead of silent (AC#4). The
    witness has to distinguish 'not probed' from 'probed and refused', because
    workspace_readonly is False in both cases and those are opposite facts."""
    ungated = policy_record(frozenset(), enforcement_applied=False)
    assert ungated.enforcement_applied is False
    assert ungated.workspace_readonly is False
    assert ungated.workspace_witness == NOT_PROBED_WITNESS
    assert "not probed" in ungated.workspace_witness


def test_ungated_record_names_no_workspace_rather_than_an_empty_one():
    """A run that never gated has no directory to name, and the field says so in
    words. `""` would be the wrong answer twice over: it reads as a path, and it is
    exactly the 'unmeasured must not look like zero' failure in a string field.
    The mount answer is null for the same reason — there was no mount to ask
    about, and false would be a claim about one."""
    ungated = policy_record(frozenset(), enforcement_applied=False)
    assert ungated.workspace_path == NOT_PROBED_WITNESS
    assert ungated.workspace_path != ""
    assert ungated.workspace_mechanism == MECHANISM_UNDETERMINED
    assert ungated.workspace_mount_readonly is None
    assert ungated.workspace_mount_readonly is not False
    assert ungated.workspace_mount_witness == NOT_PROBED_WITNESS


def test_ungated_record_cannot_advertise_a_denied_capability():
    """The hole this session closed. The ungated branch returned without ever
    consulting DENIES, so it would mint a record whose `capabilities` is ["edit"]
    while its own `denied` says ["edit", "execute"] — the module whose purpose is
    that those cannot both be true, producing both. A gated record already refused
    this; the not-probed marker was the way around it.

    The message has to distinguish this defect from the gated path's: a run that
    never gated has no policy to violate, so this is an incoherent record rather
    than a leak, and an operator reading the error should not have to work out
    which check fired."""
    for denied in ("edit", "execute"):
        with pytest.raises(PermissionError, match="never gated"):
            policy_record(GRANTS | {denied}, enforcement_applied=False)
        with pytest.raises(PermissionError, match=denied):
            policy_record(GRANTS | {denied}, enforcement_applied=False)


def test_the_ungated_leak_check_is_not_a_completeness_check():
    """The boundary of the fix, and the reason the new check is deliberately
    narrow. An ungated record describes a stage that never gated, so a partial
    capability set is a legitimate thing to report — requiring all five grants
    here would make the not-probed marker unusable and push callers toward
    inventing a full set they never had. So partial passes, leaked fails, and the
    two must not be conflated into one 'fail closed' rule."""
    partial = policy_record(frozenset({"read"}), enforcement_applied=False)
    assert partial.capabilities == ("read",)
    assert partial.enforcement_applied is False
    with pytest.raises(PermissionError, match="never gated"):
        policy_record(frozenset({"read", "edit"}), enforcement_applied=False)


@SKIP_AS_ROOT
def test_record_names_the_workspace_it_was_actually_proven_on(ro_workspace):
    """The fragment has to be evidence about something. Before this session the
    record carried a bare errno string, so a run record could say 'a workspace was
    refused' without ever saying which one — which is true of every workspace on
    the machine. The path is a function of the probe, so an implementation that
    built the record from a constant or from GRANTS fails this."""
    record = enforce_worker_read_only(DECLARED, ro_workspace)
    assert record.workspace_path == str(ro_workspace)
    assert record.workspace_path == str(probe_workspace_readonly(ro_workspace).path)
    assert record.workspace_mechanism == MECHANISM_NO_WRITE_BIT
    assert record.workspace_mount_readonly is False


def test_policy_record_rejects_a_proof_on_an_ungated_record(ro_mode_workspace):
    """A run that never gated reporting workspace_readonly=True would be
    incoherent: the only path to that value is a gated run. Raising beats
    dropping the proof on the floor, which is the habit this module is trying to
    break everywhere else."""
    proof = probe_workspace_readonly(ro_mode_workspace)
    with pytest.raises(PermissionError, match="never gated"):
        policy_record(GRANTS, enforcement_applied=False, proof=proof)


@SKIP_AS_ROOT
def test_enforced_record_shape_is_json_ready(ro_workspace):
    """Exact fragment M9 places under record["attestor_policy"].

    CHANGED THIS SESSION: four keys added — the workspace that was probed, the
    mechanism that refused, the mount's own answer, and that answer's witness.
    The point of the added keys is that an auditor can no longer read this
    fragment without learning which control actually held."""
    witness = probe_workspace_readonly(ro_workspace).witness
    enforced = enforce_worker_read_only(DECLARED, ro_workspace)
    assert enforced.to_dict() == {
        "capabilities": ["llm_egress", "read", "skill", "subagent", "workflow"],
        "granted": ["llm_egress", "read", "skill", "subagent", "workflow"],
        "denied": ["edit", "execute"],
        "enforcement_applied": True,
        "workspace_readonly": True,
        "workspace_witness": witness,
        "workspace_path": str(ro_workspace),
        "workspace_mechanism": MECHANISM_NO_WRITE_BIT,
        "workspace_mount_readonly": False,
        "workspace_mount_witness": enforced.workspace_mount_witness,
    }
    # the fragment is self-describing: the corroboration is explained, not just present
    assert "ST_RDONLY" in enforced.workspace_mount_witness


def test_ungated_record_shape_is_json_ready():
    """The other shape M9 can emit, for a stage that never gated. Every key is
    present so an auditor reading the record never has to guess whether a missing
    field meant 'no' or 'not checked'.

    CHANGED THIS SESSION: the three new workspace keys appear here too, and none
    of them is empty or zero. The path carries the not-probed sentence rather than
    "", and the mount answer is null rather than false — a run that never probed
    has no mount to describe, and null says that where False would be a claim."""
    assert policy_record(GRANTS, enforcement_applied=False).to_dict() == {
        "capabilities": ["llm_egress", "read", "skill", "subagent", "workflow"],
        "granted": ["llm_egress", "read", "skill", "subagent", "workflow"],
        "denied": ["edit", "execute"],
        "enforcement_applied": False,
        "workspace_readonly": False,
        "workspace_witness": NOT_PROBED_WITNESS,
        "workspace_path": NOT_PROBED_WITNESS,
        "workspace_mechanism": MECHANISM_UNDETERMINED,
        "workspace_mount_readonly": None,
        "workspace_mount_witness": NOT_PROBED_WITNESS,
    }


@SKIP_AS_ROOT
def test_policy_record_is_json_serialisable(ro_workspace):
    """M9 embeds to_dict() in the run record, so it has to survive JSON."""
    policy = enforce_worker_read_only(DECLARED, ro_workspace)
    assert json.loads(json.dumps(policy.to_dict())) == policy.to_dict()


@SKIP_AS_ROOT
def test_policy_record_is_deterministic_across_calls(ro_workspace):
    """No clock, no run id, no randomness: two workers on the same declaration
    and the same workspace produce byte-identical fragments, so records stay
    reproducible and hashable."""
    first = json.dumps(enforce_worker_read_only(DECLARED, ro_workspace).to_dict())
    second = json.dumps(enforce_worker_read_only(DECLARED, ro_workspace).to_dict())
    assert first == second


@SKIP_AS_ROOT
def test_policy_record_is_immutable(ro_workspace):
    policy = enforce_worker_read_only(DECLARED, ro_workspace)
    with pytest.raises(FrozenInstanceError):
        policy.enforcement_applied = False
    with pytest.raises(FrozenInstanceError):
        policy.workspace_witness = "writable"
    payload = policy.to_dict()  # a copy, so mutating it cannot rewrite the record
    payload["capabilities"].append("edit")
    assert policy.capabilities == tuple(sorted(GRANTS))
