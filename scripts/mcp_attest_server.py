#!/usr/bin/env python3
"""mcp_attest_server.py — the Intent Attestation Gate as an MCP tool for Bob (M18).

Bob IDE and Bob Shell both expose `mcp` as a tool group that is SEPARATE from
`execute` (the shell). So a Bob custom mode can call this server and have no
shell at all — the read-only claim is then something the IDE enforces, not
something this process merely asserts. That is why this file exists instead of
pointing Bob at scripts/attest.py: the CLI needs a shell to run, and granting
Bob a shell to verify a diff is exactly the capability §3.3 withholds.

Transport: MCP stdio — one JSON-RPC 2.0 message per line on stdin/stdout, no
embedded newlines. THE INVARIANT: stdout carries MCP messages and nothing else.
All diagnostics go to stderr, because a stray print() corrupts the framing and
the client disconnects with a parse error that looks nothing like the real cause.

Pure on purpose. `attest_run` calls `run_pipeline(payload)` with no run_id,
which is the documented pure path: the six stages run and NOTHING is persisted
— no row, no artifact, no chain. So this server reads the code under
verification and never writes it, and the read-only posture holds at the
storage layer too, not only at the capability layer.

Fail-closed, as everywhere else (rule 6). An unreadable payload, an unimportable
pipeline, a stage that crashes, an unknown method — every one of them is an
error the caller can see, and none of them can produce a pass. The tool never
returns a verdict it did not get from the gate.

Stdlib only (rule 9), so Bob can run it with any interpreter. No live LLM, no
Bob API, no network.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PAYLOAD = ROOT / "fixtures" / "demo_payload.json"

SERVER_NAME = "intent-attestation-gate"
SERVER_VERSION = "0.1.0"

# The wire format is stable across these revisions; echo the client's own version
# when we speak it, so a newer Bob negotiates down to something we understand
# instead of failing the handshake outright. Deliberately a set rather than a
# single constant: pinning one version would make an unknown client unusable.
SUPPORTED_PROTOCOL_VERSIONS = ("2026-07-28", "2026-06-18", "2025-11-25", "2025-06-18")
DEFAULT_PROTOCOL_VERSION = SUPPORTED_PROTOCOL_VERSIONS[0]

TOOLS = [
    {
        "name": "attest_run",
        "description": (
            "Verify a change against its own acceptance criteria and return a "
            "per-criterion verdict with an evidence tier and source locations. "
            "This is a gate, not a reviewer: it decides whether the change does "
            "what the requirement asked for, and a non-zero exit blocks the "
            "merge. Read-only — it inspects the code and changes nothing. Pass "
            "either payload_path (a file holding an injected GitHub webhook "
            "body) or an inline payload object."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "payload_path": {
                    "type": "string",
                    "description": (
                        "Path to an injected GitHub webhook payload. Defaults to "
                        "the repository's fixtures/demo_payload.json."
                    ),
                },
                "payload": {
                    "type": "object",
                    "description": "An inline payload object, used when payload_path is absent.",
                },
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "attest_exposure_honesty",
        "description": (
            "State whether the false-certified rate is measured or unmeasured. "
            "A gate that shows a number it cannot back is selling a claim, so "
            "the unmeasured marker is reported explicitly rather than implied by "
            "an absent field."
        ),
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
]


def _log(message):
    """Diagnostics go to stderr. Never stdout — see the framing invariant."""
    print(message, file=sys.stderr, flush=True)


def _text_result(text, is_error=False):
    """MCP tool result. Tool-level failures ride here with isError rather than a
    protocol error, so the caller reads the reason instead of a bare code."""
    result = {"content": [{"type": "text", "text": text}]}
    if is_error:
        result["isError"] = True
    return result


def _load_pipeline():
    """Import the real gate, once, and fail loudly if it cannot be found.

    Lazy so that a `tools/list` handshake still works on a machine without the
    backend on the path — the client learns the tools exist, and the failure
    arrives on the call that actually needs them, named.
    """
    if str(ROOT / "backend") not in sys.path:
        sys.path.insert(0, str(ROOT / "backend"))
    from app.orchestrator.pipeline import run_pipeline  # noqa: PLC0415 — lazy by design

    return run_pipeline


def _resolve_payload(args):
    """Inline object wins, then payload_path (absolute, else relative to CWD),
    then the committed demo payload. Returns (payload, error_message)."""
    inline = args.get("payload")
    if isinstance(inline, dict):
        return inline, None
    raw_path = args.get("payload_path")
    path = Path(raw_path) if raw_path else DEFAULT_PAYLOAD
    if not path.is_absolute():
        # Try the launch directory first, then the repository root. Bob decides
        # this process's cwd, and .bob/mcp.json deliberately does not pin it,
        # so a relative payload_path must not depend on where we were started.
        # Absent both, the original path is kept so the error names what was
        # actually asked for rather than the first place we looked.
        for candidate in (Path.cwd() / path, ROOT / path):
            if candidate.exists():
                path = candidate
                break
    try:
        loaded = json.loads(path.read_text())
    except (OSError, ValueError) as exc:
        return None, f"cannot load payload {path}: {exc}"
    if not isinstance(loaded, dict):
        return None, f"payload {path} is not a JSON object"
    return loaded, None


def _format_record(record):
    """The auditable view: per-criterion verdict, tier, and where it was seen.
    The unmeasured exposure marker travels with the verdict on purpose — a
    number we cannot back must say so on the same surface as the one we can."""
    lines = [
        f"status: {record.get('status', '?')}",
        f"exit_code: {record.get('exit_code', 1)}",
    ]
    verdicts = record.get("verdicts") or []
    if not verdicts:
        lines.append("verdicts: (none reported)")
    for verdict in verdicts:
        if not isinstance(verdict, dict):
            continue
        locations = ", ".join(verdict.get("locations", []) or [])
        lines.append(
            f"  {verdict.get('criterion_id', '?')}: {verdict.get('verdict', '?')} "
            f"[{verdict.get('evidence_tier', '?')}] {locations}".rstrip()
        )
    exposure = record.get("exposure") or {}
    measured = exposure.get("measured", record.get("measured", False))
    rate = exposure.get("false_certified_rate")
    lines.append(
        "exposure: false-certified rate is "
        + (f"{rate} (measured)" if measured else "unmeasured — no number is claimed")
    )
    links = (record.get("traceability") or {}).get("links") or []
    lines.append(f"traceability links: {len(links)}")
    return "\n".join(lines)


def _call_attest_run(args):
    payload, error = _resolve_payload(args or {})
    if error:
        return _text_result(f"attest_run: {error}", is_error=True)
    try:
        run_pipeline = _load_pipeline()
    except ImportError as exc:
        return _text_result(f"attest_run: cannot import the gate: {exc}", is_error=True)
    try:
        # Pure: no run_id, so nothing is persisted (see the module docstring).
        record = run_pipeline(payload)
    except Exception as exc:  # noqa: BLE001 — a crashing gate blocks, never passes
        return _text_result(
            f"attest_run: the gate raised and this run is blocking: "
            f"{type(exc).__name__}: {exc}",
            is_error=True,
        )
    if not isinstance(record, dict):
        return _text_result("attest_run: the gate returned no record", is_error=True)
    return _text_result(_format_record(record))


def _call_attest_exposure_honesty(_args):
    return _text_result(
        "false_certified_rate: unmeasured.\n"
        "The spec-mutation harness is not part of this build, so no rate is "
        "computed and none is reported. Absence of a number is not a zero."
    )


_HANDLERS = {
    "attest_run": _call_attest_run,
    "attest_exposure_honesty": _call_attest_exposure_honesty,
}


def _negotiate(requested):
    if requested in SUPPORTED_PROTOCOL_VERSIONS:
        return requested
    return DEFAULT_PROTOCOL_VERSION


def _handle(message):
    """One JSON-RPC message in, one result-or-error out. Returns the response
    dict, or None for a notification (which by spec gets no reply)."""
    method = message.get("method")
    message_id = message.get("id")
    is_notification = "id" not in message

    if method == "initialize":
        params = message.get("params") or {}
        result = {
            "protocolVersion": _negotiate(params.get("protocolVersion")),
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
        }
    elif method in ("notifications/initialized", "initialized", "notifications/cancelled"):
        return None
    elif method == "ping":
        result = {}
    elif method == "tools/list":
        result = {"tools": TOOLS}
    elif method == "tools/call":
        params = message.get("params") or {}
        name = params.get("name")
        handler = _HANDLERS.get(name)
        if handler is None:
            return {
                "jsonrpc": "2.0", "id": message_id,
                "error": {"code": -32602, "message": f"unknown tool: {name}"},
            }
        result = handler(params.get("arguments") or {})
    else:
        if is_notification:
            return None
        return {
            "jsonrpc": "2.0", "id": message_id,
            "error": {"code": -32601, "message": f"method not found: {method}"},
        }

    if is_notification:
        return None
    return {"jsonrpc": "2.0", "id": message_id, "result": result}


def serve(stdin=None, stdout=None):
    """Read one message per line, answer one message per line, until EOF.

    A line that will not parse is answered with a JSON-RPC parse error and the
    loop continues: one malformed message must not take the session down, and
    must never be answered with silence (which reads to the client as a hang).
    """
    source = stdin if stdin is not None else sys.stdin
    sink = stdout if stdout is not None else sys.stdout
    for line in source:
        text = line.strip()
        if not text:
            continue
        try:
            message = json.loads(text)
        except ValueError as exc:
            sink.write(json.dumps({
                "jsonrpc": "2.0", "id": None,
                "error": {"code": -32700, "message": f"parse error: {exc}"},
            }) + "\n")
            sink.flush()
            continue
        if not isinstance(message, dict):
            sink.write(json.dumps({
                "jsonrpc": "2.0", "id": None,
                "error": {"code": -32600, "message": "request must be an object"},
            }) + "\n")
            sink.flush()
            continue
        try:
            response = _handle(message)
        except Exception as exc:  # noqa: BLE001 — never let one call kill the session
            _log(f"handler crashed: {type(exc).__name__}: {exc}")
            if "id" in message:
                response = {
                    "jsonrpc": "2.0", "id": message["id"],
                    "error": {"code": -32603, "message": f"internal error: {exc}"},
                }
            else:
                response = None
        if response is not None:
            sink.write(json.dumps(response) + "\n")
            sink.flush()


def main(argv=None):
    """--selftest runs the handshake + one tool call in-process and prints the
    transcript, so the protocol can be proven without a client. --version and
    --help work without importing the gate."""
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] in ("--version", "-V"):
        print(f"{SERVER_NAME} {SERVER_VERSION}")
        return 0
    if argv and argv[0] in ("--help", "-h"):
        print(__doc__.strip())
        print("\nTransport: stdio (newline-delimited JSON-RPC 2.0), MCP.")
        return 0
    if argv and argv[0] == "--list-tools":
        print(json.dumps({"tools": [t["name"] for t in TOOLS]}, indent=2))
        return 0
    if argv and argv[0] == "--selftest":
        steps = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize",
             "params": {"protocolVersion": "2026-07-28", "capabilities": {}}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
            {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
             "params": {"name": "attest_run", "arguments": {}}},
        ]
        for step in steps:
            response = _handle(step)
            if response is not None:
                print(json.dumps(response, indent=2))
        return 0
    serve()
    return 0


if __name__ == "__main__":
    sys.exit(main())
