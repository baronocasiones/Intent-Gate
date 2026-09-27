"""Read-only verifier policy, and the evidence that it was applied.

Two layers, and the second one is the point. The capability set below is a
declaration: it says what a worker was told it may do. `sandbox.py` is the
observation: it tries the write the policy forbids and records what the kernel
did. Only the second is worth an auditor's time. Withholding `edit` while the
workspace is still a writable directory is a claim, and selling claims is the
thing this project exists to stop doing.

GRANTS: read, subagent fan-out (OS processes), skill, workflow — Bob-harness
permission groups — plus llm_egress, an OS-level network property. The two kinds
are separate constants below so nobody reads GRANTS as one flat list
(docs/modules.md §1.6, "do not conflate them").
WITHHOLDS: edit, execute — structurally incapable of modifying what it verifies.
Never weaken this in demo shortcuts.

`assert_read_only` is a set comparison, so on its own it proves nothing: it can
only fail if the set it checks came from somewhere other than this module. The
worker path is therefore
    declared caps (os.environ[ATTESTOR_CAPS_ENV]) + workspace path
    -> resolve_worker_caps -> enforce_workspace_readonly -> policy_record
    -> PolicyRecord
Both halves fail closed. A declaration that is absent, empty, non-string, or
outside the closed vocabulary GRANTS | DENIES raises PermissionError. So does a
workspace that is writable, or that cannot be probed at all. GRANTS is never used
as a fallback and a workspace is never assumed read-only. Widening either is a
deliberate edit to the constants below, never a side effect of a more forgiving
parser. `llm_egress` landed exactly that way: option (b) means each M7b worker
calls watsonx.ai itself, so a worker needs egress, so the token was added here
with tests pinning it. DENIES did not move. Note that no code exercises that
grant yet — there is no worker pool, and MOCK_LLM is read nowhere in backend/app
(architecture.md §11.9) — so it is declared ahead of the thing that needs it, and
the docs say so rather than implying a capability that is enforced.

A third guarantee sits behind both halves. A refused write is two different
findings and the record says which: a read-only mount is the D6 mechanism, and a
missing write bit is a weaker, separately-owned permission on one inode. Both
refuse a worker; only one is the boundary D6 asks for, so `workspace_mechanism`
never words the weaker one as read-only. The mount's own ST_RDONLY answer travels
beside it as `workspace_mount_readonly`, three-valued, with null meaning "we
could not ask" and never false. The write is the authority throughout — the flag
is read after it and cannot override it. And the ungated record path refuses a
denied capability exactly as the gated one does, so no record this module can
mint both claims `edit` and denies it.

What the gate now installs is the weaker half of that pair, and the record says
so. `sandbox.ensure_readonly_workspace()` provisions a workspace that refuses
writes — 0555 on POSIX, a directory ACL on Windows — and the proof it returns is
`no_write_bit`, because a permission on one directory is exactly what it is.
Reading and listing stay available; the verifier has to read. One mutation
survives the Windows form, unlinking a file that was already there, because
Windows will not express readable-and-undeletable from a plain deny ACE. Both
facts are measured in `sandbox.py` and pinned by tests, and neither is smoothed
over: the D6 read-only mount, which has no such gap, is still M10's to provide.

Both downstream wirings are one line each, and both are now made. A worker
launched without all five tokens, or without a workspace it can prove
read-only, refuses to start:
    export ATTESTOR_CAPS="read, subagent, skill, workflow, llm_egress"
    M7/M10 worker startup:  enforce_worker_read_only(
        os.environ.get(ATTESTOR_CAPS_ENV), workspace)
    M9 emitted record:      record["attestor_policy"] = policy.to_dict()
`orchestrator/pipeline.py` is that call site (per run, before the first stage),
and the second line is `run_pipeline`'s. The workspace it passes comes from
`ATTESTOR_WORKSPACE`, and `sandbox.ensure_readonly_workspace()` provisions it
first — this module only ever observes, and nothing could refuse a write before
that existed. Copy both, and do not trim either: the gate is the whole claim.
"""

import os
from dataclasses import dataclass

from .sandbox import (
    MECHANISM_UNDETERMINED,
    WriteProof,
    enforce_workspace_readonly,
)

# GRANTS is the union of two different kinds of thing, and the split is
# structural rather than a comment, so a future edit has to decide which layer it
# is touching (docs/modules.md §1.6 — "do not conflate them"):
#   read, subagent, skill, workflow — Bob-harness permission groups, the
#     `attestor` custom mode. Pre-existing, and what Figure 6 draws in the
#     attestor box.
#   llm_egress — an OS-level network property, not a harness group. Nothing in
#     Bob config grants it and no reader should infer it is a Bob group; it is
#     here because assert_read_only asks one uniform question (may the worker do
#     this), not because the harness knows what it is.
# Figure 6 and docs/intent-attestation-gate.md §3.3 still show only the four
# groups. That drift is real and is being fixed in docs at session close.
#
# llm_egress exists because of option (b): each M7b worker calls watsonx.ai
# itself for LLM reasoning, since fan-out is N OS processes
# (docs/intent-attestation-gate.md:33). A worker that cannot reach watsonx.ai
# cannot verify anything. Named for the capability kind, never a host: the region
# is env config (WATSONX_URL) and IAM is a different host again
# (docs/watsonx-integration.md:67), so a token like
# egress:us-south.ml.cloud.ibm.com would need a code change per region, break on
# reconfiguration, and still miss the auth hop. llm_egress covers both the auth
# and the inference endpoint.
#
# A blanket `network` grant is deliberately absent and must stay absent: a worker
# with open egress can exfiltrate the very source it reads, which is the read-only
# claim itself. test_policy pins the rejection.
#
# What OS_PROPERTIES does not do is restrict the destination. The name asserts the
# kind of egress; the allowlist that pins it to watsonx.ai is the OS-level one, the
# layer a worker cannot forge. Neither set is that boundary.
HARNESS_GROUPS = frozenset({"read", "subagent", "skill", "workflow"})
OS_PROPERTIES = frozenset({"llm_egress"})
GRANTS = HARNESS_GROUPS | OS_PROPERTIES
DENIES = frozenset({"edit", "execute"})

# The variable a worker is launched with. Named here so M10 does not hardcode
# the string; the read itself stays at the launch site, which keeps this module
# free of global state and the tests free of env patching.
ATTESTOR_CAPS_ENV = "ATTESTOR_CAPS"

# The witness on a record for a run that never gated. Explicit, because the
# ungated marker and a probed-and-refused marker are the two things an auditor
# most needs to tell apart, and "False" alone cannot tell them.
NOT_PROBED_WITNESS = "not probed: this run never gated"


def _refuse_leaked(granted: frozenset, context: str) -> None:
    """The one place a denied capability is caught, on both record paths.

    `context` names which defect the caller found, because the ungated path's
    defect is not the gated one's: a run that never gated has no policy to
    violate, so a denied name in its capabilities is an incoherent record rather
    than a leak. Both raise and neither repairs — dropping the name instead would
    mint a record that reads as policy-compliant when nothing was ever checked,
    which is the one repair this module must never make.
    """
    leaked = set(granted) & set(DENIES)
    if leaked:
        raise PermissionError(f"attestor policy violation — {context}: {sorted(leaked)}")


@dataclass(frozen=True)
class PolicyRecord:
    """Auditor fragment: the capabilities the run actually had, the sets that
    decide them, and both the fact that enforcement ran and the observation that
    the workspace was read-only when it did. The last two are why this is more
    than a restatement of GRANTS — `workspace_witness` is the kernel's answer,
    carried verbatim so a reader does not have to take our word for it. Immutable
    and clock-free, so emitted records stay reproducible. to_dict() is JSON-ready.

    Three of these keys exist because a refused write is two different findings and
    a record that cannot tell them apart sells the claim. `workspace_path` names the
    directory that was actually probed, so the record is evidence about something
    rather than a reassurance; `workspace_mechanism` says which control answered
    (a read-only mount, or the weaker missing write bit); `workspace_mount_readonly`
    is the mount's independent answer and is deliberately three-valued, with None
    meaning "we could not ask" and never False. Note the cost: the fragment is no
    longer environment-free, so the same run on two machines produces different
    bytes here. That is accepted — the artefact is hashed, not this fragment — and
    the clock is still absent, so repeated runs against one workspace agree.
    """

    capabilities: tuple[str, ...]
    granted: tuple[str, ...]
    denied: tuple[str, ...]
    enforcement_applied: bool
    workspace_readonly: bool
    workspace_witness: str
    workspace_path: str
    workspace_mechanism: str
    workspace_mount_readonly: bool | None
    workspace_mount_witness: str

    def to_dict(self) -> dict:
        return {
            "capabilities": list(self.capabilities),
            "granted": list(self.granted),
            "denied": list(self.denied),
            "enforcement_applied": self.enforcement_applied,
            "workspace_readonly": self.workspace_readonly,
            "workspace_witness": self.workspace_witness,
            "workspace_path": self.workspace_path,
            "workspace_mechanism": self.workspace_mechanism,
            "workspace_mount_readonly": self.workspace_mount_readonly,
            "workspace_mount_witness": self.workspace_mount_witness,
        }


def assert_read_only(granted: frozenset) -> None:
    _refuse_leaked(granted, "denied caps granted")
    missing = set(GRANTS) - set(granted)
    if missing:
        raise PermissionError(f"attestor policy incomplete — missing: {sorted(missing)}")


def resolve_worker_caps(declared: str | None) -> frozenset[str]:
    """Parse the capability set a worker process was actually launched with.
    `declared` is that raw string, e.g. os.environ.get(ATTESTOR_CAPS_ENV).
    A declaration that is absent, empty, not a string, or names a capability this
    policy does not define is refused, never repaired. A denied name parses fine
    here and is rejected by assert_read_only, so the vocabulary question lives in
    the parser and the policy judgement lives in the policy."""
    if declared is None:
        raise PermissionError(
            f"attestor policy unresolved — {ATTESTOR_CAPS_ENV} absent, "
            "worker did not declare its capabilities"
        )
    if not isinstance(declared, str):
        raise PermissionError(
            "attestor policy unresolved — capability declaration must be str, "
            f"got {type(declared).__name__}"
        )
    tokens = declared.replace(",", " ").split()
    if not tokens:
        raise PermissionError(
            f"attestor policy unresolved — empty capability declaration in {ATTESTOR_CAPS_ENV}"
        )
    unknown = sorted(set(tokens) - (GRANTS | DENIES))
    if unknown:
        raise PermissionError(
            f"attestor policy unresolved — capability not in policy vocabulary: {unknown}"
        )
    return frozenset(tokens)


def policy_record(
    caps: frozenset,
    *,
    enforcement_applied: bool,
    proof: WriteProof | None = None,
) -> PolicyRecord:
    """Build the auditor fragment, and refuse to mint a record that advertises a
    control it does not have.

    Claiming enforcement re-runs assert_read_only, so the record cannot claim
    read-only over capabilities that would not survive the check. It additionally
    requires a witness: enforcement_applied=True without a successful read-only
    proof raises, because `enforcement_applied` is now a claim about the workspace
    as much as about the capability set, and a claim about the workspace with no
    probe behind it is the exact failure mode this module exists to remove.

    The inverse also holds: enforcement_applied=False is the honest marker for a
    run that never gated, and such a record reports workspace_readonly=False with
    the not-probed witness. Supplying a proof alongside it is a contradiction
    (the only path to workspace_readonly=True is a gated run) and raises rather
    than quietly dropping the evidence.

    That ungated branch is also where a denied capability used to slip through.
    It returned without consulting DENIES at all, so `capabilities` could be
    ["edit"] in a record whose own `denied` says ["edit", "execute"] — a
    self-contradicting object, minted by the module whose purpose is that those
    two cannot both be true. The leak check now runs on this path too, with its
    own context string. It is deliberately NOT extended to the completeness check:
    an ungated record legitimately describes a stage that never gated, so
    {"read"} is a valid thing to report and requiring all five grants here would
    make the not-probed marker unusable.

    Real runs take their record from enforce_worker_read_only."""
    if not enforcement_applied:
        _refuse_leaked(caps, "denied caps granted on a record for a run that never gated")
        if proof is not None:
            raise PermissionError(
                "attestor policy incoherent — a workspace proof was supplied for a "
                "run that never gated; workspace_readonly is only claimed on a gated run"
            )
        return PolicyRecord(
            capabilities=tuple(sorted(caps)),
            granted=tuple(sorted(GRANTS)),
            denied=tuple(sorted(DENIES)),
            enforcement_applied=False,
            workspace_readonly=False,
            workspace_witness=NOT_PROBED_WITNESS,
            workspace_path=NOT_PROBED_WITNESS,
            workspace_mechanism=MECHANISM_UNDETERMINED,
            workspace_mount_readonly=None,
            workspace_mount_witness=NOT_PROBED_WITNESS,
        )

    assert_read_only(caps)
    if proof is None:
        raise PermissionError(
            "attestor policy incomplete — enforcement claimed with no workspace "
            "read-only proof"
        )
    if proof.undetermined or proof.writable:
        raise PermissionError(
            "attestor policy incomplete — workspace read-only proof does not "
            f"support the claim: {proof.path} ({proof.witness})"
        )
    return PolicyRecord(
        capabilities=tuple(sorted(caps)),
        granted=tuple(sorted(GRANTS)),
        denied=tuple(sorted(DENIES)),
        enforcement_applied=True,
        workspace_readonly=True,
        workspace_witness=proof.witness,
        workspace_path=proof.path,
        workspace_mechanism=proof.mechanism,
        workspace_mount_readonly=proof.mount_readonly,
        workspace_mount_witness=proof.mount_witness,
    )


def enforce_worker_read_only(declared: str | None, workspace: str | os.PathLike) -> PolicyRecord:
    """Worker-startup gate: resolve the external capability declaration, prove the
    workspace is read-only, and hand back a record carrying both. Raises rather
    than returning, so a worker that cannot prove read-only never starts.

    `workspace` is required, not optional. A worker that cannot prove the
    workspace is read-only has no business running, and a default would make
    forgetting the argument indistinguishable from passing it — the same reason
    there is no default for the capability declaration.

    Order is deliberate: the declaration is validated before the workspace is
    touched, so a worker that is already refused on its face never gets a write
    attempted in its directory and never gets a misleading error about the wrong
    defect."""
    caps = resolve_worker_caps(declared)
    assert_read_only(caps)
    proof = enforce_workspace_readonly(workspace)
    return policy_record(caps, enforcement_applied=True, proof=proof)
