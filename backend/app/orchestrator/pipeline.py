"""Pipeline — ingest → extract → parse → verify → adjudicate → emit.
Non-zero exit blocks merge (gate, not reviewer).

One run's attestor gate: before a single stage executes, the workspace is made
to refuse writes, the refused write is proved, and the capability declaration
the worker was launched with is checked against the policy. A run that cannot
prove either never reaches `ingest` — that is the whole point of a gate, and a
check performed after the work it was supposed to authorise is not one.

Order inside the gate is the same order `enforce_worker_read_only` documents,
for the same reason: provision the workspace, then prove it, then judge the
declaration. Provisioning a run that would have been refused is cheap and
idempotent; refusing on a capability gap before probing saves a write attempt
in a directory nobody was authorised to use. Both halves fail closed, so the
worst case is a refused run, never a run that reads and writes the workspace
while claiming it cannot.

The proof is attached to the record this function returns, under
`attestor_policy`, as the M12 fragment M9 embeds — so the artefact carries the
evidence rather than the promise. The mechanism it reports is `no_write_bit`
(a permission on one directory, which its owner can lift) until M10 provides
the D6 read-only bind mount, and it is never worded as the mount.
"""
import os
import uuid
from pathlib import Path

from ..attestor.policy import ATTESTOR_CAPS_ENV, PolicyRecord, enforce_worker_read_only
from ..attestor.sandbox import (
    DEFAULT_WORKSPACE,
    WORKSPACE_ENV,
    ensure_readonly_workspace,
)
from ..gates import ingest, extract, parse, verify, adjudicate, emit as emit_gate


def _attestor_workspace() -> str:
    """The directory this run verifies against.

    Unset means the product-owned default, which is created on demand because
    the attestor needs a workspace to attest to and inventing nothing here would
    mean refusing every run for a reason an operator cannot act on. A path an
    operator *did* name is never created: inventing a directory because of a
    typo in a configured path is worse than refusing to start, and the refusal
    names the path that was not there.
    """
    configured = os.environ.get(WORKSPACE_ENV)
    if configured is not None:
        return configured
    Path(DEFAULT_WORKSPACE).mkdir(parents=True, exist_ok=True)
    return DEFAULT_WORKSPACE


def _attestor_policy() -> PolicyRecord:
    """Gate this run, and return the proof it will be recorded with.

    Reads the capability declaration at call time rather than at import, so the
    launch site owns it and a test can set it with `monkeypatch.setenv` — the
    alternative, a module-level import-time binding, is what makes env-dependent
    code untestable (docs/test-suite.md Convention 2).
    """
    workspace = _attestor_workspace()
    ensure_readonly_workspace(workspace)
    return enforce_worker_read_only(os.environ.get(ATTESTOR_CAPS_ENV), workspace)


def enqueue_run(payload: dict) -> str:
    """Stub-first: return run id; async execution lands in jobs.py."""
    return f"run-{uuid.uuid4().hex[:8]}"


def run_pipeline(payload: dict) -> dict:
    """Synchronous scaffold path — each gate returns fixture-shaped stub until
    implemented, gated on a workspace the kernel actually refuses to write to.
    """
    policy = _attestor_policy()
    bundle = ingest.run(payload)
    criteria = extract.run(bundle)
    ast = parse.run(criteria)
    findings = verify.run(ast)
    verdict = adjudicate.run(findings)
    record = emit_gate.run(verdict)
    # Shape stability (rule 3): a key added, none renamed or dropped. The
    # fragment is JSON-ready and clock-free, so repeated runs against one
    # workspace agree — see `test_policy.py`.
    record["attestor_policy"] = policy.to_dict()
    return record
