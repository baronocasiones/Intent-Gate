"""API surface — docs/architecture.md §5 (Today column).

Characterization of the live/stub endpoints. Stub responses flip when the
store wiring lands (§11.2) — update these deliberately alongside the code.
"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app import db as db_mod
from app.main import app, mount_dashboard
from app.orchestrator.pipeline import enqueue_run, run_pipeline

client = TestClient(app)


def test_health_is_live():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"ok": True, "service": "intent-attestation-gate"}


def test_route_table_matches_documented_surface():
    """All five §5 routes must exist: health, webhook, runs list/detail, metrics."""
    paths = {getattr(route, "path", None) for route in app.routes}
    expected = {
        "/health",
        "/webhooks/github",
        "/api/runs",
        "/api/runs/{run_id}",
        "/api/metrics",
    }
    assert expected <= paths, f"missing routes: {expected - paths}"


def test_webhook_accepts_injected_payload_and_queues_run():
    """Same endpoint for real webhooks and hand-injected demo bodies (§4.1)."""
    res = client.post("/webhooks/github", json={"action": "opened", "pr": 142})
    assert res.status_code == 200
    body = res.json()
    assert body["run_id"].startswith("run-")
    assert len(body["run_id"]) == len("run-") + 8
    assert body["status"] == "queued"


def test_webhook_run_ids_differ_per_call():
    ids = set()
    for _ in range(5):
        res = client.post("/webhooks/github", json={"n": 1})
        ids.add(res.json()["run_id"])
    assert len(ids) == 5


def test_api_runs_list_serves_newest_first(monkeypatch):
    """R2: the index, newest-first — the old `{"runs": []}` stub is gone."""
    stamps = iter([
        "2026-09-27T10:00:00+00:00",
        "2026-09-27T10:00:01+00:00",
        "2026-09-27T10:00:02+00:00",
    ])
    monkeypatch.setattr(db_mod, "now_iso", lambda: next(stamps))
    ids = [enqueue_run({"n": i}) for i in range(3)]
    res = client.get("/api/runs")
    assert res.status_code == 200
    runs = res.json()["runs"]
    assert [r["run_id"] for r in runs] == ids[::-1]
    assert all(set(r) == {"run_id", "status"} for r in runs)
    assert all(r["status"] == "queued" for r in runs)


def test_api_run_detail_unknown_id_is_404():
    """R2: today the endpoint echoed any id with `status: "pending"` — a stub,
    not a lookup. Unknown ids now 404."""
    res = client.get("/api/runs/run-doesnotexist")
    assert res.status_code == 404


def test_api_run_detail_queued_run_has_no_artifact_yet():
    run_id = enqueue_run({"action": "opened"})
    res = client.get(f"/api/runs/{run_id}")
    assert res.status_code == 200
    body = res.json()
    assert body["run_id"] == run_id
    assert body["status"] == "queued"
    assert body["verdicts"] == [] and body["measured"] is False
    assert body["artifact_path"] is None


def test_api_run_detail_executed_run_serves_row_plus_artifact():
    """Row lifecycle status (D-e) + the chain's artifact, with its pointer."""
    payload = {"action": "opened", "pr": 142,
               "requirement": "AC-1: refunds over $100 require supervisor approval."}
    run_id = enqueue_run(payload)
    run_pipeline(payload, run_id)
    res = client.get(f"/api/runs/{run_id}")
    assert res.status_code == 200
    body = res.json()
    assert body["run_id"] == run_id
    assert body["status"] == "pending"
    assert body["measured"] is False
    assert isinstance(body["verdicts"], list)
    assert body["artifact_path"] is not None
    assert body["artifact_path"].endswith(f"{run_id}.json")


def test_dist_path_climbs_two_levels_to_repo_frontend():
    """Pins M15's _dist fix: three levels land outside the project."""
    from app import main as main_mod
    expected = Path(main_mod.__file__).resolve().parents[2] / "frontend" / "dist"
    assert Path(main_mod._dist) == expected


def test_dashboard_mount_serves_dist_when_present(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<h1>gate</h1>")
    fresh = FastAPI()
    assert mount_dashboard(fresh, str(dist)) is True
    res = TestClient(fresh).get("/")
    assert res.status_code == 200
    assert "gate" in res.text


def test_dashboard_mount_absent_dist_mounts_nothing(tmp_path):
    fresh = FastAPI()
    before = len(fresh.routes)
    assert mount_dashboard(fresh, str(tmp_path / "nope")) is False
    assert len(fresh.routes) == before


def test_api_metrics_stub_shape():
    """§5: stub must already carry the exposure contract's three keys."""
    res = client.get("/api/metrics")
    assert res.status_code == 200
    body = res.json()
    assert set(body) == {"false_certified_rate", "measured", "by_operator"}
    assert body["false_certified_rate"] is None
    assert body["measured"] is False
    assert body["by_operator"] == {}


def test_app_title_and_version_match_docs():
    assert app.title == "Intent Attestation Gate"
    assert app.version == "0.1.0"
