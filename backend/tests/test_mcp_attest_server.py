"""Guards for the Bob MCP integration — scripts/mcp_attest_server.py and .bob/ (M18).

Two things are proven here, and they are different kinds of claim.

1. PROTOCOL. The server is driven as a real subprocess over real stdio with real
   JSON-RPC 2.0 messages, the way a client will drive it. Canned `_handle`
   calls would pass against a server whose framing was broken, so nothing in
   this file short-circuits the transport.

2. POLICY. `.bob/custom_modes.yaml` is the Bob-side half of the read-only
   claim, and a config file is a claim until something mechanical reads it. The
   guard below pins the mode's tool groups to exactly {read, mcp} — a positive
   pin, not a check against the deny list — so *adding* a group fails the suite
   even though adding one is what weakens the posture. `edit` and `execute`
   are checked separately against the gate's own DENIES, so the two halves
   cannot drift apart silently.

STILL UNPROVEN, and the guards must not pretend otherwise: that IBM Bob
speaks this protocol. These tests prove our client and our server agree. Until
a real `bob run --mode attestor` exercises the server, "our client agrees with
our server" is not "Bob agrees with our server". That gap is Phase C of the
plan and nothing in this file can close it.

Convention: subprocess, never a live gate, never a live LLM, never Bob. The
pure path is used throughout, so nothing is persisted and the repo tree stays
clean (Convention 3).
"""
import ast
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SERVER = ROOT / "scripts" / "mcp_attest_server.py"
PAYLOAD = ROOT / "fixtures" / "demo_payload.json"
MODES = ROOT / ".bob" / "custom_modes.yaml"
MCP_CONFIG = ROOT / ".bob" / "mcp.json"
BOB_DIR = ROOT / ".bob"

# The tool-group vocabulary of bobshell@2.0.5 (commit 2dc180906), vendored as
# test data because it lives inside a 15 MB bundle at a machine-specific path.
# Provenance: the `groups:` arrays of the shipped builtin mode definitions —
# agent, plan, ask, and friends — which are the product's own statement of what
# a group is. Read from the installed package, NOT from the docs: Bob's Bob
# Shell custom-modes page advertises a `command` group that does not exist in
# the binary, and omits todo/artifact/subtask/mode. If a future Bob adds a
# group, this set is wrong and the exact-match guard below will say so.
BOB_TOOL_GROUPS = frozenset({
    "read", "edit", "execute", "browser", "mcp",
    "skill", "todo", "artifact", "subtask", "subagent", "mode",
})

# What the gate's own policy withholds. Imported, not retyped: the two halves of
# the read-only claim are only worth anything if they are checked against the
# same constant the product uses.
sys.path.insert(0, str(ROOT / "backend"))
from app.attestor.policy import DENIES  # noqa: E402 — path set above, as the CLI does


# --------------------------------------------------------------------------
# Transport
# --------------------------------------------------------------------------

def _rpc(*messages, cwd=None, timeout=90):
    """Drive the server over real stdio. Returns (responses, stderr, proc).

    `responses` is every line the server wrote to stdout, parsed. It is a list
    rather than a single object so a test can assert on what was NOT sent back —
    a notification must be silent, and that is only visible across a sequence.

    A str argument is written through verbatim, which is how a deliberately
    malformed line reaches the server's parser instead of being JSON-encoded
    into a well-formed request (a valid JSON-RPC message is always an object,
    so a str can only ever mean "raw").
    """
    payload = "".join(
        (m if isinstance(m, str) else json.dumps(m)) + "\n" for m in messages
    )
    proc = subprocess.run(
        [sys.executable, str(SERVER)],
        input=payload, capture_output=True, text=True,
        timeout=timeout, cwd=str(cwd or ROOT),
    )
    responses = [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]
    return responses, proc.stderr, proc


def _initialize(requested="2026-07-28", msg_id=1):
    return {"jsonrpc": "2.0", "id": msg_id, "method": "initialize",
            "params": {"protocolVersion": requested, "capabilities": {},
                       "clientInfo": {"name": "test", "version": "0"}}}


def _call(name, arguments=None, msg_id=2):
    return {"jsonrpc": "2.0", "id": msg_id, "method": "tools/call",
            "params": {"name": name, "arguments": arguments or {}}}


def _text(response):
    return response["result"]["content"][0]["text"]


# --------------------------------------------------------------------------
# Protocol
# --------------------------------------------------------------------------

def test_initialize_handshake_advertises_tool_capability():
    responses, _err, proc = _rpc(_initialize())
    assert proc.returncode == 0
    assert len(responses) == 1
    result = responses[0]["result"]
    assert responses[0]["jsonrpc"] == "2.0"
    assert "tools" in result["capabilities"]
    assert result["serverInfo"]["name"] == "intent-attestation-gate"


@pytest.mark.parametrize("requested", [
    "2026-07-28", "2026-06-18", "2025-11-25", "2025-06-18",
])
def test_initialize_echoes_a_protocol_version_we_speak(requested):
    """Negotiate down rather than fail the handshake. A newer client and an
    older client must both end up with a version this server actually speaks."""
    responses, _err, _proc = _rpc(_initialize(requested=requested))
    assert responses[0]["result"]["protocolVersion"] == requested


def test_initialize_with_unknown_version_falls_back_instead_of_failing():
    responses, _err, _proc = _rpc(_initialize(requested="1999-01-01"))
    assert responses[0]["result"]["protocolVersion"] == "2026-07-28"


def test_notification_gets_no_reply():
    """By spec a notification has no id and gets no response. A server that
    answers one is chatty, and Bob reads the extra line as an unsolicited
    message — so this is a framing property, not a tidiness preference."""
    responses, _err, _proc = _rpc(
        _initialize(),
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
    )
    assert [r.get("id") for r in responses] == [1]


def test_tools_list_exposes_both_tools_with_input_schemas():
    responses, _err, _proc = _rpc(_initialize(), {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    tools = responses[1]["result"]["tools"]
    by_name = {t["name"]: t for t in tools}
    assert set(by_name) == {"attest_run", "attest_exposure_honesty"}
    for tool in tools:
        assert tool["description"].strip(), f"{tool['name']} has no description"
        assert tool["inputSchema"]["type"] == "object"


def test_malformed_line_gets_a_parse_error_and_the_session_survives():
    """One bad message must not take the session down, and must not be answered
    with silence — silence reads to the client as a hang."""
    responses, _err, proc = _rpc(
        _initialize(), "not json", _call("attest_run"),
    )
    assert proc.returncode == 0
    assert responses[1]["error"]["code"] == -32700
    # The session kept working: the third message still got a real answer.
    assert "AC-1" in _text(responses[2])


def test_unknown_method_is_method_not_found():
    responses, _err, _proc = _rpc({"jsonrpc": "2.0", "id": 9, "method": "totally/unknown"})
    assert responses[0]["error"]["code"] == -32601


def test_unknown_tool_is_invalid_params_not_a_crash():
    responses, _err, proc = _rpc(_call("nope"))
    assert proc.returncode == 0
    assert responses[0]["error"]["code"] == -32602


def test_every_response_line_is_valid_jsonrpc():
    """The framing invariant: stdout carries MCP messages and nothing else. A
    stray print() anywhere in the chain would break this and would look to Bob
    like an unrelated parse error, so the check is on shape, not on content."""
    responses, _err, _proc = _rpc(
        _initialize(),
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        _call("attest_run"),
    )
    assert responses, "server produced no output at all"
    for response in responses:
        assert response["jsonrpc"] == "2.0"
        assert "id" in response
        assert ("result" in response) ^ ("error" in response)


# --------------------------------------------------------------------------
# The demo verdict — the thing the demo actually shows
# --------------------------------------------------------------------------

def test_attest_run_returns_the_demo_verdict():
    """§1.7's pair, end to end over the transport Bob will use: AC-1 CERTIFIED
    at E4, AC-2 REJECTED at E2 with its location, and a blocking exit code."""
    responses, _err, _proc = _rpc(_initialize(), _call("attest_run"))
    assert not responses[-1]["result"].get("isError"), _text(responses[-1])
    text = _text(responses[-1])
    assert "AC-1: CERTIFIED [E4]" in text
    assert "src/refund.py:64" in text
    assert "AC-2: REJECTED [E2]" in text
    assert "src/refund.py:88" in text
    assert "status: rejected" in text
    assert "exit_code: 1" in text


def test_attest_run_reports_the_rate_as_unmeasured_not_zero():
    """The honesty surface. A gate that printed 0.0 would be claiming a
    measurement it never made; 'unmeasured' is the only true thing to say."""
    responses, _err, _proc = _rpc(_initialize(), _call("attest_run"))
    text = _text(responses[-1])
    assert "unmeasured" in text
    assert "no number is claimed" in text


def test_exposure_honesty_tool_states_it_plainly():
    responses, _err, _proc = _rpc(_initialize(), _call("attest_exposure_honesty"))
    text = _text(responses[-1])
    assert "unmeasured" in text
    assert "not a zero" in text


def test_attest_run_accepts_an_inline_payload():
    responses, _err, _proc = _rpc(
        _initialize(), _call("attest_run", {"payload": json.loads(PAYLOAD.read_text())}))
    assert "AC-1" in _text(responses[-1])


def test_attest_run_resolves_a_relative_path_from_any_working_directory():
    """Bob chooses this process's cwd and .bob/mcp.json deliberately does not
    pin it, so a relative payload_path must resolve regardless. Launched from
    / — a directory with no fixtures/ at all."""
    responses, _err, _proc = _rpc(
        _initialize(),
        _call("attest_run", {"payload_path": "fixtures/demo_payload.json"}),
        cwd=Path("/"),
    )
    assert not responses[-1]["result"].get("isError"), _text(responses[-1])
    assert "AC-1: CERTIFIED [E4]" in _text(responses[-1])


# --------------------------------------------------------------------------
# Fail-closed (rule 6) — every unreachable verdict blocks, none passes
# --------------------------------------------------------------------------

def test_missing_payload_is_an_error_not_a_pass():
    responses, _err, proc = _rpc(
        _initialize(), _call("attest_run", {"payload_path": "definitely/not/here.json"}))
    assert proc.returncode == 0
    assert responses[-1]["result"]["isError"] is True
    assert "cannot load payload" in _text(responses[-1])


def test_unparseable_payload_is_an_error_not_a_pass(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json")
    responses, _err, _proc = _rpc(_initialize(), _call("attest_run", {"payload_path": str(bad)}))
    assert responses[-1]["result"]["isError"] is True
    assert "cannot load payload" in _text(responses[-1])


def test_a_crashing_gate_is_an_error_not_a_pass(tmp_path):
    """A payload the chain cannot process must never come back as a verdict.
    The demo payload's diff_paths point at a file that does not exist in
    tmp_path, so ingest has nothing to hash."""
    responses, _err, proc = _rpc(
        _initialize(),
        _call("attest_run", {"payload": {"action": "opened", "pr": 1,
                                         "requirement": 17, "diff_paths": None}}),
        cwd=tmp_path,
    )
    assert proc.returncode == 0
    last = responses[-1]
    # Either the gate blocked it, or it produced a record with no certification.
    # What must never happen is a clean pass.
    if last.get("result", {}).get("isError"):
        assert "blocking" in _text(last) or "cannot" in _text(last)
    else:
        assert "exit_code: 0" not in _text(last)


def test_no_tool_can_return_a_certified_verdict_without_the_gate_saying_so():
    """Structural: the formatter reads the record, it does not decide. If
    `status` is absent the exit line says 1, not 0."""
    responses, _err, _proc = _rpc(
        _initialize(),
        {"jsonrpc": "2.0", "id": 5, "method": "tools/call",
         "params": {"name": "attest_run", "arguments": {"payload": {}}}},
    )
    text = _text(responses[-1])
    assert "exit_code: 0" not in text


def test_formatter_fails_closed_on_a_record_it_cannot_read():
    """The fail-closed default in `_format_record` is the last line of defence,
    and no black-box path reaches it: the emit stage always sets `exit_code`, so
    mutating the default from 1 to 0 survives every subprocess test in this
    file. It is pinned here directly instead, which means importing the server
    — a deliberate exception to the black-box rule, because the alternative is
    a guard that names an invariant it never actually checks.

    Caught by the mutation harness: 18 mutations, this was the only genuine
    survivor, and it was a weak test rather than a weak product.
    """
    formatter = _server_module()._format_record
    for record in ({}, {"status": "certified"}, {"verdicts": "not-a-list"}):
        text = formatter(record)
        assert "exit_code: 0" not in text, f"fail-open on {record!r}"
        assert "CERTIFIED" not in text
    # And the honest case still passes through when the record really says so.
    assert "exit_code: 0" in formatter({"exit_code": 0, "status": "certified"})


def _server_module():
    """Load scripts/mcp_attest_server.py as a module without installing it."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("mcp_attest_server_under_test", SERVER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# --------------------------------------------------------------------------
# Secrets — .bob/ is version-controlled, and Bob's own config format invites one
# --------------------------------------------------------------------------

def test_bob_directory_contains_no_secret():
    """`.bob/` is committed on purpose (it is the shareable artifact) and Bob's
    MCP config has an `env` key whose entire purpose is carrying a credential.
    Those two facts together are how an API key gets committed, so the file Bob
    reads is scanned for the shapes a key takes. Cheap, and the failure mode it
    prevents is not recoverable from git history."""
    suspicious = ("apikey", "api_key", "api-key", "secret", "token", "password",
                  "bob_prod_", "bearer ", "sk-", "BEGIN RSA", "BEGIN PRIVATE")
    for path in sorted(BOB_DIR.rglob("*")):
        if not path.is_file():
            continue
        text = path.read_text(errors="replace")
        for marker in suspicious:
            assert marker not in text.lower(), (
                f"{path.name} contains {marker!r} — a credential must never be "
                "committed. Pass secrets through the environment, not the config."
            )


# --------------------------------------------------------------------------
# Read-only at the storage layer
# --------------------------------------------------------------------------

def test_pure_path_persists_nothing_from_any_working_directory():
    """attest_run calls run_pipeline with no run_id, which is the documented
    pure path: stages run, nothing is written. So the read-only posture holds
    at the storage layer, not only at the capability layer — and it holds
    without pinning a cwd, which is why .bob/mcp.json carries no `cwd` key."""
    before = sorted(p.name for p in ROOT.iterdir())
    _rpc(_initialize(), _call("attest_run"), cwd=Path("/"))
    after = sorted(p.name for p in ROOT.iterdir())
    assert before == after
    assert not (ROOT / "attestation.db").exists()
    assert not (ROOT / "artifacts").exists()


def test_gates_contain_no_write_calls():
    """The claim above rests on the gates being write-free. A future gate that
    writes would make attest_run a writer, and this guard would then be
    asserting the opposite of the truth.

    Two shapes are checked, because the obvious one is not the common one. A
    method-style call (`Path(p).write_text(...)`) shows up as an attribute name
    the AST hands over directly. A bare `open(p, "w")` has no such name, because
    `open` is a builtin — so a guard built only on the first passes cleanly
    against the second. The mutation harness is what found that: the open() form
    survived every mutation, which is a fact about the guard rather than about
    the gates.

    `os.open` is deliberately out of scope. Its second argument is integer flags
    rather than a mode string, so no mode check reads it, and the one call in
    the gates — ingest.py's `os.open(path, O_RDONLY | O_NOFOLLOW)` — is the gate
    hashing the very file it verifies. Attempting to reason about those flags
    here produced a false positive on the one gate that is behaving correctly,
    which is worse than the gap it closed. M4's own guards pin O_RDONLY; this
    guard is about the spelling, not the flag.
    """
    write_methods = {
        "write_text", "write_bytes", "writelines", "write_artifact", "mkdir",
        "mkdirs", "unlink", "remove", "rmdir", "rename", "replace", "touch",
        "truncate", "chmod", "chown", "utime", "copy", "copyfile", "move",
        "symlink_to", "hardlink_to", "link_to", "rmtree", "sendfile",
    }
    offenders = []
    for path in sorted((ROOT / "backend" / "app" / "gates").glob("*.py")):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = getattr(func, "attr", getattr(func, "id", ""))
            if name in write_methods:
                offenders.append(f"{path.name}:{node.lineno}:{name}()")
            elif name == "open" and _is_bare_open(func) and _opens_for_writing(node):
                offenders.append(f"{path.name}:{node.lineno}:open-for-write")
    assert not offenders, f"gates must not write (M18 read-only claim): {offenders}"


def _is_bare_open(func):
    """True for the builtin `open`, false for `os.open` / `io.open`."""
    return not (isinstance(func, ast.Attribute)
                and isinstance(func.value, ast.Name) and func.value.id != "open")


def _opens_for_writing(call):
    """True when `open(...)` is opened for writing.

    The mode is the second positional argument or the `mode=` keyword. An absent
    mode means read, so it is not flagged. A mode that is not a literal string
    IS flagged: it could be anything at runtime, and the honest reading of an
    unreadable mode inside a read-only gate is "it writes" — the asymmetry is
    the point (rule 6).

    Matched as a character set rather than a list of spellings, because `wb`,
    `bw+` and `ab` are all writes, and enumerating the obvious strings is the
    wrong shape of guard.
    """
    mode = None
    if len(call.args) >= 2:
        mode = call.args[1]
    for keyword in call.keywords:
        if keyword.arg == "mode":
            mode = keyword.value
    if mode is None:
        return False
    if isinstance(mode, ast.Constant) and isinstance(mode.value, str):
        return bool(set("wax+") & set(mode.value.lower()))
    return True




# --------------------------------------------------------------------------
# The Bob-side policy claim
# --------------------------------------------------------------------------

def _mode_groups(text, slug="attestor"):
    """The `groups:` list for one mode slug, read without PyYAML (rule 9 — it is
    not a pin, and a dependency added to parse one list would be absurd).

    Strict on purpose: if the file's shape changes so this cannot find the slug
    or its groups, it raises. A permissive reader that returned [] on a
    reformat would make every guard below pass vacuously, which is the failure
    mode this repo keeps paying for.
    """
    lines = text.splitlines()
    slug_indent = None
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped in (f"- slug: {slug}", f"slug: {slug}"):
            slug_indent = len(line) - len(line.lstrip())
            break
    if slug_indent is None:
        raise AssertionError(f"no slug {slug!r} in {MODES.name}")

    for index in range(len(lines)):
        line = lines[index]
        if not line.strip() or line.strip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        if indent <= slug_indent or line.strip() != "groups:":
            continue
        groups = []
        for follow in lines[index + 1:]:
            if not follow.strip():
                continue
            follow_indent = len(follow) - len(follow.lstrip())
            if follow_indent <= indent:
                break
            if follow_indent == indent + 2 and follow.strip().startswith("- "):
                groups.append(follow.strip()[2:].strip())
        if not groups:
            raise AssertionError(f"groups: under {slug!r} is empty or unparseable")
        return groups
    raise AssertionError(f"no groups: block for {slug!r} in {MODES.name}")


@pytest.fixture(scope="module")
def mode_text():
    if not MODES.exists():
        pytest.fail(f"{MODES} is missing — the Bob-side read-only claim is a file, "
                    "and a deleted file is a deleted claim")
    return MODES.read_text()


def test_attestor_mode_grants_exactly_read_and_mcp(mode_text):
    """The positive pin. Checking only against DENIES would pass a mode that
    gained `browser` or `subagent` or `artifact` — each of which widens the
    posture without touching the deny list. Exactly two, both load-bearing:
    read inspects, mcp reaches the gate."""
    assert set(_mode_groups(mode_text)) == {"read", "mcp"}


def test_attestor_mode_grants_nothing_the_gate_withholds(mode_text):
    """The two halves of one claim, checked against the same constant the
    product uses. If DENIES is ever widened, this fails until the mode is."""
    from app.attestor.policy import GRANTS

    granted = set(_mode_groups(mode_text))
    assert not granted & set(DENIES), f"attestor must not grant {sorted(granted & set(DENIES))}"
    # `mcp` has no counterpart in the gate's GRANTS: it is a client-side group,
    # not a worker capability. Everything else must be a real grant.
    assert granted - {"mcp"} <= set(GRANTS)


def test_every_mode_group_is_a_real_bob_tool_group(mode_text):
    """A typo would be silently ignored by Bob and the mode would quietly have
    fewer capabilities than the file claims — the read-only claim would survive
    for the wrong reason. `command` is the trap: Bob's documentation advertises
    it, and the shipped binary has no such group."""
    for group in _mode_groups(mode_text):
        assert group in BOB_TOOL_GROUPS, f"{group!r} is not a bobshell 2.0.5 tool group"


def test_attestor_mode_forbids_subagents_explicitly(mode_text):
    """`subagent` is not in the groups, so spawn_subagent is never registered —
    this pins the declared intent too, so a reader of the file can see it
    without resolving the group semantics."""
    assert "allowedSubagents: []" in mode_text


def test_mode_file_documents_where_the_vocabulary_came_from(mode_text):
    """Provenance, as a guard. The file's central claim (that these are the
    real group names) is true because someone read the shipped bundle, and that
    is invisible to anyone reading only the YAML."""
    assert "bobshell@2.0.5" in mode_text
    assert "2dc180906" in mode_text


# --------------------------------------------------------------------------
# The MCP registration Bob reads
# --------------------------------------------------------------------------

@pytest.fixture(scope="module")
def mcp_config():
    if not MCP_CONFIG.exists():
        pytest.fail(f"{MCP_CONFIG} is missing — without it Bob never connects")
    return json.loads(MCP_CONFIG.read_text())


def test_mcp_config_registers_the_gate_server(mcp_config):
    assert "attest-gate" in mcp_config["mcpServers"]
    server = mcp_config["mcpServers"]["attest-gate"]
    assert server["disabled"] is not True
    assert server["args"] == ["scripts/mcp_attest_server.py"]
    assert (ROOT / server["args"][0]).exists(), "registered script does not exist"


def test_mcp_config_auto_allows_both_tools(mcp_config):
    """alwaysAllow is what stops a mid-demo approval prompt. A tool added to the
    server without being listed here is one the demo would stall on."""
    server = mcp_config["mcpServers"]["attest-gate"]
    tools = _tool_names()
    assert set(server["alwaysAllow"]) == tools, (
        "alwaysAllow must cover every tool the server exposes, or the demo "
        f"prompts for approval: server has {sorted(tools)}")


def _tool_names():
    responses, _err, _proc = _rpc(_initialize(), {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    return {t["name"] for t in responses[1]["result"]["tools"]}


def test_mcp_config_pins_no_working_directory(mcp_config):
    """Deliberate. Relative-path semantics for `cwd` are undocumented, and the
    pure path writes nothing, so pinning one would add a dependency on
    undefined behaviour in exchange for nothing. If a future change makes the
    server write, this guard is where that has to be revisited."""
    assert "cwd" not in mcp_config["mcpServers"]["attest-gate"]


def test_bob_directory_holds_only_the_two_documented_files():
    """`.bob/` is read by Bob and version-controlled, so an unexpected file here
    is either a leftover or something that will be read by more than one tool."""
    assert {p.name for p in BOB_DIR.iterdir()} == {"custom_modes.yaml", "mcp.json"}


# --------------------------------------------------------------------------
# Stdlib only — Bob runs this with whatever interpreter it finds
# --------------------------------------------------------------------------

def test_mcp_server_is_stdlib_only():
    """Same rule as scripts/attest.py. `app` is imported lazily inside
    _load_pipeline (it needs the repo checkout); everything at module scope must
    be stdlib, or Bob launches a server that dies on import and the client
    reports a connection failure with no cause."""
    tree = ast.parse(SERVER.read_text())
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    imported.discard("app")
    non_stdlib = imported - set(sys.stdlib_module_names)
    assert not non_stdlib, f"non-stdlib imports: {non_stdlib}"


def test_server_diagnostics_never_go_to_stdout():
    """A print() without a file= argument inside the server would corrupt the
    framing. Pin the call site, not the intention."""
    tree = ast.parse(SERVER.read_text())
    bare = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
            continue
        if node.func.id != "print":
            continue
        if not any(kw.arg == "file" for kw in node.keywords):
            # main()'s CLI output is fine: those paths return before serve().
            bare.append(node.lineno)
    serve_body = ast.get_source_segment(SERVER.read_text(), _find_serve(SERVER.read_text()))
    assert serve_body is not None
    for lineno in bare:
        segment = ast.get_source_segment(SERVER.read_text(),
                                         _enclosing_line(SERVER.read_text(), lineno))
        assert "serve" not in segment, f"print() at line {lineno} is inside serve()"


def _find_serve(source):
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.FunctionDef) and node.name == "serve":
            return node
    raise AssertionError("no serve() in the MCP server")


def _enclosing_line(source, lineno):
    """The statement at `lineno`, widened to its enclosing block when the print
    is nested in one — enough to tell a serve() print from a main() print."""
    tree = ast.parse(source)
    best = None
    for node in ast.walk(tree):
        if isinstance(node, ast.stmt) and getattr(node, "lineno", None) == lineno:
            parent_block = getattr(node, "_parent", None)
            if parent_block is not None and getattr(parent_block, "lineno", 10**6) < node.lineno:
                best = parent_block
            else:
                best = node
    return best
