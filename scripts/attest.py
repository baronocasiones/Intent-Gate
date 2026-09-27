#!/usr/bin/env python3
"""attest.py — Bob-facing CLI for the Intent Attestation Gate (M18).

HTTP mode (default): POST an injected GitHub payload to /webhooks/github,
poll GET /api/runs/{id} until the run leaves a non-terminal status, print the
verdict + traceability, and exit with the run's merge signal.

Exit derivation: the served `status` field is the signal — exit 0 iff status
is "certified" (case-insensitive), 1 for everything else, including timeouts,
leftover queued/pending statuses, and connection errors. Fail-closed: a gate
that cannot decide blocks the merge (rule 6).

--direct mode: run the pipeline in-process (no server needed) and exit with
the record's exit_code (1 when absent or unparseable — fail-closed).

Stdlib only, so Bob can run it with any interpreter. No live LLM, no Bob API.
"""
import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PAYLOAD = ROOT / "fixtures" / "demo_payload.json"

# Statuses that mean "the loop has not finished yet". Anything else the server
# returns is terminal — including the lifecycle `pending`/`failed` (D-e: the
# chain completed) and any future verdict-level status. The exit derivation
# below stays fail-closed regardless of which words a future stage chooses.
NON_TERMINAL = {"", "queued", "running"}


def _post(url, payload, timeout):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read() or b"{}")


def _get(url, timeout):
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return json.loads(resp.read() or b"{}")


def _print_run(run):
    print(f"run_id: {run.get('run_id', '?')}")
    print(f"status: {run.get('status', '?')}")
    verdicts = run.get("verdicts") or []
    if not verdicts:
        print("verdicts: (none reported)")
    for v in verdicts:
        locs = ", ".join(v.get("locations", []) or [])
        tier = v.get("evidence_tier", "?")
        print(f"  {v.get('criterion_id', '?')}: {v.get('verdict', '?')} [{tier}] {locs}")


def _exit_for_status(status):
    """0 iff certified, else 1 — fail-closed on anything undecided."""
    return 0 if str(status or "").lower() == "certified" else 1


def run_http(args):
    try:
        payload = json.loads(Path(args.payload).read_text())
    except (OSError, ValueError) as exc:
        print(f"attest: cannot load payload {args.payload}: {exc}")
        return 1
    try:
        posted = _post(args.server + "/webhooks/github", payload, args.request_timeout)
    except (urllib.error.URLError, OSError, ValueError) as exc:
        print(f"attest: POST failed (is the server up at {args.server}?): {exc}")
        return 1
    run_id = posted.get("run_id")
    if not run_id:
        print(f"attest: webhook returned no run_id: {posted}")
        return 1

    deadline = time.monotonic() + args.timeout
    run = {"run_id": run_id, "status": "queued"}
    while time.monotonic() < deadline:
        try:
            run = _get(f"{args.server}/api/runs/{run_id}", args.request_timeout)
        except (urllib.error.URLError, OSError, ValueError) as exc:
            print(f"attest: poll failed: {exc}")
            return 1
        if str(run.get("status", "")).lower() not in NON_TERMINAL:
            break
        time.sleep(args.interval)
    else:
        print(f"attest: run {run_id} never reached a terminal status "
              f"(last: {run.get('status')}) — the server loop may not be wired yet")
        _print_run(run)
        return 1

    _print_run(run)
    code = _exit_for_status(run.get("status"))
    print(f"exit_code: {code}")
    return code


def run_direct(args):
    try:
        payload = json.loads(Path(args.payload).read_text())
    except (OSError, ValueError) as exc:
        print(f"attest: cannot load payload {args.payload}: {exc}")
        return 1
    sys.path.insert(0, str(ROOT / "backend"))
    try:
        from app.orchestrator.pipeline import run_pipeline
    except ImportError as exc:
        print(f"attest: cannot import pipeline in --direct mode: {exc}")
        return 1
    try:
        record = run_pipeline(payload)
    except Exception as exc:  # noqa: BLE001 — a crashing gate blocks, never passes
        print(f"attest: pipeline raised (blocking): {exc}")
        return 1
    print(json.dumps(record, indent=2, sort_keys=True))
    try:
        code = int(record.get("exit_code", 1))
    except (TypeError, ValueError):
        code = 1
    print(f"exit_code: {code}")
    return code


def main(argv=None):
    parser = argparse.ArgumentParser(description="Invoke the Intent Attestation Gate.")
    parser.add_argument("--server", default="http://127.0.0.1:8000")
    parser.add_argument("--payload", default=str(DEFAULT_PAYLOAD))
    parser.add_argument("--timeout", type=float, default=60.0,
                        help="poll deadline in seconds (HTTP mode)")
    parser.add_argument("--interval", type=float, default=1.0,
                        help="seconds between polls (HTTP mode)")
    parser.add_argument("--request-timeout", type=float, default=10.0)
    parser.add_argument("--direct", action="store_true",
                        help="run the pipeline in-process instead of HTTP")
    args = parser.parse_args(argv)
    return run_direct(args) if args.direct else run_http(args)


if __name__ == "__main__":
    sys.exit(main())
