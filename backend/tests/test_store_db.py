"""Persistence — docs/architecture.md §6 (SQLite WAL index + hash-sha256 artifacts).

Everything writes to tmp_path — never the repo working tree (no ./attestation.db,
no ./artifacts pollution; the pre-commit cleanliness gate depends on this).
"""
import hashlib
import json
from pathlib import Path

import app.store.artifacts as artifacts_mod
from app.db import SCHEMA, get_db

EXPECTED_RUN_COLS = {"id", "status", "created_at", "artifact_path"}


def test_schema_creates_single_runs_table():
    assert "CREATE TABLE IF NOT EXISTS runs" in SCHEMA
    assert SCHEMA.count("CREATE TABLE") == 1  # §6: one table today


def test_get_db_sets_wal_mode(tmp_path):
    conn = get_db(str(tmp_path / "t.db"))
    try:
        mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
        assert mode == "wal"
    finally:
        conn.close()


def test_get_db_creates_runs_table_with_expected_columns(tmp_path):
    conn = get_db(str(tmp_path / "t.db"))
    try:
        cols = {row[1] for row in conn.execute("PRAGMA table_info(runs)")}
        assert cols == EXPECTED_RUN_COLS
    finally:
        conn.close()


def test_get_db_is_idempotent(tmp_path):
    """CREATE IF NOT EXISTS — opening twice must not fail."""
    path = str(tmp_path / "t.db")
    c1 = get_db(path)
    c1.close()
    c2 = get_db(path)
    c2.close()


def test_write_artifact_sha256_is_hash_of_sorted_body(tmp_path, monkeypatch):
    monkeypatch.setattr(artifacts_mod, "ARTIFACT_DIR", str(tmp_path))
    payload = {"run_id": "r1", "b": 2, "a": 1}
    path = artifacts_mod.write_artifact("r1", payload)

    expected = hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode()
    ).hexdigest()

    data = json.loads(Path(path).read_text())
    assert data["sha256"] == expected
    # payload merged alongside the digest (envelope + artifact pointer, §6)
    assert data["run_id"] == "r1"
    assert data["a"] == 1
    assert data["b"] == 2


def test_write_artifact_hash_independent_of_key_order():
    """sort_keys=True means dict insertion order cannot change the digest."""
    a = {"x": 1, "y": 2}
    b = {"y": 2, "x": 1}
    ha = hashlib.sha256(json.dumps(a, sort_keys=True).encode()).hexdigest()
    hb = hashlib.sha256(json.dumps(b, sort_keys=True).encode()).hexdigest()
    assert ha == hb


def test_write_artifact_lands_under_configured_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(artifacts_mod, "ARTIFACT_DIR", str(tmp_path))
    path = artifacts_mod.write_artifact("r2", {})
    assert Path(path).parent == tmp_path
    assert Path(path).name == "r2.json"
    assert Path(path).exists()


def test_write_artifact_creates_missing_directories(tmp_path, monkeypatch):
    target = tmp_path / "nested" / "deep"
    monkeypatch.setattr(artifacts_mod, "ARTIFACT_DIR", str(target))
    path = artifacts_mod.write_artifact("r3", {"k": "v"})
    assert Path(path).exists()
    assert Path(path).parent == target


def test_write_artifact_creates_valid_json(tmp_path, monkeypatch):
    monkeypatch.setattr(artifacts_mod, "ARTIFACT_DIR", str(tmp_path))
    path = artifacts_mod.write_artifact("r4", {"nested": {"list": [1, 2, 3]}})
    data = json.loads(Path(path).read_text())
    assert data["nested"] == {"list": [1, 2, 3]}
    assert "sha256" in data
