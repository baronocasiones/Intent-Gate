"""Persistence — docs/architecture.md §6 (SQLite WAL index + hash-sha256 artifacts).

Everything writes to tmp_path — never the repo working tree (no ./attestation.db,
no ./artifacts pollution; the pre-commit cleanliness gate depends on this).
"""
import hashlib
import json
from datetime import datetime
from pathlib import Path

import pytest

import app.db as db_mod
import app.store.artifacts as artifacts_mod
from app.db import (
    SCHEMA,
    get_db,
    get_run,
    list_runs,
    now_iso,
    save_run,
    set_status,
)

ROOT = Path(__file__).resolve().parents[2]
CONTRACTS = ROOT / "contracts"

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


def test_write_artifact_hash_independent_of_key_order(tmp_path, monkeypatch):
    """sort_keys=True *inside write_artifact*: two payloads whose dicts are
    inserted in opposite orders must emit the same digest. Exercised through
    the product — this test originally hashed two dicts directly with
    hashlib and therefore guarded nothing (Session 22 verification finding A)."""
    monkeypatch.setattr(artifacts_mod, "ARTIFACT_DIR", str(tmp_path))
    p1 = artifacts_mod.write_artifact("ord-a", {"x": 1, "y": 2})
    p2 = artifacts_mod.write_artifact("ord-b", {"y": 2, "x": 1})
    h1 = json.loads(Path(p1).read_text())["sha256"]
    h2 = json.loads(Path(p2).read_text())["sha256"]
    assert h1 == h2  # insertion order cannot reach the digest
    assert h1 == hashlib.sha256(
        json.dumps({"x": 1, "y": 2}, sort_keys=True).encode()
    ).hexdigest()


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


@pytest.mark.parametrize(
    "url,expected",
    [
        ("sqlite:///./attestation.db", "./attestation.db"),
        ("sqlite:////abs/x.db", "/abs/x.db"),
        ("sqlite:///rel.db", "rel.db"),
        ("plain/path.db", "plain/path.db"),
        ("./attestation.db", "./attestation.db"),
    ],
)
def test_sqlite_path_strips_scheme_variants(url, expected):
    assert db_mod._sqlite_path(url) == expected


def test_get_db_defaults_to_database_url(tmp_path, monkeypatch):
    """AC 4: with no explicit path, the env URL selects the file. Patched on
    the consumer module (Convention 2) — config.py itself is M11's file."""
    db_path = tmp_path / "from-env.db"
    monkeypatch.setattr(db_mod, "DATABASE_URL", f"sqlite:///{db_path}")
    conn = get_db()
    try:
        save_run(conn, "run-env", "queued")
        assert get_run(conn, "run-env")["status"] == "queued"
    finally:
        conn.close()
    assert db_path.exists()


def test_get_db_explicit_path_wins_over_env(tmp_path, monkeypatch):
    monkeypatch.setattr(
        db_mod, "DATABASE_URL", f"sqlite:///{tmp_path / 'env.db'}"
    )
    explicit = str(tmp_path / "explicit.db")
    conn = get_db(explicit)
    try:
        save_run(conn, "run-exp", "queued")
    finally:
        conn.close()
    # The env file was never even created — the explicit path won outright.
    assert not (tmp_path / "env.db").exists()
    conn = get_db(explicit)
    try:
        assert get_run(conn, "run-exp") is not None
    finally:
        conn.close()


def test_now_iso_is_utc_aware_parseable_str():
    ts = now_iso()
    assert isinstance(ts, str)
    parsed = datetime.fromisoformat(ts)
    assert parsed.tzinfo is not None
    assert parsed.utcoffset().total_seconds() == 0


def test_now_iso_orders_lexicographically():
    first, second = now_iso(), now_iso()
    assert first <= second
    assert first.endswith("+00:00") and second.endswith("+00:00")


def test_schema_includes_created_at_index(tmp_path):
    """`GET /api/runs` lists newest-first — the index keeps it an index scan.
    An index is not a table, so the single-table guard above is untouched.
    Pins the index's *target column* too: `index_list` only shows names, so
    without `index_info` a mutation to `ON runs(id)` would pass
    (Session 22 verification finding B)."""
    conn = get_db(str(tmp_path / "t.db"))
    try:
        names = {row[1] for row in conn.execute("PRAGMA index_list(runs)")}
        assert "idx_runs_created_at" in names
        cols = {row[2] for row in conn.execute("PRAGMA index_info(idx_runs_created_at)")}
        assert "created_at" in cols
    finally:
        conn.close()


def test_save_run_commits_so_row_survives_reopen(tmp_path):
    """The commit lives in `save_run`, not the caller — a reopen must see it."""
    path = str(tmp_path / "t.db")
    conn = get_db(path)
    save_run(conn, "run-1a2b3c4d", "queued")
    conn.close()
    conn = get_db(path)
    try:
        row = get_run(conn, "run-1a2b3c4d")
        assert row is not None
        assert row["status"] == "queued"
        assert row["artifact_path"] is None
    finally:
        conn.close()


def test_save_run_created_at_is_iso8601_string(tmp_path):
    """AC 2 (+ M17's missing-coverage item): `created_at` is a TEXT ISO-8601
    string. A mutation-lab run showed nothing pinned the *type*, so this pins
    it — including the float it must never become."""
    conn = get_db(str(tmp_path / "t.db"))
    try:
        save_run(conn, "run-ts", "queued")
        ts = conn.execute(
            "SELECT created_at FROM runs WHERE id = ?", ("run-ts",)
        ).fetchone()[0]
    finally:
        conn.close()
    assert isinstance(ts, str)
    assert not isinstance(ts, float)
    assert datetime.fromisoformat(ts).utcoffset().total_seconds() == 0


def test_save_run_accepts_artifact_path(tmp_path):
    conn = get_db(str(tmp_path / "t.db"))
    try:
        save_run(conn, "run-ap", "running", artifact_path="artifacts/run-ap.json")
        assert get_run(conn, "run-ap")["artifact_path"] == "artifacts/run-ap.json"
    finally:
        conn.close()


def test_set_status_flips_row_and_commits(tmp_path):
    path = str(tmp_path / "t.db")
    conn = get_db(path)
    save_run(conn, "run-flip", "queued")
    assert set_status(conn, "run-flip", "running") == 1
    conn.close()
    conn = get_db(path)
    try:
        assert get_run(conn, "run-flip")["status"] == "running"
    finally:
        conn.close()


def test_set_status_keeps_path_unless_overwritten(tmp_path):
    conn = get_db(str(tmp_path / "t.db"))
    try:
        save_run(conn, "run-sp", "queued", artifact_path="old.json")
        assert set_status(conn, "run-sp", "running") == 1
        # None keeps the existing pointer — only an explicit path overwrites.
        assert get_run(conn, "run-sp")["artifact_path"] == "old.json"
        assert (
            set_status(conn, "run-sp", "rejected", artifact_path="new.json") == 1
        )
        assert get_run(conn, "run-sp")["artifact_path"] == "new.json"
    finally:
        conn.close()


def test_set_status_unknown_run_returns_zero(tmp_path):
    """Rowcount 0 = the run does not exist. M10 must read that as a blocking
    failure (rule 6), never as a pass."""
    conn = get_db(str(tmp_path / "t.db"))
    try:
        assert set_status(conn, "ghost", "certified") == 0
    finally:
        conn.close()


def test_get_run_returns_none_for_unknown_id(tmp_path):
    conn = get_db(str(tmp_path / "t.db"))
    try:
        assert get_run(conn, "nope") is None
    finally:
        conn.close()


def test_list_runs_newest_first(tmp_path):
    conn = get_db(str(tmp_path / "t.db"))
    try:
        save_run(conn, "run-aaa", "queued")
        save_run(conn, "run-bbb", "queued")
        save_run(conn, "run-ccc", "queued")
        assert [r["id"] for r in list_runs(conn)] == [
            "run-ccc",
            "run-bbb",
            "run-aaa",
        ]
    finally:
        conn.close()


def test_list_runs_respects_limit(tmp_path):
    conn = get_db(str(tmp_path / "t.db"))
    try:
        for i in range(3):
            save_run(conn, f"run-l{i}", "queued")
        assert len(list_runs(conn, limit=2)) == 2
    finally:
        conn.close()


def test_list_runs_orders_by_created_at_not_id(tmp_path, monkeypatch):
    """The column driving the sort must be `created_at`, not `id`.

    `test_list_runs_newest_first` saves ids that sort in insertion order, so
    its expectation is satisfied by `created_at DESC`, by `id DESC`, and by
    the tiebreak alone — it cannot tell them apart. Here the clock is mocked
    and the ids are reverse-sorted, so the three orderings disagree
    deterministically (no microsecond race): only a genuine
    `created_at DESC` yields [run-aaa, run-zzz]
    (Session 22 verification finding C).
    """
    stamps = iter(
        ["2026-01-01T00:00:00.000001+00:00", "2026-01-01T00:00:00.000002+00:00"]
    )
    monkeypatch.setattr(db_mod, "now_iso", lambda: next(stamps))
    conn = get_db(str(tmp_path / "t.db"))
    try:
        save_run(conn, "run-zzz", "queued")  # older stamp, later id sort position
        save_run(conn, "run-aaa", "queued")  # newer stamp
        assert [r["id"] for r in list_runs(conn)] == ["run-aaa", "run-zzz"]
    finally:
        conn.close()


def test_write_artifact_prev_digest_defaults_to_none_and_stays_out_of_digest(
    tmp_path, monkeypatch
):
    """AC 3 + the D8 seam: the digest still covers the payload only, and the
    provisional `prev_digest` rides alongside as `None`."""
    monkeypatch.setattr(artifacts_mod, "ARTIFACT_DIR", str(tmp_path))
    payload = {"run_id": "r5", "v": 1}
    data = json.loads(
        Path(artifacts_mod.write_artifact("r5", payload)).read_text()
    )
    assert data["prev_digest"] is None
    assert data["sha256"] == hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode()
    ).hexdigest()


def test_write_artifact_threads_prev_digest(tmp_path, monkeypatch):
    monkeypatch.setattr(artifacts_mod, "ARTIFACT_DIR", str(tmp_path))
    first = json.loads(
        Path(artifacts_mod.write_artifact("chain-a", {"n": 1})).read_text()
    )
    second = json.loads(
        Path(
            artifacts_mod.write_artifact(
                "chain-b", {"n": 2}, prev_digest=first["sha256"]
            )
        ).read_text()
    )
    assert second["prev_digest"] == first["sha256"]
    # The chain link does not enter the digest — per-file hashing stays
    # authoritative until D8 is ratified.
    assert second["sha256"] == hashlib.sha256(
        json.dumps({"n": 2}, sort_keys=True).encode()
    ).hexdigest()


def test_write_artifact_store_keys_win_over_payload(tmp_path, monkeypatch):
    """The envelope is payload-first, store-keys-last: a payload carrying
    `sha256`/`prev_digest` cannot forge the store's own keys."""
    monkeypatch.setattr(artifacts_mod, "ARTIFACT_DIR", str(tmp_path))
    payload = {"x": 1, "sha256": "forged", "prev_digest": "forged"}
    data = json.loads(
        Path(artifacts_mod.write_artifact("rx", payload)).read_text()
    )
    expected = hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode()
    ).hexdigest()
    assert data["sha256"] == expected
    assert data["sha256"] != "forged"
    assert data["prev_digest"] is None
    assert data["x"] == 1


def test_prev_digest_is_provisional_until_m1_contracts_the_envelope():
    """D15: the envelope is uncontracted, so `prev_digest` is PROPOSED. The
    day M1 adds an envelope contract this fails — ratify or remove the key.
    (The INLINE_MIRRORS pattern from Session 18.)"""
    envelope_contracts = sorted(
        p.name for p in CONTRACTS.glob("*.schema.json") if "envelope" in p.stem
    )
    assert envelope_contracts == [], (
        "an envelope contract exists "
        f"({envelope_contracts}) — ratify or remove the PROPOSED "
        "`prev_digest` seam (modules.md D15)"
    )
