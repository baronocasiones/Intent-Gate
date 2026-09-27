"""Typed in-process mirrors of contracts/*.schema.json — one model per contract.

Two tiers, deliberately:
  * contracts/ is the PERMISSIVE interchange layer. None of the six draft-07
    schemas sets `additionalProperties: false`, so extra keys are tolerated by
    omission. That is what lets a fixture or a payload carry more than the
    contract needs.
  * these models are the STRICT trust layer: `extra="forbid"`, so a key no
    contract declares is a loud contract violation rather than a silently
    dropped field. This matches the gate's fail-closed posture (modules.md
    rule 6 — uncertainty resolves to *not certified*), and these are the shapes
    a verdict rests on.

The strictness is pinned by `backend/tests/test_models_parity.py`; it is a
design position, not a default that drifts.

TWO OBLIGATIONS THIS STRICTNESS CREATES — both belong to M9/M14, and neither can
be fixed inside this file without inventing a contract M1 has not ratified:
  1. `store.write_artifact` writes `{"sha256": ..., **payload}` (envelope +
     artifact pointer, pinned by test_store_db.py). Reading an artifact back
     into `RunRecord` must therefore project the owned keys first.
  2. Stage 6's record is a superset of `run.schema.json` — it also carries the
     traceability matrix, the debt ledger, exposure and `signed` (modules.md
     1.7). M9 cannot validate its own output into `RunRecord` unprojected.

The stage chain is NOT affected: `orchestrator/pipeline.py` passes plain dicts
between gates, and rule 3 lets gates add keys. These models are for *records*,
never for the pass-through.

SHAPE ONLY. No D1 tier semantics are encoded here (no "CERTIFIED requires E4",
no tier monotonicity) — that stays with M8/M9 until the ladder is ratified.
`CriterionVerdict.rationale` / `.locations` keep their defaults: strictness
lives at the contract boundary (docs/test-suite.md Convention 5).
"""
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal

Verdict = Literal["CERTIFIED", "CONDITIONAL", "REJECTED", "PENDING"]
EvidenceTier = Literal["E0", "E1", "E2", "E3", "E4", "E5", "E6"]
Probe = Literal["CODE_SEARCH", "LOGIC_TRACE", "STATE_CHECK", "ERROR_PATH", "ABSENCE_CHECK"]


class ContractModel(BaseModel):
    """Base for every contract mirror — see the module docstring for the why."""

    model_config = ConfigDict(extra="forbid")


class Criterion(ContractModel):
    """contracts/criterion.schema.json — produced by M5, consumed by M6/M7.

    No defaults, unlike `CriterionVerdict`: `text=""` would erase the criterion
    and `testable=False` would silently drop it, and an untestable criterion is
    rejected outright rather than verified (modules.md 1.3). These three fields
    are the criterion's identity, so none of them is optional.
    """

    criterion_id: str
    text: str
    testable: bool


class Finding(ContractModel):
    """contracts/findings.schema.json — one probe result against one criterion (M7).

    Merged from two independent additions — one on each side of this merge, both
    adding the same five fields. The union of both docstrings is kept because each
    records something the other does not.

    **No defaults, for the same reason `Criterion` has none.** All five keys are in
    the contract's `required`, and a probe that silently defaulted its `note` or
    `location` to `""` would attest that something was examined when it was not. A
    finding with no location is not admissible evidence at all, so a default here
    would let an unlocated probe result validate as a well-formed one.

    Two properties of the contract are load-bearing and are carried across
    deliberately rather than "cleaned up":

    * **`result` is unenumerated.** Its vocabulary belongs to M7, not to M1, so it
      stays a bare `str` here. Narrowing it in this mirror would smuggle a decision
      into the strict layer that the permissive layer deliberately defers. The
      moment M7 ratifies one, M3 changes in the same commit. Enforced from the model
      side by `test_finding_result_is_not_narrowed_to_a_vocabulary_the_contract_defers`.
    * **`evidence_tier` is ABSENT, on purpose — and D1 is now RATIFIED.** The
      contract forbids declaring it, and the E0-E6 ladder is undefined in the source
      (that was decision **D1**, ratified 2026-09-27 in `docs/modules.md` 1.4). The
      field is still absent, but no longer because D1 is open: the tier is *derived
      by M8 from which probe ran*, not carried on the finding. A finding states what a
      probe observed; a verdict states how far the evidence reached. So the honest
      contract for `findings` has no tier field either way. **Consequence to carry, not
      to act on:** if M1 ever adds `evidence_tier` for M7b, M3 must add it here in the
      same change or M7's output is rejected by its own strict mirror — which is the
      intended direction of failure, loud rather than silent.

    `probe` reuses the contract's five-value enum as the `Probe` alias, so an unknown
    probe name is a loud `ValidationError` rather than a finding attributed to a probe
    nobody ran. `test_mirror_field_types_are_the_contract_field_types` pins the alias's
    members to the contract enum, closing the alias-to-field gap that
    `architecture.md` §11.12 records as unguarded for `Verdict` / `EvidenceTier`.
    """

    criterion_id: str
    probe: Probe
    result: str
    location: str
    note: str


class CriterionVerdict(ContractModel):
    criterion_id: str
    verdict: Verdict
    evidence_tier: EvidenceTier
    locations: list[str] = Field(default_factory=list)
    rationale: str = ""


class RunRecord(ContractModel):
    run_id: str
    status: str
    verdicts: list[CriterionVerdict] = Field(default_factory=list)
    measured: bool = False


class TraceabilityLink(ContractModel):
    """contracts/traceability.schema.json -> `links.items`.

    This object is declared inline in the schema, so it has no `title` of its
    own. `TraceabilityLink` is therefore M3's one invented name; the shape it
    carries is entirely the contract's.
    """

    criterion_id: str
    locations: list[str] = Field(default_factory=list)
    evidence_tier: EvidenceTier


class TraceabilityMatrix(ContractModel):
    run_id: str
    links: list[TraceabilityLink] = Field(default_factory=list)


class Exposure(ContractModel):
    """contracts/exposure.schema.json — the publishable number (M13).

    These defaults ARE the honest pre-measurement state (modules.md 1.7): a
    `null` rate with `measured: false`, never `0.0`. A pre-measurement dashboard
    must not be able to imply a good number.

    `by_operator` is typed from what `metrics.false_certified_rate` actually
    returns (`{op: {"certified": int, "total": int}}`), which is more specific
    than the contract's bare `{"type": "object"}` — and
    `test_models_parity.py` asserts that binding against the real function, so
    the extra specificity is a checked claim rather than an assumption.
    """

    false_certified_rate: float | None = None
    measured: bool = False
    by_operator: dict[str, dict[str, int]] = Field(default_factory=dict)
