"""API surface — docs/architecture.md §5 (as of the M15 core slice).

The three stub-response tests were flipped in the same change that replaced
the stubs (modules.md rule 7): runs list/detail now hit the runs table (with
404 for unknown ids), metrics aggregates M13's function over the artifact
store, and the static mount is provable instead of silently dead.
"""
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.routing import Mount

from app import main as main_mod
from app.main import app
from app.metrics.false_certified import OPERATORS
from app.orchestrator.pipeline import enqueue_run, run_pipeline
from app.store import artifacts

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


def test_webhook_persists_queued_row_visible_in_list():
    """enqueue_run persists before submitting, so the run is listable while
    still `queued` (the worker is not running under this client — module-level
    TestClient does not run the lifespan)."""
    res = client.post("/webhooks/github", json={"action": "opened", "pr": 142})
    run_id = res.json()["run_id"]

    runs = client.get("/api/runs").json()["runs"]
    row = next(r for r in runs if r["run_id"] == run_id)
    assert row["status"] == "queued"
    assert row["artifact_path"] is None


def test_api_runs_list_starts_empty():
    res = client.get("/api/runs")
    assert res.status_code == 200
    assert res.json() == {"runs": []}


def test_api_runs_list_returns_newest_first():
    ids = [enqueue_run({"n": i}) for i in range(3)]
    res = client.get("/api/runs")
    assert res.status_code == 200
    runs = res.json()["runs"]
    # newest first (rowid tiebreak keeps same-timestamp inserts ordered)
    assert [r["run_id"] for r in runs] == list(reversed(ids))
    for row in runs:
        assert set(row) == {"run_id", "status", "created_at", "artifact_path"}
        assert row["status"] == "queued"
        # M14's type pin: created_at is an ISO-8601 STRING (column is TEXT).
        datetime.fromisoformat(row["created_at"])


def test_api_run_detail_404s_for_unknown_id():
    """The stub used to echo any id with status "pending" — a lookup must 404."""
    res = client.get("/api/runs/run-abcdef12")
    assert res.status_code == 404
    assert "run-abcdef12" in res.json()["detail"]


def test_api_run_detail_returns_envelope_with_artifact_pointer():
    payload = {"pr": 142}
    run_id = enqueue_run(payload)
    run_pipeline(payload, run_id=run_id)

    res = client.get(f"/api/runs/{run_id}")
    assert res.status_code == 200
    body = res.json()
    # run.schema.json's four keys are all present
    assert {"run_id", "status", "verdicts", "measured"} <= set(body)
    assert body["run_id"] == run_id
    # stub verdict PENDING -> lowercased D9 lifecycle value (pipeline shim)
    assert body["status"] == "pending"
    # M8 not landed: no per-criterion verdicts yet, honestly empty/false
    assert body["verdicts"] == []
    assert body["measured"] is False
    # fail-closed merge signal (§1.5)
    assert body["exit_code"] == 1
    # artifact pointer: path under the isolated dir + 64-hex digest
    assert body["artifact"]["path"].endswith(f"{run_id}.json")
    assert Path(body["artifact"]["path"]).is_file()
    assert len(body["artifact"]["sha256"]) == 64


def test_api_run_detail_before_emit_has_no_artifact():
    run_id = enqueue_run({"pr": 1})
    res = client.get(f"/api/runs/{run_id}")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "queued"
    assert body["artifact"] is None
    assert body["exit_code"] is None


def test_api_metrics_unmeasured_by_default():
    """§5 + 1.7: null rate / measured false / all seven operator buckets —
    never 0.0 before data exists."""
    res = client.get("/api/metrics")
    assert res.status_code == 200
    body = res.json()
    assert set(body) == {"false_certified_rate", "measured", "by_operator"}
    assert body["false_certified_rate"] is None
    assert body["measured"] is False
    assert body["by_operator"] == {
        op: {"certified": 0, "total": 0} for op in OPERATORS
    }


def test_api_metrics_aggregates_stored_mutation_results():
    """M13 wiring point: artifacts carrying {operator, verdict} are aggregated
    by false_certified_rate(); run artifacts (no operator key) are skipped."""
    artifacts.write_artifact("mut-a", {"operator": "boundary_drop", "verdict": "CERTIFIED"})
    artifacts.write_artifact("mut-b", {"operator": "boundary_drop", "verdict": "REJECTED"})
    artifacts.write_artifact("run-skipped", {"stage": "emit", "ok": True})

    res = client.get("/api/metrics")
    assert res.status_code == 200
    body = res.json()
    assert body["false_certified_rate"] == 0.5
    assert body["measured"] is True
    assert body["by_operator"]["boundary_drop"] == {"certified": 1, "total": 2}
    assert set(body) == {"false_certified_rate", "measured", "by_operator"}


def test_resolve_dist_points_at_project_frontend_dist():
    """The defect: the old climb went THREE levels and landed outside the
    project, so the isdir check always failed and the mount never activated."""
    repo_root = Path(__file__).resolve().parents[2]
    assert Path(main_mod._resolve_dist()) == repo_root / "frontend" / "dist"


def test_mount_dashboard_mounts_when_dist_exists(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>dashboard</html>", encoding="utf-8")

    fresh = FastAPI()

    @fresh.get("/health")
    def _health():
        return {"ok": True}

    assert main_mod.mount_dashboard(fresh, dist=str(dist)) is True
    # Starlette registers a "/" mount with path "" (verified against the pinned
    # starlette 1.7.0) — assert on the Mount object, not a literal path.
    assert any(isinstance(r, Mount) for r in fresh.routes)

    tc = TestClient(fresh)
    # the "/" mount must not shadow routes registered before it
    assert tc.get("/health").status_code == 200
    assert tc.get("/").status_code == 200


def test_mount_dashboard_skips_when_dist_missing(tmp_path):
    fresh = FastAPI()
    assert main_mod.mount_dashboard(fresh, dist=str(tmp_path / "nope")) is False
    assert not any(isinstance(r, Mount) for r in fresh.routes)


def test_app_title_and_version_match_docs():
    assert app.title == "Intent Attestation Gate"
    assert app.version == "0.1.0"
