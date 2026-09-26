"""API surface — docs/architecture.md §5 (Today column).

Characterization of the live/stub endpoints. Stub responses flip when the
store wiring lands (§11.2) — update these deliberately alongside the code.
"""
from fastapi.testclient import TestClient

from app.main import app

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


def test_api_runs_list_is_stub():
    res = client.get("/api/runs")
    assert res.status_code == 200
    assert res.json() == {"runs": []}


def test_api_run_detail_is_stub_echoing_id():
    res = client.get("/api/runs/run-abcdef12")
    assert res.status_code == 200
    assert res.json() == {"run_id": "run-abcdef12", "status": "pending"}


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
