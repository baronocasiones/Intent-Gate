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

    No defaults, for the same reason `Criterion` has none: all five keys are in
    the contract's `required`, and a probe that silently defaulted its `note` or
    `location` to `""` would attest that something was examined when it was not.

    Two properties of the contract are load-bearing and are carried across
    deliberately rather than "cleaned up":

    * **`result` is unenumerated.** Its vocabulary belongs to M7, not to M1, so
      it stays `str` here. The moment M7 ratifies one, M3 changes in the same
      commit (AC 3).
    * **`evidence_tier` is ABSENT, on purpose.** The contract expects a tier
      alongside it, and the E0-E6 ladder is still undefined in the source — it
      is decision **D1**, unratified. The contract says in its own `description`
      not to add it, so it is not added here, and the model enforces no tier
      constraint. Adding a field now would invent a contract M1 has not written.

    `probe` reuses the contract's five-value enum as a `Literal`, so an unknown
    probe name is a loud `ValidationError` rather than a finding attributed to a
    probe nobody ran. The enum is pinned to the contract by
    `test_schemas_contracts.py::FIVE_PROBES`; note that this is the same alias->
    field wiring that `architecture.md` 11.12 records as unguarded for
    `Verdict` / `EvidenceTier` — `Probe` inherits that gap rather than closing it.
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
