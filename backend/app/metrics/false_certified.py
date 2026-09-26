"""FALSE CERTIFIED RATE = P(CERTIFIED | spec violation present).
Seven spec-mutation operator classes (Session 6 record):
boundary_drop, comparison_inversion, threshold_weakening, error_path_deletion,
normative_demotion, negative_constraint_removal, untestability.
"""

OPERATORS = (
    "boundary_drop",
    "comparison_inversion",
    "threshold_weakening",
    "error_path_deletion",
    "normative_demotion",
    "negative_constraint_removal",
    "untestability",
)


def false_certified_rate(results: list[dict]) -> dict:
    per_op: dict[str, dict[str, int]] = {op: {"certified": 0, "total": 0} for op in OPERATORS}
    for r in results:
        op = r.get("operator")
        if op not in per_op:
            continue
        per_op[op]["total"] += 1
        if r.get("verdict") == "CERTIFIED":
            per_op[op]["certified"] += 1
    total = sum(v["total"] for v in per_op.values())
    certified = sum(v["certified"] for v in per_op.values())
    rate = (certified / total) if total else None
    return {"false_certified_rate": rate, "measured": total > 0, "by_operator": per_op}
