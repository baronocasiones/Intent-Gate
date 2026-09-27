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
with tests pinning it. DENIES did not move.

Both downstream wirings are one line each. A worker launched without all five
tokens, or without a workspace it can prove read-only, now refuses to start, so
copy both rather than trimming either:
    export ATTESTOR_CAPS="read, subagent, skill, workflow, llm_egress"
    M7/M10 worker startup:  enforce_worker_read_only(
        os.environ.get(ATTESTOR_CAPS_ENV), workspace)
    M9 emitted record:      record["attestor_policy"] = policy.to_dict()
"""

import os
from dataclasses import dataclass

from .sandbox import WriteProof, enforce_workspace_readonly

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


@dataclass(frozen=True)
class PolicyRecord:
    """Auditor fragment: the capabilities the run actually had, the sets that
    decide them, and both the fact that enforcement ran and the observation that
    the workspace was read-only when it did. The last two are why this is more
    than a restatement of GRANTS — `workspace_witness` is the kernel's answer,
    carried verbatim so a reader does not have to take our word for it. Immutable
    and clock-free, so emitted records stay reproducible. to_dict() is JSON-ready."""

    capabilities: tuple[str, ...]
    granted: tuple[str, ...]
    denied: tuple[str, ...]
    enforcement_applied: bool
    workspace_readonly: bool
    workspace_witness: str

    def to_dict(self) -> dict:
        return {
            "capabilities": list(self.capabilities),
            "granted": list(self.granted),
            "denied": list(self.denied),
            "enforcement_applied": self.enforcement_applied,
            "workspace_readonly": self.workspace_readonly,
            "workspace_witness": self.workspace_witness,
        }


def assert_read_only(granted: frozenset) -> None:
    leaked = set(granted) & set(DENIES)
    if leaked:
        raise PermissionError(f"attestor policy violation — denied caps granted: {sorted(leaked)}")
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

    Real runs take their record from enforce_worker_read_only."""
    if not enforcement_applied:
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
