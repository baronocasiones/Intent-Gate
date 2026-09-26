"""Runtime config — docs/architecture.md §3 (config row) + §7.

config.py binds os.getenv() at import time, so these tests reload the module
under a controlled environment and restore the original state afterward —
a stray developer .env must never change suite results.
"""
import importlib
import os
from pathlib import Path

import pytest

import app.config as config

ENV_VARS = (
    "WATSONX_API_KEY",
    "WATSONX_PROJECT_ID",
    "WATSONX_URL",
    "DATABASE_URL",
    "MOCK_LLM",
    "ARTIFACT_DIR",
)

# Snapshot of the real environment before any test touches it.
_SNAPSHOT = {var: os.environ.get(var) for var in ENV_VARS}


@pytest.fixture(autouse=True)
def restore_config_after_test():
    """Restore real env values + reload config so no test leaks state."""
    yield
    for var, value in _SNAPSHOT.items():
        if value is None:
            os.environ.pop(var, None)
        else:
            os.environ[var] = value
    importlib.reload(config)


def _clear_env(monkeypatch):
    for var in ENV_VARS:
        monkeypatch.delenv(var, raising=False)


def test_defaults_match_docs(monkeypatch):
    _clear_env(monkeypatch)
    importlib.reload(config)
    assert config.WATSONX_API_KEY == ""
    assert config.WATSONX_PROJECT_ID == ""
    assert config.WATSONX_URL == "https://us-south.ml.cloud.ibm.com"
    assert config.DATABASE_URL == "sqlite:///./attestation.db"
    assert config.ARTIFACT_DIR == "./artifacts"
    assert config.MOCK_LLM is False  # opt-in fixture mode (§7)


def test_env_overrides_flow_through(monkeypatch):
    _clear_env(monkeypatch)
    monkeypatch.setenv("WATSONX_URL", "https://example.invalid")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./other.db")
    monkeypatch.setenv("ARTIFACT_DIR", "/tmp/somewhere")
    importlib.reload(config)
    assert config.WATSONX_URL == "https://example.invalid"
    assert config.DATABASE_URL == "sqlite:///./other.db"
    assert config.ARTIFACT_DIR == "/tmp/somewhere"


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("true", True),
        ("True", True),
        ("TRUE", True),
        ("false", False),
        ("1", False),  # only the literal "true" (any case) enables mock mode
        ("", False),
    ],
)
def test_mock_llm_parsing(monkeypatch, raw, expected):
    _clear_env(monkeypatch)
    monkeypatch.setenv("MOCK_LLM", raw)
    importlib.reload(config)
    assert config.MOCK_LLM is expected


def test_watsonx_api_key_survives_reload(monkeypatch):
    _clear_env(monkeypatch)
    monkeypatch.setenv("WATSONX_API_KEY", "sekret")
    importlib.reload(config)
    assert config.WATSONX_API_KEY == "sekret"


def test_secrets_never_hardcoded_in_config_source():
    """§3: secrets come from env only; .env is gitignored — no literals here."""
    text = Path(config.__file__).read_text(encoding="utf-8")
    assert "os.getenv" in text  # every setting is env-driven
    # No real-looking key material committed in config:
    assert "apikey-" not in text
    assert "IBM_" not in text
    assert "sk-" not in text
