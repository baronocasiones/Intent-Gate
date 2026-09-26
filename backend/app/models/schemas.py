"""Shared schemas — per-criterion verdict, traceability, exposure, run envelope."""
from pydantic import BaseModel, Field
from typing import Literal

Verdict = Literal["CERTIFIED", "CONDITIONAL", "REJECTED", "PENDING"]
EvidenceTier = Literal["E0", "E1", "E2", "E3", "E4", "E5", "E6"]


class CriterionVerdict(BaseModel):
    criterion_id: str
    verdict: Verdict
    evidence_tier: EvidenceTier
    locations: list[str] = Field(default_factory=list)
    rationale: str = ""


class RunRecord(BaseModel):
    run_id: str
    status: str
    verdicts: list[CriterionVerdict] = Field(default_factory=list)
    measured: bool = False
