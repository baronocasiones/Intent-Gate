"""Provisional spec mutations for the M13 false-certified benchmark.

The transformations deliberately support a small, explicit criterion vocabulary.
D4 still has to select the real corpus before these results are publishable.
The runner is injected so this module neither imports nor starts the unfinished
pipeline, and the attestor can stay read-only while a separate benchmark driver
constructs mutated inputs.
"""

from copy import deepcopy
from dataclasses import dataclass
import logging
import re
from typing import Any, Callable, Mapping, Sequence

from ..models.schemas import Criterion, Exposure
from .false_certified import OPERATORS, false_certified_rate

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MutationRequest:
    operator: str
    criterion: Mapping[str, Any]
    context: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class MutationCase:
    operator: str
    original: dict[str, Any]
    mutated: dict[str, Any]
    context: dict[str, Any] | None = None


Runner = Callable[[MutationCase], Mapping[str, Any]]

_BOUNDARY = re.compile(
    r"\b(?:no more than|no less than|greater than|fewer than|more than|less than|"
    r"at least|at most|over|under|above|below)\s+\$?\d+(?:\.\d+)?\b",
    re.IGNORECASE,
)
_COMPARISON = re.compile(
    r"\b(?:no more than|no less than|greater than|less than|more than|fewer than|"
    r"at least|at most|over|under|above|below)\b(?=\s+\$?\d+(?:\.\d+)?\b)"
    r"|(?:>=|<=|>|<)(?=\s*\$?\d+(?:\.\d+)?\b)",
    re.IGNORECASE,
)
_INVERSE = {
    "no more than": "no less than",
    "no less than": "no more than",
    "greater than": "less than",
    "less than": "greater than",
    "more than": "less than",
    "fewer than": "more than",
    "at least": "at most",
    "at most": "at least",
    "over": "under",
    "under": "over",
    "above": "below",
    "below": "above",
    ">=": "<=",
    "<=": ">=",
    ">": "<",
    "<": ">",
}
_INTEGER = re.compile(r"(?<![\w.\-])\$?(\d+)(?![\w.])")
_ERROR_CLAUSE = re.compile(
    r"^(?:on (?:error|failure)|if\b.*\b(?:fails|errors)\b|retry\b|fallback\b|otherwise\b)",
    re.IGNORECASE,
)
_NEGATIVE_CLAUSE = re.compile(r"\b(?:must not|shall not|never)\b", re.IGNORECASE)
_NORMATIVE = re.compile(r"\b(?:must|shall)\b|\b(?:is )?required to\b", re.IGNORECASE)


def _drop_clause(text: str, pattern: re.Pattern[str]) -> str:
    """Remove one independent semicolon clause; ambiguous prose is unsupported."""
    clauses = [part.strip() for part in text.split(";")]
    if len(clauses) < 2 or any(not part for part in clauses):
        raise ValueError("mutation requires independent semicolon clauses")
    for index, clause in enumerate(clauses):
        if pattern.search(clause):
            remaining = clauses[:index] + clauses[index + 1 :]
            return "; ".join(remaining)
    raise ValueError("mutation target was not found")


def mutate_criterion(criterion: Mapping[str, Any], operator: str) -> dict[str, Any]:
    """Return one changed, schema-shaped criterion or raise on ambiguity."""
    if operator not in OPERATORS:
        raise ValueError(f"unsupported mutation operator: {operator}")

    original = Criterion.model_validate(deepcopy(dict(criterion))).model_dump()
    if not original["testable"] or not original["text"].strip():
        raise ValueError("benchmark input must be a nonempty, testable criterion")
    mutated = deepcopy(original)
    text = original["text"]

    if operator == "boundary_drop":
        match = _BOUNDARY.search(text)
        if match is None:
            raise ValueError("numeric boundary qualifier was not found")
        mutated["text"] = re.sub(r"\s+", " ", text[: match.start()] + text[match.end() :]).strip()
    elif operator == "comparison_inversion":
        match = _COMPARISON.search(text)
        if match is None:
            raise ValueError("supported comparison was not found")
        replacement = _INVERSE[match.group().lower()]
        mutated["text"] = text[: match.start()] + replacement + text[match.end() :]
    elif operator == "threshold_weakening":
        match = _INTEGER.search(text)
        if match is None or int(match.group(1)) < 1:
            raise ValueError("positive integer threshold was not found")
        replacement = match.group().replace(match.group(1), str(int(match.group(1)) - 1))
        mutated["text"] = text[: match.start()] + replacement + text[match.end() :]
    elif operator == "error_path_deletion":
        mutated["text"] = _drop_clause(text, _ERROR_CLAUSE)
    elif operator == "normative_demotion":
        match = _NORMATIVE.search(text)
        if match is None:
            raise ValueError("normative term was not found")
        mutated["text"] = text[: match.start()] + "should" + text[match.end() :]
    elif operator == "negative_constraint_removal":
        mutated["text"] = _drop_clause(text, _NEGATIVE_CLAUSE)
    else:  # untestability
        mutated["testable"] = False

    validated = Criterion.model_validate(mutated).model_dump()
    if not validated["text"].strip() or validated == original:
        raise ValueError("mutation produced an empty or unchanged criterion")
    return validated


def build_mutation_case(request: MutationRequest) -> MutationCase:
    original = Criterion.model_validate(deepcopy(dict(request.criterion))).model_dump()
    mutated = mutate_criterion(original, request.operator)
    context = None if request.context is None else deepcopy(dict(request.context))
    return MutationCase(request.operator, original, mutated, context)


def _verdict_from_run(run: Mapping[str, Any]) -> str:
    if not isinstance(run, Mapping) or ("ok" in run and run["ok"] is not True):
        raise ValueError("runner did not return a successful run")
    record = run["record"] if "record" in run else run
    if not isinstance(record, Mapping):
        raise ValueError("emitted record is missing")
    verdict = record.get("verdict")
    if verdict not in {"CERTIFIED", "CONDITIONAL", "REJECTED", "PENDING"}:
        raise ValueError("emitted run has no valid verdict")
    if "exit_code" in run:
        code = run["exit_code"]
        if type(code) is not int or code not in (0, 1):
            raise ValueError("emitted run has no valid gate exit code")
        if (code == 0) != (verdict == "CERTIFIED"):
            raise ValueError("emitted verdict conflicts with the gate exit code")
    return verdict


def run_mutation_suite(requests: Sequence[MutationRequest], runner: Runner) -> dict[str, Any]:
    """Run all seven cases or return an honest, wholly unmeasured exposure."""
    unmeasured = false_certified_rate([])
    try:
        by_operator = {request.operator: request for request in requests}
        if len(requests) != len(OPERATORS) or set(by_operator) != set(OPERATORS):
            raise ValueError("suite requires exactly one case for each operator")

        # Preflight every transformation before invoking the runner even once.
        cases = [build_mutation_case(by_operator[operator]) for operator in OPERATORS]
        results = []
        for case in cases:
            verdict = _verdict_from_run(runner(case))
            results.append({"operator": case.operator, "verdict": verdict})

        exposure = false_certified_rate(results)
        Exposure.model_validate(exposure)
        return exposure
    except Exception:
        logger.exception("M13 mutation suite failed; exposure remains unmeasured")
        return unmeasured
