"""LLM layer — docs/architecture.md §7 (mock mode + loud live failure).

Hard rule: ZERO live watsonx.ai calls in tests. The live client is exercised
only up to its deliberate failure points, with the API key patched at the
consumer-module level (config binds env at import time — patching os.environ
after import would be a no-op).

Session 21 adds the selector: `select_client()` closes §11.9, where `MOCK_LLM`
was parsed and read by nothing. Its docstring states the two limits plainly —
no product code calls it yet, and it selects rather than falls back — and
`test_the_selector_is_the_only_sanctioned_path` is the guard that keeps the
first limit from quietly becoming untrue.
"""
import inspect
import json
from pathlib import Path

import pytest

from app import config
from app.llm import MOCK_CLIENT, LIVE_CLIENT, mock_client, select_client, watsonx_client

LLM_DIR = Path(__file__).resolve().parents[1] / "app" / "llm"
APP_DIR = LLM_DIR.parent


def test_llm_package_has_no_third_model_client():
    """§7: 'No other model call sites exist' — only mock + watsonx."""
    py_files = {p.name for p in LLM_DIR.glob("*.py")}
    assert py_files == {"__init__.py", "mock_client.py", "watsonx_client.py"}


# --- the selector (Session 21) ------------------------------------------------


def test_select_client_returns_the_mock_client_in_mock_mode(monkeypatch):
    """Patched on the *consumer* module, per test-suite.md Convention 2.

    This is also the only reason the selector is testable at all: `config`
    binds the environment at import, so a `setenv` after import changes nothing
    and the switch would be untestable without this lever.
    """
    monkeypatch.setattr("app.llm.MOCK_LLM", True)
    assert select_client() is MOCK_CLIENT


def test_select_client_returns_the_live_client_when_not_in_mock_mode(monkeypatch):
    monkeypatch.setattr("app.llm.MOCK_LLM", False)
    assert select_client() is LIVE_CLIENT


def test_select_client_agrees_with_config_rather_than_with_the_environment(monkeypatch):
    """Whichever way this machine is configured, the two must not disagree.

    Deliberately env-independent: a developer running with `MOCK_LLM=true` should
    not see this fail. The *default* being live is pinned separately by
    `test_config.py::test_defaults_match_docs`; what matters here is that the
    selector reads the same binding config parsed, so the switch cannot report
    one mode while behaving as another.
    """
    assert select_client() is (MOCK_CLIENT if config.MOCK_LLM else LIVE_CLIENT)


def test_select_client_takes_no_arguments():
    """No override parameter, and that is the design.

    `select_client(mock=False)` would be a second way to choose that no config
    governs and no environment can set — which is how a "single sanctioned path"
    becomes two paths, the second one undocumented. Pinned by signature so the
    escape hatch cannot be added without failing here.
    """
    assert inspect.signature(select_client).parameters == {}


def test_select_client_offers_exactly_two_distinct_clients():
    assert MOCK_CLIENT is mock_client
    assert LIVE_CLIENT is watsonx_client
    assert MOCK_CLIENT is not LIVE_CLIENT
    for client in (MOCK_CLIENT, LIVE_CLIENT):
        assert callable(client.complete), f"{client.__name__} has no complete()"


async def test_the_selected_client_is_usable_end_to_end(monkeypatch):
    """Selecting and calling are one path: what comes back is a parsable string."""
    monkeypatch.setattr("app.llm.MOCK_LLM", True)
    parsed = json.loads(await select_client().complete("adjudicate AC-1"))
    assert parsed["verdict"] == "PENDING"


def test_the_selector_is_the_only_sanctioned_path():
    """§7's real claim, made mechanical: nothing reaches a client except the switch.

    `docs/intent-attestation-gate.md` §3.3 and `architecture.md` §7 both say all
    model reasoning goes through one path. Until now that was prose. This walks
    `backend/app` and fails if any module outside `llm/` names either client —
    so M5 or M7b cannot quietly import `mock_client` directly and bypass the
    switch, which would leave the demo unable to say which client ran.

    Currently vacuous: no product module imports a client, because no stage
    calls one yet. That is the state `llm/__init__.py`'s first stated limit
    describes, and this guard is what stops it becoming untrue quietly. Proven
    to bite by the Session 21 mutation battery, which injects exactly such an
    import into a gate.
    """
    offenders = []
    for path in sorted(APP_DIR.rglob("*.py")):
        if LLM_DIR in path.parents:
            continue
        text = path.read_text(encoding="utf-8")
        for name in ("mock_client", "watsonx_client"):
            if name in text:
                offenders.append(f"{path.relative_to(APP_DIR)} references {name}")
    assert not offenders, (
        "model clients must be reached through select_client(), not imported "
        f"directly: {offenders}"
    )


async def test_mock_client_is_deterministic():
    r1 = await mock_client.complete("any prompt")
    r2 = await mock_client.complete("a different prompt")
    assert r1 == r2


async def test_mock_client_response_is_valid_json_verdict():
    out = await mock_client.complete("adjudicate AC-1")
    parsed = json.loads(out)
    assert parsed["verdict"] == "PENDING"
    assert "mock" in parsed["rationale"]
    assert "no live call" in parsed["rationale"]


async def test_mock_client_ignores_max_tokens():
    assert await mock_client.complete("p", max_tokens=1) == (
        await mock_client.complete("p", max_tokens=4096)
    )


async def test_watsonx_without_key_fails_loud(monkeypatch):
    """§7: live path without WATSONX_API_KEY raises RuntimeError — never silent."""
    monkeypatch.setattr(watsonx_client, "WATSONX_API_KEY", "")
    with pytest.raises(RuntimeError, match="WATSONX_API_KEY"):
        await watsonx_client.complete("prompt")


async def test_watsonx_with_key_pending_spike(monkeypatch):
    """§11.4 characterization: past the key check it raises NotImplementedError
    (IAM exchange + call pattern land with the research spike). Flips when
    the spike lands — update deliberately, adding a live-marked test then."""
    monkeypatch.setattr(watsonx_client, "WATSONX_API_KEY", "test-key-not-real")
    with pytest.raises(NotImplementedError):
        await watsonx_client.complete("prompt")


async def test_watsonx_with_key_makes_no_network_call(monkeypatch):
    """NotImplementedError must fire before any HTTP *request* — constructing
    a client is I/O-free; sending is not. Prove send() is never reached."""
    monkeypatch.setattr(watsonx_client, "WATSONX_API_KEY", "test-key-not-real")
    calls = {"send": 0}

    class _SpyClient:
        def __init__(self, *a, **kw):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

        async def send(self, *a, **kw):
            calls["send"] += 1
            raise AssertionError("network request attempted — live call made")

    monkeypatch.setattr(watsonx_client.httpx, "AsyncClient", _SpyClient)
    with pytest.raises(NotImplementedError):
        await watsonx_client.complete("prompt")
    assert calls["send"] == 0
