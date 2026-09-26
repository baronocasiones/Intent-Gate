"""Receipt renderer - a human-readable rendering of a signed run artefact.

The artefact is the record. The receipt reports what that record contains and
what state it is in, including when it is unsigned or its digest does not
match. Nothing here asserts a signature it cannot verify.
"""
from .render import (
    CHAIN_ACTIVE,
    CHAIN_NOTE,
    DATA_ARTEFACTS,
    GAP,
    LADDER_PROVISIONAL,
    PROVISIONAL_NOTE,
    RATIONALE_GAP,
    TIERS,
    TAMPERED,
    UNMEASURED,
    UNSIGNED,
    VERDICTS,
    canonical_digest,
    debt_entries,
    digest_state,
    exposure_measured,
    is_signed,
    missing_artefacts,
    render,
)
from .store import write_receipt

__all__ = [
    "CHAIN_ACTIVE",
    "CHAIN_NOTE",
    "DATA_ARTEFACTS",
    "GAP",
    "LADDER_PROVISIONAL",
    "PROVISIONAL_NOTE",
    "RATIONALE_GAP",
    "TIERS",
    "TAMPERED",
    "UNMEASURED",
    "UNSIGNED",
    "VERDICTS",
    "canonical_digest",
    "debt_entries",
    "digest_state",
    "exposure_measured",
    "is_signed",
    "missing_artefacts",
    "render",
    "write_receipt",
]
