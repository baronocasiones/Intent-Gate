# docs/architecture.md — Intent Attestation Gate (software architecture)

Code-faithful record of the system as built. Conceptual model (6 stages, probe model,
governance claim, metric) lives in `docs/intent-attestation-gate.md` — this file describes
how the code implements it, endpoint by endpoint, module by module. Single source for the
idea remains `IBM BOB.pdf` (Adrian, pp. 14–25).

Status: **scaffold** — FastAPI process boots, pipeline stub path runs end-to-end,
contract validator passes; gates/routers/store return stubs or TODOs (see §11 gaps).
Last verified against code: **2026-09-27** (this session).

## 1. Runtime shape

One Python process (modular monolith). No workers, no sidecars, no message bus:

```
GitHub webhook (or injected payload, same endpoint)
  → POST /webhooks/github (backend/app/routers/webhooks.py)
    → enqueue_run() → run_id (in-memory id only today)
      → run_pipeline(): ingest → extract → parse → verify → adjudicate → emit
        → SQLite runs row + JSON artifact under ARTIFACT_DIR
          → GET /api/runs, GET /api/runs/{id}, GET /api/metrics
            → React dashboard (served as static dist by the same FastAPI app when built,
               Vite dev proxy otherwise) — live-API first, fixture fallback
```

Async execution path (`backend/app/orchestrator/jobs.py`: in-process `asyncio.Queue` +
`worker()`) exists but is **not wired**: `enqueue_run()` mints `run-{8 hex}` and returns
without calling `submit()`, and nothing ever starts `worker()`. The synchronous
`run_pipeline()` is the only path exercised (by `tests/test_scaffold.py`).

Figure 6 (`docs/Figure-6-System-Architecture.png`) is the visual twin of this shape:
6 stage boxes, `attestor` policy box, Budget Governor metering note, traceability /
signer / ledger / exposure / receipt surfaces. Known figure gaps (kept as-is from
Session 7/10): false-certified rate + 7 mutation classes appear nowhere in the figure.

## 2. Entry point

`backend/app/main.py` — `FastAPI(title="Intent Attestation Gate", version="0.1.0")`.
Includes the three routers, exposes `GET /health` → `{"ok": true, "service:
"intent-attestation-gate"}`. Serves the built dashboard by mounting `frontend/dist`
at `/` **only if that directory exists** (API-first otherwise).

> Known defect (documented, not fixed this session): the `_dist` resolution climbs three
> levels from `backend/app/` (`".." , "..", "..", "frontend", "dist"`), which lands at
> `<repo-parent>/frontend/dist` instead of `<project>/frontend/dist`. Correct climb is
> two levels. Effect today: the `isdir` check silently fails and the app runs API-only
> even when `frontend/dist` is built.

## 3. Components → code paths

| Concern | Code | State |
|---|---|---|
| Webhook ingress | `backend/app/routers/webhooks.py` — `POST /webhooks/github` | parses JSON body, calls `enqueue_run(payload)`, returns `{"run_id", "queued"}`. No signature check, no tunnel requirement (injected payloads hit the same endpoint) |
| Run pipeline | `backend/app/orchestrator/pipeline.py` — `enqueue_run()` / `run_pipeline()` | `enqueue_run` mints id only; `run_pipeline` calls the six gates in order, synchronously |
| Job queue | `backend/app/orchestrator/jobs.py` — `submit()` / `worker()` | exists, unwired (see §1) |
| Stage 1 Ingest | `backend/app/gates/ingest.py::run(payload)` | stub: `{"stage": "ingest", "ok": True, "input_keys": sorted(payload.keys())}` |
| Stage 2 Extract | `backend/app/gates/extract.py::run(bundle)` | stub: `{"stage": "extract", "ok": True, "criteria": []}`. Spec: atomic criteria, ISO/IEC/IEEE 29148 quality gate, untestable rejected |
| Stage 3 Parse | `backend/app/gates/parse.py::run(criteria)` | stub: `{"stage": "parse", "ok": True, "ast": []}`. Spec: cucumber/gherkin → AST, **no model in this loop** |
| Stage 4 Verify | `backend/app/gates/verify.py::run(ast)` | stub: `{"stage": "verify", "ok": True, "findings": []}`. Spec: N workers (OS processes, not model subagents), 5 static probes (`CODE_SEARCH`, `LOGIC_TRACE`, `STATE_CHECK`, `ERROR_PATH`, `ABSENCE_CHECK`) + adversarial pass over 7 failure classes; LLM via watsonx.ai only |
| Stage 5 Adjudicate | `backend/app/gates/adjudicate.py::run(findings)` | stub: `{"stage": "adjudicate", "ok": True, "verdict": "PENDING"}`. Spec: E0–E6 ladder → `CERTIFIED` / `CONDITIONAL` / `REJECTED` |
| Stage 6 Emit+gate | `backend/app/gates/emit.py::run(verdict)` | stub: `{"stage": "emit", "ok": True, "exit_code": 1, "record": verdict}`. Spec: traceability matrix, signed hash-chained record, debt ledger, risk-weighted exposure; non-zero exit blocks merge |
| Read-only policy | `backend/app/attestor/policy.py` — `GRANTS={read,subagent,skill,workflow}`, `DENIES={edit,execute}`, `assert_read_only(granted)` | raises `PermissionError` on leaked denies or missing grants. Enforced in tests only today, not in the pipeline path (see §11) |
| LLM — live | `backend/app/llm/watsonx_client.py::complete(prompt, max_tokens=512)` | raises `RuntimeError` when `WATSONX_API_KEY` unset; otherwise raises `NotImplementedError` — IAM exchange + generation call land after the research spike |
| LLM — mock | `backend/app/llm/mock_client.py::complete(...)` | deterministic `'{"verdict": "PENDING", "rationale": "mock — no live call"}'`; zero spend |
| Metric | `backend/app/metrics/false_certified.py` — `OPERATORS` (7) + `false_certified_rate(results)` | `P(CERTIFIED \| spec violation present)`; returns `{false_certified_rate, measured, by_operator}`; `measured = total > 0`; `None` rate when empty |
| Schemas | `backend/app/models/schemas.py` — `CriterionVerdict`, `RunRecord`, `Verdict`, `EvidenceTier` literals | pydantic v2; verdicts carry `criterion_id, verdict, evidence_tier, locations[], rationale`; `measured: bool` on runs |
| Persistence — index | `backend/app/db.py` — `get_db()` + `SCHEMA` | SQLite, `PRAGMA journal_mode=WAL`, one table `runs(id, status, created_at, artifact_path)`. No caller yet |
| Persistence — artifacts | `backend/app/store/artifacts.py::write_artifact(run_id, payload)` | writes `$ARTIFACT_DIR/{run_id}.json` as `{"sha256": <of sorted body>, **payload}`; `makedirs` on demand. No caller yet |
| Config | `backend/app/config.py` + `backend/.env.example` | env-driven: `WATSONX_API_KEY/PROJECT_ID/URL` (default `https://us-south.ml.cloud.ibm.com`), `DATABASE_URL` (`sqlite:///./attestation.db`), `MOCK_LLM` (`"true"` → mock), `ARTIFACT_DIR` (`./artifacts`). Secrets never committed (`.gitignore` covers `.env`) |

## 4. Data flow (as coded)

1. `POST /webhooks/github` receives any JSON payload (real GitHub event or hand-injected demo body — same path, tunnel-independent).
2. `enqueue_run(payload)` returns `run-{uuid4[:8]}`. Nothing is persisted, nothing is queued.
3. When `run_pipeline(payload)` is invoked (tests only, today), each gate's `run()` passes its stub dict to the next: payload → bundle → criteria → ast → findings → verdict → record.
4. Terminal stub output today: `{"stage": "emit", "ok": True, "exit_code": 1, "record": {"stage": "adjudicate", ...}}` — exit 1 = blocked, which is the safe default for a gate.
5. Intended (not yet coded): persist `runs` row + `write_artifact()` hash-chained JSON, serve via `/api/runs*`, aggregate metric via `/api/metrics`.

## 5. API surface

| Method + path | Router | Today | Spec target |
|---|---|---|---|
| `GET /health` | `main.py` | live `{"ok": true, ...}` | same |
| `POST /webhooks/github` | `routers/webhooks.py` | live (id mint, no persistence) | + HMAC check, persist run, submit to queue, GitHub check-run write-back |
| `GET /api/runs` | `routers/runs.py` | stub `{"runs": []}` (`TODO: query SQLite`) | list from `runs` table |
| `GET /api/runs/{run_id}` | `routers/runs.py` | stub `{"run_id", "pending"}` (`TODO: load from store`) | run + artifact pointers |
| `GET /api/metrics` | `routers/metrics.py` | stub `{false_certified_rate: None, measured: False, by_operator: {}}` (`TODO: aggregate`) | aggregate `false_certified_rate()` over mutation runs |

No auth, no SSE/polling, no GitHub comment/check-run write-back yet (all were old-idea open items; re-decide under the new idea).

## 6. Persistence

- **Index:** SQLite WAL single file (`./attestation.db` default). Schema is one table (`runs`). WAL mode set on every `get_db()`. No migrations, no callers.
- **Artifacts:** JSON files under `ARTIFACT_DIR`, each self-describing with a `sha256` of its own sorted body (hash-chained *record* in the weak sense: tamper-evident per file; no cross-file chain yet — that is spec-future).
- **Convention (carried):** envelope + artifact-pointer integration — API returns small records pointing at artifact files, never giant blobs inline.

## 7. LLM layer + spend discipline

- All verification reasoning goes through `llm/watsonx_client.py::complete()`. No other model call sites exist.
- `MOCK_LLM=true` selects `mock_client` (deterministic, zero spend). Live path without `WATSONX_API_KEY` fails loud with `RuntimeError` (fixture-backed fallback, never silent).
- Hour-one spike still open: IAM token exchange + generation-endpoint call pattern + burn plan (carried from Session 6 open decisions, reworded watsonx-only in Session 10).

## 8. Read-only attestor (differentiator, as coded)

`GRANTS = {read, subagent, skill, workflow}`; `DENIES = {edit, execute}`. `assert_read_only()` fails closed on either leak or incompleteness. The N-worker fan-out in Stage 4 is N **OS processes**, not model-invoked subagents (this is what the Figure 6 footer note means; the fleet-flags string `--disable-subagents` vs the granted `subagent` cap is a known wording tension kept as-is from Session 7). **Never weaken this in demo shortcuts** (standing convention).

## 9. Publishable metric (as coded)

`FALSE CERTIFIED RATE = P(CERTIFIED | spec violation present)`, computed by
`metrics/false_certified.py::false_certified_rate()` over 7 operator classes:
`boundary_drop, comparison_inversion, threshold_weakening, error_path_deletion,
normative_demotion, negative_constraint_removal, untestability`. Output shape matches
`contracts/exposure.schema.json` (`{false_certified_rate: number|null, measured: bool,
by_operator}`). Corroborating ground truth per spec (Stryker "Survived" mutants) is not
wired yet.

## 10. Contracts, fixtures, validator, frontend

- **Contracts** (`contracts/*.schema.json`, draft-07): `criterion` (`criterion_id, text, testable`), `verdict` (verdict enum + E0–E6 tier + `locations[]` + `rationale`), `run` (`run_id, status, verdicts[], measured`), `traceability` (`run_id, links[{criterion_id, locations[], evidence_tier}]`), `exposure` (`false_certified_rate, measured, by_operator`). `run` → `verdict` via `$ref`.
- **Fixtures** (`fixtures/`): `demo_run.json` (run `demo`, `PENDING`, `measured: false`, AC-1/AC-2 E0 stubs), `demo_traceability.json` (matching links). These **are the frontend's API** until backends land.
- **Validator** (`scripts/validate_contracts.py`): validates the two pairs (`run↔demo_run`, `traceability↔demo_traceability`) with `$ref` store resolution; exit non-zero on failure. stdlib + `jsonschema` only.
- **Frontend** (`frontend/`, React 18 + Vite 6): `App.jsx` fetches live (`api.js: fetchRun/fetchMetrics`, graceful `null` on failure) then falls back to `fixtures.js` (mirrors `demo_run.json`); banner shows `(fixture mode)` when not live. Four components: `VerdictBadge` (green/red/orange), `EvidenceLadder` (E0–E6 counts), `TraceabilityMatrix` (criterion/verdict/tier/locations table), `ExposureCard` (rate or `unmeasured`, measured/fixture tag). Dev proxy (`vite.config.js`) forwards `/api` + `/webhooks` to `127.0.0.1:8000`. Production serving is via FastAPI static mount (subject to the §2 path defect).

## 11. Gaps (honest list — what "stub" actually means)

1. `enqueue_run` never persists, never submits to `jobs` queue; `worker()` never started.
2. `GET /api/runs*` and `GET /api/metrics` return hard-coded stubs; `db.get_db` / `write_artifact` have no callers.
3. Gates return shape-correct stubs with empty payloads (`criteria: []`, `ast: []`, `findings: []`, `verdict: PENDING`).
4. `watsonx_client.complete` is `NotImplementedError` past the key check — research spike pending.
5. `assert_read_only` is test-only; pipeline never calls it.
6. §2 `_dist` path defect (three-level climb, should be two).
7. Missing vs spec: GitHub write-back (comments + check runs), review-debt ledger, risk-weighted exposure decay curve, signed cross-file hash chain, SSE/polling, auth, real demo-repo target.
8. Dependencies pinned in `backend/requirements.txt`: fastapi 0.135.3, uvicorn 0.44.0, pydantic 2.13.0, httpx 0.28.1, jsonschema 4.26.0, pytest 9.0.3, pytest-asyncio 1.4.0. Smoke tests in `backend/tests/test_scaffold.py` (pipeline stub path, policy guard, metric-empty) are the only coverage.

## 12. Monorepo layout (as on disk)

```
AGENTS.md
docs/intent-attestation-gate.md   module record (concept)
docs/architecture.md              this file (code record)
docs/Figure-6-System-Architecture.png
docs/evidence-dossier.md, docs/market-sizing-2026-09.md,
docs/ai-code-review-landscape-2026-09.md, docs/Figure-[1-5]*.png
backend/requirements.txt  backend/.env.example
backend/app/main.py  backend/app/config.py  backend/app/db.py
backend/app/routers/{webhooks,runs,metrics}.py
backend/app/gates/{ingest,extract,parse,verify,adjudicate,emit}.py
backend/app/orchestrator/{pipeline,jobs}.py
backend/app/llm/{watsonx_client,mock_client}.py
backend/app/attestor/policy.py
backend/app/metrics/false_certified.py
backend/app/models/schemas.py
backend/app/store/artifacts.py
backend/tests/test_scaffold.py
contracts/*.schema.json  fixtures/demo_*.json  scripts/validate_contracts.py
frontend/src/{App.jsx,main.jsx,api.js,fixtures.js,components/*}
frontend/{index.html,package.json,vite.config.js}
```

## Session log (append-only)

### 2026-09-27 — Session 11: architecture documented (this file created)
- `/start` with instruction "document the software architecture": parsed target (software architecture) + goal (document it); re-read `AGENTS.md` (through Session 8 archive) and `docs/intent-attestation-gate.md` (through Session 10); found `docs/architecture.md` absent (void since Session 6 purge) while a real scaffold exists on disk.
- User confirmed: new `docs/architecture.md`, code-faithful depth.
- Wrote this file from direct reads of every backend module, all 5 contracts, the validator, both fixtures, `App.jsx`/`api.js`/`fixtures.js`/4 components, `requirements.txt`, tests, `.env.example`, `.gitignore`. No code changed.
- Findings recorded as gaps (§11), including the `_dist` three-level-climb defect and the unwired `jobs` queue — flagged, not fixed, pending user go.
- Open for next session: fix §11 items in priority order; regenerate Figure 6 if code diverges from it; update `AGENTS.md` repo-state (still lists 3 files vs the real tree).
- Committed as `dc8493a` on branch `baron` per user request (docs-only commit; pre-existing working-tree `M docs/intent-attestation-gate.md` + `D gen_fig6_architecture.py` + `__pycache__/` left unstaged, none this session's).

### 2026-09-27 — Session 13: test suite + CI recorded (supplementary note)
- Test suite established per this record: `pyproject.toml` (pytest-only config at repo root), `.github/workflows/tests.yml` (push/PR/dispatch, matrix py3.11+py3.12 → pytest + `scripts/validate_contracts.py`), 9 new `backend/tests/test_*.py` files, `.gitignore` hygiene (`__pycache__/`, `*.pyc`, `.pytest_cache/`) — committed as `303241e` on `baron`; `backend/.python-version` → `3.12.14` committed as `fe8ab25`.
- §11.8 superseded by measurement: the "only coverage = 3 smokes" claim held only pre-Session-13 — suite is now **79 tests green on 3.11.9 and 3.12.14** (full CI matrix rehearsed locally, validator OK ×2 both legs).
- Module record for all test-suite matters lives in **`docs/test-suite.md`** (layout, §→test coverage map, conventions, gaps, session log); this file remains authoritative for the system itself.
