"""Workspace read-only proof: attempt the forbidden write and report what happened.

`policy.py` withholds a *capability* while the workspace is a *writable directory*.
Withholding `edit` in that setting is theatre, because the process could still
write and nothing in the emitted record would admit it. This module supplies the
other half: evidence from the filesystem itself, obtained by trying the write the
policy says is forbidden and watching the kernel refuse it. EROFS (a read-only
mount) and EACCES (no write bit on the directory) are two spellings of the same
answer, so both count as refused.

That ordering is the whole pitch. The capability set is the declaration, this is
the observation, and only the second one is worth an auditor's time.

Three outcomes, never conflated:
    refused       the write did not land. witness is the errno name.
    writable      the write landed, and the probe file is removed before returning.
    undetermined  the write was never attempted, because there is no workspace
                  directory to attempt it in. A failure, flagged as one, never
                  reported as safety.

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


@dataclass(frozen=True)
class WriteProof:
    """One observation of one workspace. `writable` is the finding, `witness` is the
    evidence behind it, and `undetermined` keeps "we looked and it refused" apart
    from "we could not look at all" — the two must never read the same to a caller
    deciding whether to start a worker. Frozen, so a proof cannot be edited into a
    better answer after the fact."""

    path: str
    writable: bool
    witness: str
    undetermined: bool = False

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "writable": self.writable,
            "witness": self.witness,
            "undetermined": self.undetermined,
        }


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
    exception: a caller asking "is this workspace read-only?" has been answered,
    and raising would make the answer indistinguishable from a malfunction. Only a
    genuinely unexpected errno escapes, because a witness we cannot name is not
    evidence."""
    root = Path(path)
    probe = root / PROBE_NAME
    try:
        probe.write_text(_PROBE_BODY, encoding="utf-8")
    except OSError as exc:
        code = exc.errno
        if code in REFUSAL_ERRNOS:
            return WriteProof(str(root), False, errno.errorcode.get(code, str(code)))
        if code in UNDETERMINED_ERRNOS:
            return WriteProof(
                str(root),
                False,
                f"undetermined: {errno.errorcode.get(code, str(code))} — {exc.strerror}",
                undetermined=True,
            )
        _discard_quietly(probe)
        raise
    return WriteProof(str(root), True, _remove_probe(probe))


def enforce_workspace_readonly(path: str | os.PathLike) -> WriteProof:
    """Gate a worker startup on the workspace actually being read-only, and hand
    back the proof so the record carries the observation.

    Raises rather than returning on anything short of a witnessed refusal. A
    writable workspace and an unprobeable one are both refusals to start, and they
    are kept apart in the message so a broken path never reads like a passing
    check."""
    proof = probe_workspace_readonly(path)
    if proof.undetermined:
        raise PermissionError(
            f"attestor workspace undetermined — {proof.path} is not a usable "
            f"workspace directory ({proof.witness})"
        )
    if proof.writable:
        raise PermissionError(
            f"attestor workspace writable — {proof.path} accepted a write the "
            f"read-only policy forbids (witness: {proof.witness})"
        )
    return proof
