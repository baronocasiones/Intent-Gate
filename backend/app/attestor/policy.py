"""Read-only verifier policy.
GRANTS: read, subagent fan-out (OS processes), skill, workflow.
WITHHOLDS: edit, execute — structurally incapable of modifying what it verifies.
Never weaken this in demo shortcuts.
"""

GRANTS = frozenset({"read", "subagent", "skill", "workflow"})
DENIES = frozenset({"edit", "execute"})


def assert_read_only(granted: frozenset) -> None:
    leaked = set(granted) & set(DENIES)
    if leaked:
        raise PermissionError(f"attestor policy violation — denied caps granted: {sorted(leaked)}")
    missing = set(GRANTS) - set(granted)
    if missing:
        raise PermissionError(f"attestor policy incomplete — missing: {sorted(missing)}")
