"""LLM layer — docs/architecture.md §7 (mock mode + loud live failure).

Hard rule: ZERO live watsonx.ai calls in tests. The live client is exercised
only up to its deliberate failure points, with the API key patched at the
consumer-module level (config binds env at import time — patching os.environ
after import would be a no-op).
"""
import json
from pathlib import Path

import pytest

from app.llm import mock_client, watsonx_client

LLM_DIR = Path(__file__).resolve().parents[1] / "app" / "llm"


def test_llm_package_has_no_third_model_client():
    """§7: 'No other model call sites exist' — only mock + watsonx."""
    py_files = {p.name for p in LLM_DIR.glob("*.py")}
    assert py_files == {"__init__.py", "mock_client.py", "watsonx_client.py"}


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
