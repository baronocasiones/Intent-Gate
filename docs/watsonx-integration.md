# docs/watsonx-integration.md — watsonx.ai integration research

Research dossier answering the hour-one spike that **M11** has been carrying since Session 6:
*"confirm the watsonx.ai auth pattern, the generation endpoint + request/response shape, the
model id, and the burn plan."*

**Compiled 27 September 2026.** Documentation read only — **no code was written, no dependency
added, no contract changed, no endpoint defined.** The M11 spike is *research-complete*; it is not
*code-complete*, and two of its four questions cannot be closed without a provisioned account
(§7).

**Source marking is used throughout, per the `docs/modules.md` convention:**

| Tag | Meaning |
|---|---|
| **[SOURCED]** | Read directly from vendor documentation. Cited. |
| **[PROPOSED]** | Our design decision. Not vendor-mandated. Reversible. |
| **[CORRECTED]** | Supersedes an earlier claim, including one made in conversation. |
| **[UNVERIFIED]** | Cannot be confirmed without a live account. Do not treat as fact. |

## Sources read

- **watsonx.ai REST API reference** — Context7 library `/websites/cloud_ibm_apidocs_watsonx-ai`
  (and the `-cp` variant surfaced in the same responses). Four queries: text generation + chat
  shapes; IAM authentication + model listing; function calling / JSON mode / guided output;
  rate limits + error codes. Benchmark score 75–94, ~3,550 code snippets across the two entries.
  Canonical URL: <https://cloud.ibm.com/apidocs/watsonx-ai>
- **IBM Cloud IAM — generating a token from an API key** —
  <https://cloud.ibm.com/docs/iam?topic=iam-iamtoken_from_apikey>
- **IBM Cloud — watsonx authentication** — <https://cloud.ibm.com/docs/watson?topic=watson-iam>
- **watsonx Orchestrate — authoring Python tools (ADK)** —
  <https://developer.watson-orchestrate.ibm.com/tools/create_tool.md> (full page fetched)
- **watsonx Orchestrate — AI Agent Builder** and the **June 2026 / April 2026 release notes** —
  <https://www.ibm.com/products/watsonx-orchestrate/ai-agent-builder>,
  <https://www.ibm.com/docs/en/watsonx/watson-orchestrate/base?topic=releases-release-notes-june-2026>

## 1. The state we are integrating into

Read from source, not from a doc. `backend/app/llm/watsonx_client.py` is 20 lines:

```python
async def complete(prompt: str, max_tokens: int = 512) -> str:
    if not WATSONX_API_KEY:
        raise RuntimeError("WATSONX_API_KEY unset — set MOCK_LLM=true for fixture mode")
    async with httpx.AsyncClient(base_url=WATSONX_URL, timeout=30) as _client:
        raise NotImplementedError("watsonx.ai call pattern lands after research spike")
```

- The hole is exactly one function. `httpx` is already a pinned dependency (0.28.1).
- The contract to preserve is `async complete(prompt: str, max_tokens: int = 512) -> str`.
  **M5 and M7 depend on that exact shape — do not widen it during the spike.**
- `config.py` binds at import: `WATSONX_API_KEY`, `WATSONX_PROJECT_ID`, `WATSONX_URL`
  (default `https://us-south.ml.cloud.ibm.com`), `MOCK_LLM`, `ARTIFACT_DIR`.
- `mock_client.complete()` returns `'{"verdict": "PENDING", "rationale": "mock — no live call"}'`,
  and `test_llm.py` asserts the output parses as JSON with `verdict == "PENDING"`. **The live
  client must be able to satisfy the same assertions** — that is a free contract to hold.
- `test_llm.py` has 7 tests, including `test_watsonx_with_key_makes_no_network_call`, which
  proves `httpx` `send()` is never reached. There is also a `live_llm` marker already declared in
  `pyproject.toml` and never selected in CI — the live test has a home.

## 2. Authentication — two steps, and the token is short-lived

**[SOURCED]** The API key is **not** the inference credential. IBM Cloud IAM exchanges it for a
bearer token first:

```
POST https://iam.cloud.ibm.com/identity/token
Content-Type: application/x-www-form-urlencoded

grant_type=urn:ibm:params:oauth:grant-type:apikey&apikey=<WATSONX_API_KEY>
```

Response: `access_token`, `refresh_token` (`"not_supported"` for the apikey grant),
`token_type: "Bearer"`, `expires_in: 3600`, `expiration`, `scope: "ibm openid"`.

Every inference call then carries `Authorization: Bearer <access_token>`.

### **[CORRECTED] The token lives one hour, not thirty days

An earlier conversational claim in this session was that the token is long-lived (30 days) and
that one exchange per process would do with no refresh. **That was wrong.** The IAM docs are
explicit: *"An access token is a temporary credential that expires after 1 hour at the latest"*
and *"An IAM token is valid for up to 60 minutes, and it is subject to change. When a token
expires, you must generate a new one. Use the property `expires_in`."* The response body in the
vendor's own example shows `expires_in: 3600`. The 30-day figure belongs to the *delegated
refresh token* from the separate refresh flow, not to the apikey grant.

**Why this matters more than it looks:** a permanent module-level token cache would have passed
every test we could write, then failed the live demo at minute 61. This is exactly the class of
defect the read-only verifier we are building exists to catch, and it is worth naming in the
pitch. The client must cache the token **with its `expires_in`** and re-exchange on expiry.

### Two auth paths, pick deliberately

**[SOURCED]** watsonx also accepts the API key directly, HTTP basic auth
(`curl -u "apikey:<KEY>"`). The vendor's guidance: *"For testing and development, you can pass an
API key directly. However, for production use … use an IAM token. When you pass an API key, the
service looks up the API key details, so it might affect performance."*

**[PROPOSED]** Support both: direct key for the smoke test (one less moving part while we discover
whether the account works at all), IAM exchange for the real path. Config gains
`WATSONX_IAM_URL` and `WATSONX_AUTH_MODE` (`iam` | `apikey`).

## 3. Inference call pattern — three candidates, one winner

**[SOURCED]** All three take `model_id`, `project_id` or `space_id`, generation controls, and
return `usage.{prompt_tokens, completion_tokens, total_tokens}`.

| Endpoint | Shape | Verdict |
|---|---|---|
| `POST /ml/v1/deployments/{id}/text/generation` | `input` (string prompt), `space_id`, `parameters` | **Reject.** Marked *"This API is legacy, consider using Deployment Text Chat."* Also needs a deployment id — a provisioning step we do not want in the 48h. |
| `POST /ml/v1/text/chat` | `messages[{role, content}]`, plus `tools`, `response_format`, `guided_*` | **Use this.** Same gateway, chat-shaped, carries a `system` message — which is where the attestor policy prompt belongs. |
| `POST /v1/chat/completions` | OpenAI-compatible | **Reject for now.** The reference pages return **two different response envelopes** for this endpoint (`completion`/`stop_reason` at top level on one page, `choices[].message.content` on another). Do not build the response parser against an ambiguous contract on demo day. |

The `/ml/v1/text/generation` request also offers a `moderations` block
(`hap` hate/profanity, `pii` with `remove_entity_value`) — **[PROPOSED]** leave off. It is for
user-facing text, and it would silently mutate the code and diff text our verifier reasons over.

**Version query parameter.** The reference examples carry `?version=YYYY-MM-DD`. **[UNVERIFIED]**
whether the version is optional on `/ml/v1/text/chat`. Pin it once, empirically.

## 4. Structured output — the most useful thing in these docs

**[SOURCED]** `response_format` has two modes:

- `{"type": "json_object"}` — guarantees a valid JSON object. Vendor caveat: *"it's crucial to
  instruct the model to produce JSON via a system or user message to prevent potential issues like
  unending whitespace or generation exceeding token limits."* Our mock already returns JSON, so
  the live client can satisfy the same tests.
- `{"type": "json_schema", "json_schema": {...}}` — **Structured Outputs: the model is constrained
  to match a supplied JSON schema.**

Plus guided decoding: `guided_choice` (one of a fixed list), `guided_regex`, `guided_grammar`
(context-free grammar), `guided_json` (a JSON schema).

**[PROPOSED]** This is worth more than it first appears. Our contracts-first convention
(`contracts/*.schema.json` is the boundary between modules) currently has **no enforcement point
on model output at all** — a gate parses prose and hopes. `guided_json` pointed at
`verdict.schema.json` makes the contract the model's output grammar. That turns
"the schema is the contract" from a doc claim into a runtime guarantee, and it is the single
highest-leverage integration available to us. It also lets M8 fail closed on a malformed verdict
by construction rather than by defensive parsing.

## 5. Model selection and spend

**[SOURCED]** `GET /ml/v1/foundation_model_specs` (filterable by `model_id`, `provider`, `source`,
`tier`, `task`, `lifecycle_state`, `function`) returns each model's `model_id`, `label`,
`provider`, `tasks`, `number_params`, and `input_tier` / `output_tier` — e.g. `class_2` on the
starcoder example. Lower tier classes are the cheaper classes. `GET /ml/gateway/v1/models` is the
AI Gateway model list (OpenAI-shaped `data[].id`).

**[UNVERIFIED]** which model ids this account can actually reach, and at what tier. **Do not
hardcode a guessed model id.** One call to `foundation_model_specs` against the real account
settles it; `WATSONX_MODEL_ID` becomes a required config value, not a constant.

**[SOURCED]** The spend meter we need for **D11** is already in every response: `usage.prompt_tokens`
/ `completion_tokens` / `total_tokens`. We do not have to estimate — we can count. **[PROPOSED]**
accumulate per run and store with the run record; that is the burn plan's raw material, and it is
free.

**[SOURCED] Rate limits.** `429` with error code `rate_limit` and a message naming the IBMid
(`"The requests from IBMid-310000A00A exceeds rate limit. Please try again later."`). There is
also a per-tenant rate-limit configuration API (`POST /ml/gateway/v1/rate_limits`, shaped
`{request: {amount, capacity, duration}, token: {...}}`) — **[PROPOSED]** do not touch it during
the build (same reasoning as **D10**: not during the build). Handle `429` with bounded
exponential backoff and let the D11 ceiling be the real guard.

## 6. The finding that changes an architecture decision: watsonx Orchestrate

Our differentiator is a read-only verifier (M12, **D6**). `backend/app/attestor/policy.py` today
asserts a `frozenset` against itself — `GRANTS = {read, subagent, skill, workflow}`,
`DENIES = {edit, execute}` — and `docs/architecture.md` §11 gap 5 records the blunt version:
*"`assert_read_only` is test-only; pipeline never calls it."* **D6** asks where read-only is
enforced. It currently is enforced nowhere.

> **SUPERSEDED as an as-built claim, 2026-09-27 (Session 22).** The paragraph above is a
> point-in-time snapshot and is deliberately left as written — this is a research dossier,
> not the as-built record, and `docs/architecture.md` §8 is the authority on what the code
> does. Three of its statements are now false: there are **five** grants rather than four
> (`llm_egress` was added as an OS-level property, not a harness group), and the module is
> no longer a set comparison against itself — `attestor/sandbox.py` exists and obtains
> exactly the evidence §7 below asked for. What has **not** changed is the part that
> matters: it is still enforced nowhere in the pipeline, and the D6 read-only bind mount
> still does not exist. §7's recommendation is implemented; the control is still unwired.

**[SOURCED]** watsonx Orchestrate ships the primitive:

- **Python tools execute in an isolated container with a read-only filesystem.** The docs state
  verbatim: *"For security and stability, tools execute in a **read-only filesystem**. Each tool
  can access only its own filesystem and cannot modify files during execution."* This is an
  OS-level guarantee, not a prompt.
- ADK package `ibm_watsonx_orchestrate`, `@tool` decorator, JSON Schema inferred from type hints
  or pydantic, `expected_credentials` bound to platform **connections** (basic / bearer / API key /
  OAuth / key-value), **MCP** server import, `orchestrate tools import` / `toolkits add` CLI.
- The tools runtime supports **Python 3.12 only** — which happens to match our pending 3.12
  upgrade, so nothing is lost whichever way we go.

### The caveat we must not skip

**[SOURCED]** `ToolPermission` is flagged `deprecated="true"` in the `@tool` reference. It used to
control whether an agent asks the user to confirm an action, and: *"This behavior has been
deprecated and removed; it no longer occurs."* So the enum is **not** a live control. What is live
and enforced is the **read-only filesystem sandbox**.

**Consequence for the pitch:** we must claim the *filesystem sandbox*, never
`ToolPermission.READ_ONLY`. Adrian's proposal predates this and refers to a Bob-era custom mode;
we should cite the current Orchestrate docs instead of the PDF on this point. An IBM judge will
notice the difference, and so will the false-certified-rate benchmark if our own verifier's
read-only claim is a prompt rather than a control.

### **[SOURCED] The model default flips — this one bites**

Per the June 2026 Orchestrate release notes, *"prebuilt agents in watsonx Orchestrate AWS and IBM
Cloud deployments use the Groq-hosted model, while those in on-premises and AWS GovCloud
deployments use the watsonx.ai-hosted model."* The default builder model is `groq/openai/gpt-oss-120b`.

So adopting Orchestrate without explicitly binding the model **silently moves our inference off
watsonx.ai**, violating Convention 8 ("All LLM reasoning via watsonx.ai"). It would have to be
pinned through AI Gateway on day one. Another reason to keep Orchestrate out of the critical path.

## 7. Recommendation

**Use the watsonx.ai REST API for inference. Do not adopt Orchestrate for the gate logic. Adopt its
read-only sandbox as the design template for M12 / D6.**

Reasons: Orchestrate is a deployment platform — Kubernetes, tenant package allowlists, draft/live
environments, 100–300 ms per-call process overhead for standalone tools — and we have a 40-file
FastAPI monolith and ~40 hours. Putting provisioning in front of the critical path
`M1→M2→M4→M5→M6→M7→M8→M9→M10→M15` to obtain a property we can get from a bind mount is a bad
trade. But the sandbox tells us exactly what to imitate: **M7b's worker pool should run with the
workspace read-only**, and `assert_read_only` should become a real pre-flight capability check at
worker startup rather than a set comparison. That converts **D6**'s "a one-line change that makes
the read-only differentiator a control rather than a claim" into an actual OS-level control — and
it is demonstrable live in the demo.

## 8. Concrete changes to `watsonx_client.py` — the shape to code against

Not yet written. The recommended decomposition:

1. **`_iam_token()`** — POST the apikey grant to `WATSONX_IAM_URL`, form-encoded. Cache the
   `access_token` **together with its `expires_in`**; re-exchange when stale with a safety margin
   (e.g. refresh at 80% of lifetime). Skip entirely when `WATSONX_AUTH_MODE=apikey`.
2. **`complete()`** — POST `/ml/v1/text/chat`, `messages = [{system: attestor policy}, {user: prompt}]`,
   `temperature=0` (verdicts must be deterministic), `max_tokens` from the existing signature,
   `response_format={"type": "json_object"}` — and `guided_json` against the target contract schema
   once **D1** fixes which schema that is. Return the message content string; keep the signature.
3. **`429`** → bounded exponential backoff. Any other error → raise loudly. Never fall through to
   a fabricated verdict.
4. **Meter every call** — accumulate `usage` into the run record. This is D11's input.
5. **Fail closed on a live error** — the demo degrades to `mock_client`/fixtures, it does not
   crash and it does not silently produce a passing verdict.

`config.py` additions: `WATSONX_IAM_URL`, `WATSONX_MODEL_ID`, `WATSONX_AUTH_MODE`,
`WATSONX_MAX_RETRIES`, `WATSONX_MAX_TOKENS_PER_RUN` (D11).

## 9. Test plan changes this implies

Per `docs/test-suite.md` conventions — never a live call in the suite; characterization tests flip
deliberately with the gap they pin.

- `test_watsonx_with_key_pending_spike` **flips**: it currently asserts `NotImplementedError`.
  When the client lands, it becomes a mocked-transport test asserting the **request body**
  (endpoint, `temperature=0`, `response_format`, model id) and the response parse. Flip it in the
  same commit that lands the client.
- `test_watsonx_with_key_makes_no_network_call` changes meaning: it proved *absence* of a request
  before `NotImplementedError` fired. It should keep its zero-network property under the test
  suite, but for a different reason — the default is `MOCK_LLM=true`. Rewrite its docstring, do not
  silently repurpose it.
- New: token-cache TTL test using a fake clock (assert re-exchange happens before expiry — the
  defect in §2), `429` backoff test, `usage` metering test, and a `live_llm`-marked smoke test
  that CI never selects.

## 10. What is still open — needs a real account

Nothing below is answerable from documentation. These are the M11 items that remain, and they are
the *only* thing standing between this dossier and a live call.

1. **Is watsonx.ai provisioned at all?** An IBM Cloud account with a watsonx.ai service instance
   and an IAM API key. Until this is answered, no live call is possible and M7's demo path stays
   mock-first (**D12**).
2. **Region.** `config.py` defaults to `us-south`. The instance URL must come from *Show
   Credentials* on the actual instance.
3. **Model id + tier** — one `GET /ml/v1/foundation_model_specs` call settles it (§5).
4. **Burn plan** — tokens per run, runs per demo, per-criterion-group ceiling (**D11**). The
   `usage` block gives us the numerator; the denominator needs a real run.
5. **Does `?version=` matter**, and does `guided_json` work on the model we can reach (§3, §4).

## 11. Effects on the rest of the plan

- **D1 (E0–E6 ladder) gains weight.** `guided_json` is only as good as the schema it points at, and
  the ladder is currently named but never defined. Ratifying **D1** is now on the critical path
  *and* it unblocks the cleanest output-validity story we have.
- **D6 gains an answer.** Recommended default is unchanged ("assert at worker startup, fail
  closed") but the *mechanism* is now specified: read-only workspace bind mount + a pre-flight
  capability check, modelled on Orchestrate's sandbox.
- **D11 gains a data source.** Token counts come back in every response; only the policy is open.
- **Convention 8 stays true** only if we stay on the REST API, or explicitly bind the model on
  Orchestrate. Flagged in §6.
- **The read-only claim in the pitch gets sharper.** "The verifier cannot modify what it verifies"
   is currently a `frozenset` assertion with no call site. A read-only bind mount makes it a
   property of the process. Worth a demo slide.

## Session log (append-only)

### 2026-09-27 — Session 15: watsonx.ai integration research (this file created)
- Instruction: study watsonx.ai documentation and determine how it integrates into the system;
  then document and commit.
- Read `backend/app/llm/watsonx_client.py`, `llm/mock_client.py`, `llm/__init__.py`,
  `app/config.py`, `app/attestor/policy.py`, `backend/tests/test_llm.py`, and
  `docs/architecture.md` §7/§8/§11 directly. **Docs-only: no code, no contracts, no fixtures, no
  dependencies, no endpoint changes.**
- Four Context7 queries against the watsonx.ai API reference; fetched the full Orchestrate ADK
  page; read the IAM token docs, the watsonx auth docs, and the Orchestrate June/April 2026
  release notes.
- **Answers the spike:** auth is a two-step IAM apikey→bearer exchange; `/ml/v1/text/chat` is the
  endpoint; `response_format` (`json_object` / `json_schema`) and `guided_json` are available and
  should constrain output to our contracts; `usage` gives us the D11 meter; `429` is the rate
  limit to back off.
- **Self-correction carried into §2:** an earlier claim in this session that the IAM token lasts
  30 days and needs no refresh was **wrong** — `expires_in` is 3600s and the vendor docs require
  re-exchange. A permanent token cache would have passed every test and failed the demo at minute
  61. The client spec is TTL-aware as a result.
- **Honest negative results recorded rather than smoothed over:** `ToolPermission.READ_ONLY` is
  deprecated and is not a live control (the read-only *filesystem* is); Orchestrate defaults to a
  Groq-hosted model on IBM Cloud, which would silently violate Convention 8; the
  `/v1/chat/completions` envelope is documented inconsistently across two reference pages, which
  is why it was rejected rather than preferred.
- **Open at archive:** all five items in §10 need a provisioned account — provisioning, region,
  model id, burn plan, and the `version`/`guided_json` behaviours. M11 stays unimplemented. D1
  becomes more urgent, not less. No decision was taken and no module brief was rewritten.
