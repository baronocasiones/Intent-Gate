"""Read-only attestor policy — Figure 6 attestor box + docs/architecture.md §8.

The read-only grant set is the product's differentiator (governance by
construction). These tests are load-bearing: they fail if anyone widens the
policy — never weaken it in demo shortcuts (standing convention).
"""
import pytest

from app.attestor.policy import DENIES, GRANTS, assert_read_only


def test_grants_match_figure_6_attestor_box():
    assert GRANTS == frozenset({"read", "subagent", "skill", "workflow"})


def test_denies_edit_and_execute():
    assert DENIES == frozenset({"edit", "execute"})


def test_grants_and_denies_disjoint():
    """The policy must never overlap — a cap cannot be granted and denied."""
    assert set(GRANTS) & set(DENIES) == set()


def test_exact_policy_passes():
    assert_read_only(GRANTS)  # must not raise


def test_leaked_edit_raises_permission_error():
    with pytest.raises(PermissionError, match="denied caps granted"):
        assert_read_only(GRANTS | {"edit"})


def test_leaked_execute_raises_permission_error():
    with pytest.raises(PermissionError, match="denied caps granted"):
        assert_read_only(GRANTS | {"execute"})


def test_missing_grant_fails_closed():
    """Incomplete policy fails closed, not open (§8: fails on leak OR gap)."""
    with pytest.raises(PermissionError, match="missing"):
        assert_read_only({"read"})


def test_empty_grants_fail_closed():
    with pytest.raises(PermissionError):
        assert_read_only(frozenset())


def test_edit_only_fails_on_leak_first():
    """Leak is checked before incompleteness — error names the leak."""
    with pytest.raises(PermissionError, match="denied caps granted"):
        assert_read_only({"edit"})
