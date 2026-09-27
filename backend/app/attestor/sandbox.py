"""Workspace read-only proof: attempt the forbidden write and report what happened.

`policy.py` withholds a *capability* while the workspace is a *writable directory*.
Withholding `edit` in that setting is theatre, because the process could still
write and nothing in the emitted record would admit it. This module supplies the
other half: evidence from the filesystem itself, obtained by trying the write the
policy says is forbidden and watching the kernel refuse it. EROFS (a read-only
mount) and EACCES (no write bit on the directory) both mean the write did not land,
so both count as refused — but they are not the same *control*, and the distinction
below is the reason this module cannot be reduced to one boolean.

That ordering is the whole pitch. The capability set is the declaration, this is
the observation, and only the second one is worth an auditor's time.

Three outcomes, never conflated:
    refused       the write did not land. witness is the errno name.
    writable      the write landed, and the probe file is removed before returning.
    undetermined  the write was never attempted, because there is no workspace
                  directory to attempt it in. A failure, flagged as one, never
                  reported as safety.

Refused is not one finding, it is two, and this module says which:

    read_only_mount   EROFS — the mount refuses writes. This is the D6 mechanism:
                      a boundary a process inside the workspace cannot lift.
    no_write_bit      EACCES — the directory is not writable. Weaker, and honest
                      about being weaker: it is a permission on one inode, which
                      anyone who owns the directory can put back. It is still a
                      refused write and still gates a worker; it is just not the
                      same control, so the two answers are not collapsed into one
                      boolean. Naming a missing write bit `read_only` would be a
                      lie carrying a kernel's errno, which is the one thing an
                      auditor must be able to rule out.

A second, independent reading corroborates that: `os.statvfs` reports whether the
mount holding the workspace is mounted read-only (`ST_RDONLY`). **The write is the
authority and the flag is only corroboration** — it is read after the write and
can never override it, so a workspace that accepted the forbidden write stays
`writable` even if the flag claims otherwise. An answer we cannot get (no
`statvfs`, no `ST_RDONLY`, a path the kernel will not describe) is recorded as
`undetermined` and never coerced to a value; an absence of evidence is not
evidence of a writable mount, and it is not evidence of a read-only one either.
Corroboration never gates: a refused write stands on its own, because requiring a
specific kernel mechanism would refuse to start wherever the deployment cannot
mount read-only, which says nothing about whether the control held.

The reading is point-in-time, taken at worker startup. Whatever makes the
workspace read-only is the durable control; this records that the control was in
place when the worker started, which is the only moment a run record can speak
about. It is a smoke test on the mount, not a substitute for it — the long-lived
boundary for the duration of a run is the mount, and M10 owns it. A `writable`
answer is the interesting one, because it means the mount that was supposed to
hold is not holding.
"""

import errno
import os
from dataclasses import dataclass
from pathlib import Path

# An unlikely dotfile, so a probe can neither overwrite real workspace content nor
# be mistaken for it, and so `ls` hides it from anyone eyeballing a tree.
PROBE_NAME = ".attestor_write_probe"
_PROBE_BODY = "attestor read-only probe\n"

# The two ways a kernel says no: a read-only mount refuses at the filesystem layer
# (EROFS), a missing write bit refuses at the permission layer (EACCES). Same
# meaning here, and both are the outcome we are looking for.
REFUSAL_ERRNOS = frozenset({errno.EROFS, errno.EACCES})

# The write was never attempted because there is no directory to attempt it in.
# Neither a refusal nor a pass: there is nothing to attest to.
UNDETERMINED_ERRNOS = frozenset({errno.ENOENT, errno.ENOTDIR})

# Which control the kernel actually applied, named as the two different things it
# could have been. These strings reach the emitted run record, so they are part of
# the module's contract with an auditor and are pinned by tests — in particular
# `no_write_bit`, which must never be worded as a read-only anything.
MECHANISM_MOUNT = "read_only_mount"
MECHANISM_NO_WRITE_BIT = "no_write_bit"
MECHANISM_WRITABLE = "writable"
MECHANISM_UNDETERMINED = "undetermined"


@dataclass(frozen=True)
class WriteProof:
    """One observation of one workspace. `writable` is the finding, `witness` is the
    evidence behind it, and `undetermined` keeps "we looked and it refused" apart
    from "we could not look at all" — the two must never read the same to a caller
    deciding whether to start a worker.

    `mechanism` says which control answered a refusal, because a refused write is
    two findings and not one. `mount_readonly` is the mount's independent answer,
    and it is deliberately three-valued: True, False, or None for "we could not
    ask". None is not False — a missing answer is never rounded down into a
    finding, in either direction. Frozen, so a proof cannot be edited into a
    better answer after the fact."""

    path: str
    writable: bool
    witness: str
    undetermined: bool = False
    mechanism: str = MECHANISM_UNDETERMINED
    mount_readonly: bool | None = None
    mount_witness: str = ""

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "writable": self.writable,
            "witness": self.witness,
            "undetermined": self.undetermined,
            "mechanism": self.mechanism,
            "mount_readonly": self.mount_readonly,
            "mount_witness": self.mount_witness,
        }


def _probe_mount_readonly(root: Path) -> tuple[bool | None, str]:
    """Ask the mount holding `root` whether it is mounted read-only.

    Returns `(flag, witness)`, where the flag is True, False, or None for an
    answer we could not get. Corroboration, never the control: the refused write
    in `probe_workspace_readonly` is what gates a worker, and this only labels
    which mechanism produced it. So every failure mode here degrades to None and
    names itself in the witness rather than raising, because a platform without
    `statvfs` is a less-informed caller, not a broken one.

    `ST_RDONLY` is read through `getattr` because it is not guaranteed to exist
    everywhere, and a missing constant must read as "we could not ask" — never as
    "not read-only", and never as an AttributeError from the gate.
    """
    statvfs = getattr(os, "statvfs", None)
    readonly_flag = getattr(os, "ST_RDONLY", None)
    if statvfs is None or readonly_flag is None:
        return None, "undetermined: os.statvfs/ST_RDONLY unavailable on this platform"
    try:
        f_flag = statvfs(root).f_flag
    except OSError as exc:
        return None, (
            f"undetermined: {errno.errorcode.get(exc.errno, str(exc.errno))}"
            f" — {exc.strerror}"
        )
    if f_flag & readonly_flag:
        return True, f"ST_RDONLY on the mount holding {root}"
    return False, f"no ST_RDONLY on the mount holding {root}"


def _refusal_mechanism(code: int) -> str:
    """Name the control the kernel applied. EROFS is the read-only mount, which is
    the D6 mechanism; EACCES is a directory that may not be written, which is a
    weaker and differently-owned control. Same answer to the question we asked,
    different boundary — which is the whole reason this function exists."""
    return MECHANISM_MOUNT if code == errno.EROFS else MECHANISM_NO_WRITE_BIT


def _proof(
    root: Path,
    *,
    writable: bool,
    witness: str,
    mechanism: str,
    undetermined: bool = False,
) -> WriteProof:
    """Assemble the observation, reading the mount's own answer second.

    The order is the invariant: the write is the authority, so the mount is asked
    afterwards and cannot override what the write already showed. A workspace that
    accepted the forbidden write is `writable` and stays `writable` even if the
    mount claims ST_RDONLY — a code that let the flag win there would be the
    fail-open inversion of the whole module, so the two are never compared.
    """
    mount_readonly, mount_witness = _probe_mount_readonly(root)
    return WriteProof(
        str(root),
        writable,
        witness,
        undetermined,
        mechanism,
        mount_readonly,
        mount_witness,
    )


def _remove_probe(probe: Path) -> str:
    """Delete a probe file that was created by a write that should not have
    succeeded. Returns the witness for a writable finding, naming the residue if
    the cleanup itself failed — a probe that leaves a file in the tree it is
    probing has contaminated the run it was supposed to be observing, so that has
    to be visible rather than swallowed."""
    try:
        probe.unlink()
    except OSError as exc:
        return f"writable; {PROBE_NAME} could not be removed ({exc.strerror})"
    return "writable"


def _discard_quietly(probe: Path) -> None:
    """Best-effort cleanup on a path that is about to raise. A write that failed
    after the file was created still leaves residue, and this function is the last
    chance to not leave it."""
    try:
        probe.unlink()
    except OSError:
        pass


def probe_workspace_readonly(path: str | os.PathLike) -> WriteProof:
    """Try to write one dotfile into `path` and report what the filesystem said.

    A refusal is a successful observation, so it comes back as data rather than an
    exception: a caller asking "is my workspace read-only?" has been answered, and
    raising would make the answer indistinguishable from a malfunction. Only a
    genuinely unexpected errno escapes, because a witness we cannot name is not
    evidence.

    A refusal therefore comes back with `mechanism` naming the control that
    answered and `mount_readonly` carrying the mount's own answer, both read after
    the write. Neither is required for a caller to proceed, and neither can veto
    what the write showed."""
    root = Path(path)
    probe = root / PROBE_NAME
    try:
        probe.write_text(_PROBE_BODY, encoding="utf-8")
    except OSError as exc:
        code = exc.errno
        if code in REFUSAL_ERRNOS:
            return _proof(
                root,
                writable=False,
                witness=errno.errorcode.get(code, str(code)),
                mechanism=_refusal_mechanism(code),
            )
        if code in UNDETERMINED_ERRNOS:
            return _proof(
                root,
                writable=False,
                witness=(
                    f"undetermined: {errno.errorcode.get(code, str(code))}"
                    f" — {exc.strerror}"
                ),
                mechanism=MECHANISM_UNDETERMINED,
                undetermined=True,
            )
        _discard_quietly(probe)
        raise
    return _proof(
        root,
        writable=True,
        witness=_remove_probe(probe),
        mechanism=MECHANISM_WRITABLE,
    )


def enforce_workspace_readonly(path: str | os.PathLike) -> WriteProof:
    """Gate a worker startup on the workspace actually being read-only, and hand
    back the proof so the record carries the observation.

    Raises rather than returning on anything short of a witnessed refusal. A
    writable workspace and an unprobeable one are both refusals to start, and they
    are kept apart in the message so a broken path never reads like a passing
    check. Both messages now carry the mount's own answer, because the operator's
    next move differs by mechanism: a `no_write_bit` refusal is fixed at the mount
    and a chmod will not hold it, and a `read_only_mount` refusal is already the
    boundary D6 asks for. Naming only the errno would leave them guessing."""
    proof = probe_workspace_readonly(path)
    if proof.undetermined:
        raise PermissionError(
            f"attestor workspace undetermined — {proof.path} is not a usable "
            f"workspace directory (witness: {proof.witness}; {proof.mount_witness})"
        )
    if proof.writable:
        raise PermissionError(
            f"attestor workspace writable — {proof.path} accepted a write the "
            f"read-only policy forbids (witness: {proof.witness}; "
            f"{proof.mount_witness})"
        )
    return proof
