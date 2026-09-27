"""Guards for scripts/attest.py — the Bob-facing CLI (M18-exclusive file).

Convention: the CLI is exercised as a black box (subprocess, like the
validator wrap in this file's neighbours) against a fake localhost server —
never a live gate, never a live LLM, never Bob. The --direct path runs the
real in-process pipeline with its persistence redirected into tmp_path, so
the repo tree stays clean (Convention 3).
"""
import ast
import json
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
ATTEST = ROOT / "scripts" / "attest.py"
PAYLOAD = ROOT / "fixtures" / "demo_payload.json"


class _Handler(BaseHTTPRequestHandler):
    def _send(self, obj):
        body = json.dumps(obj).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):  # noqa: N802 — http.server names the method
        length = int(self.headers.get("Content-Length", 0))
        self.server.seen_posts.append(json.loads(self.rfile.read(length) or b"{}"))
        self._send({"run_id": "run-test01", "status": "queued"})

    def do_GET(self):  # noqa: N802 — http.server names the method
        statuses = self.server.poll_statuses
        status = statuses.pop(0) if len(statuses) > 1 else statuses[0]
        self._send({"run_id": "run-test01", "status": status, "measured": False,
                    "verdicts": [{"criterion_id": "AC-1", "verdict": "CERTIFIED",
                                  "evidence_tier": "E4",
                                  "locations": ["src/refund.py:41"]}]})

    def log_message(self, *args):
        pass


@pytest.fixture()
def fake_gate():
    """A canned gate server on localhost. poll_statuses is consumed in order;
    the last entry repeats, so ["pending"] never terminates."""
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    server.seen_posts = []
    server.poll_statuses = ["pending"]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server
    server.shutdown()
    thread.join()


def _run_attest(*argv, cwd=None, env=None):
    return subprocess.run(
        [sys.executable, str(ATTEST), *argv],
        capture_output=True, text=True, timeout=60, cwd=cwd or str(ROOT), env=env,
    )


def test_demo_payload_matches_section_1_7_shape():
    payload = json.loads(PAYLOAD.read_text())
    assert payload["action"] == "opened"
    assert payload["pr"] == 142
    assert "AC-1" in payload["requirement"] and "AC-2" in payload["requirement"]
    assert payload["diff_paths"] == ["src/refund.py"]


def test_http_certified_run_exits_zero(fake_gate):
    fake_gate.poll_statuses = ["queued", "certified"]
    port = fake_gate.server_address[1]
    proc = _run_attest("--server", f"http://127.0.0.1:{port}",
                       "--payload", str(PAYLOAD), "--interval", "0.05")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert "run-test01" in proc.stdout
    assert "AC-1" in proc.stdout
    assert "exit_code: 0" in proc.stdout
    posted = fake_gate.seen_posts[0]
    assert posted["pr"] == 142


def test_http_rejected_run_exits_nonzero(fake_gate):
    fake_gate.poll_statuses = ["queued", "rejected"]
    port = fake_gate.server_address[1]
    proc = _run_attest("--server", f"http://127.0.0.1:{port}",
                       "--payload", str(PAYLOAD), "--interval", "0.05")
    assert proc.returncode == 1
    assert "exit_code: 1" in proc.stdout


def test_http_never_terminal_exits_nonzero(fake_gate):
    """A run stuck in queue must block, never pass."""
    fake_gate.poll_statuses = ["queued"]
    port = fake_gate.server_address[1]
    proc = _run_attest("--server", f"http://127.0.0.1:{port}",
                       "--payload", str(PAYLOAD),
                       "--timeout", "0.5", "--interval", "0.05")
    assert proc.returncode == 1
    assert "never reached a terminal status" in proc.stdout


def test_http_pending_lifecycle_status_is_terminal_but_blocking(fake_gate):
    """`pending` (D-e: the chain completed, verdict in the artifact) ends the
    poll — but without a certified status the exit still blocks (rule 6)."""
    fake_gate.poll_statuses = ["queued", "pending"]
    port = fake_gate.server_address[1]
    proc = _run_attest("--server", f"http://127.0.0.1:{port}",
                       "--payload", str(PAYLOAD), "--interval", "0.05")
    assert proc.returncode == 1
    assert "status: pending" in proc.stdout


def test_http_connection_refused_exits_nonzero():
    probe = HTTPServer(("127.0.0.1", 0), _Handler)
    closed_port = probe.server_address[1]
    probe.server_close()
    proc = _run_attest("--server", f"http://127.0.0.1:{closed_port}",
                       "--payload", str(PAYLOAD))
    assert proc.returncode == 1
    assert "POST failed" in proc.stdout


def test_http_missing_payload_exits_nonzero(tmp_path):
    proc = _run_attest("--payload", str(tmp_path / "missing.json"))
    # Missing payload file fails before any network happens — still fail-closed.
    assert proc.returncode == 1
    assert "cannot load payload" in proc.stdout


def test_direct_mode_runs_pipeline_and_blocks_on_stub_emit(tmp_path):
    """--direct runs the real in-process chain. The demo payload violates AC-2,
    so the exit is 1 both on today's hard-coded emit and on R4's derived one
    (§1.7 target exit_code: 1) — stable across the thin slice."""
    env = {"PATH": "/usr/bin:/bin",
           "DATABASE_URL": f"sqlite:///{tmp_path}/t.db",
           "ARTIFACT_DIR": str(tmp_path / "artifacts")}
    proc = _run_attest("--direct", "--payload", str(PAYLOAD), cwd=str(tmp_path), env=env)
    assert proc.returncode == 1, proc.stderr + proc.stdout
    assert "exit_code: 1" in proc.stdout
    # CWD-relative persistence must have landed in tmp_path, never the repo.
    assert not (ROOT / "attestation.db").exists()
    assert not (ROOT / "artifacts").exists()


def test_attest_script_is_stdlib_only():
    """Bob may run this with any interpreter — no venv-only imports allowed."""
    tree = ast.parse(ATTEST.read_text())
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    # "app" is imported lazily inside run_direct (needs the repo checkout);
    # everything at module scope must be stdlib.
    imported.discard("app")
    non_stdlib = imported - set(sys.stdlib_module_names)
    assert not non_stdlib, f"non-stdlib imports: {non_stdlib}"
