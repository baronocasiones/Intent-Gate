# docs/test-suite.md — Intent Attestation Gate (test suite)

Append-only module record for the project's test suite. Architecture context
lives in `docs/architecture.md` (code-faithful) and `docs/intent-attestation-gate.md`
(concept); this file records only how the suite is organized, run, and extended.

Status: **scaffold + architecture-derived unit tests + M1 contracts guard** — 89 tests
(79 pre-existing + 10 new in `test_schemas_contracts.py`). Last verified 2026-09-27 on
Python **3.14.7** (isolated `/tmp/opencode/venv`, `PYTHONDONTWRITEBYTECODE=1 -p no:cacheprovider`).
The 79-test baseline is green on 3.11.9 and 3.12.14 per Session 13 and Session 17 records.
**3.14.7 is not the CI matrix (3.11 + 3.12) — one CI run is owed** for this session's 10
new tests before they are trusted on the matrix.

## Layout

```
pyproject.toml                     pytest config only (not an installable package)
.github/workflows/tests.yml        CI: matrix py3.11/py3.12 → pytest + contract validator
backend/requirements.txt           runtime + test deps (pytest 9.0.3, pytest-asyncio 1.4.0)
backend/tests/
  __init__.py                      makes pytest put backend/ on sys.path (imports are `app.*`)
  test_scaffold.py                 Session-11 smoke tests (pipeline, policy, metric-empty)
  test_gates.py                    §3 stage stubs: shapes, stage order, exit_code=1 blocks
  test_pipeline.py                 §1/§4 chaining, run-id format, §11.1 unwired-queue characterization
  test_policy.py                   §8 attestor GRANTS/DENIES exact sets, fail-closed both ways
  test_metric.py                   §9 seven operators, rate math, exposure-schema conformance
  test_llm.py                      §7 mock determinism; watsonx fails loud; zero-network proof
  test_schemas_contracts.py        §10 pydantic↔contract parity, fixture validation, validator wrap;
                                   coverage check (every schema paired), example validation
                                   (verdict, criterion, exposure, findings), probe-enum pin,
                                   uncovered_schemas unit tests (2), result-unenumerated +
                                   tier-not-required pin
  test_api.py                      §5 route table + health/webhook/stub endpoint shapes
  test_store_db.py                 §6 WAL mode, runs table, sha256-of-sorted-body artifacts
  test_config.py                   §3 env defaults/overrides, MOCK_LLM parsing, reload-restore
```

## How to run

```bash
# from the repo root (CI runs exactly this):
pytest                                  # uses pyproject testpaths → backend/tests
python scripts/validate_contracts.py    # contracts ↔ examples + fixtures gate (exit non-zero on fail)
```

No setup beyond `pip install -r backend/requirements.txt`. The suite never
needs network access, a database file, or watsonx.ai credentials.

## Coverage map (docs/architecture.md § → test file)

| § | Concern | Test file |
|---|---|---|
| §1/§4 | runtime shape, data flow, pipeline chain | `test_pipeline.py` |
| §3 | six gates, schemas, config, LLM clients, metric, policy | `test_gates.py`, `test_schemas_contracts.py`, `test_config.py`, `test_llm.py`, `test_metric.py`, `test_policy.py` |
| §5 | API surface (health, webhook, runs, metrics) | `test_api.py` |
| §6 | persistence (SQLite WAL, hash-sha256 artifacts) | `test_store_db.py` |
| §7 | LLM dual-mode + spend discipline | `test_llm.py` |
| §8 | read-only attestor (the differentiator) | `test_policy.py` |
| §9 | false-certified-rate metric (the "THE NUMBER") | `test_metric.py` |
| §10 | contracts (6 schemas), fixtures (2), validator (6 pairs + coverage check) | `test_schemas_contracts.py` |
| §11 | honest gaps — characterized, not hidden | `test_pipeline.py` (queue), `test_llm.py` (spike pending) |

Figure 6 (`docs/Figure-6-System-Architecture.png`) is the visual cross-check:
the attestor box ↔ `test_policy.py`, the metering note ↔ `test_llm.py` /
`test_config.py`, the stage boxes ↔ `test_gates.py`.

## Conventions

1. **Never a live LLM call.** Live client is exercised only up to its loud
   failure points (`RuntimeError` without key, `NotImplementedError` past the
   spike); the zero-network property is asserted with a spy client. The
   `live_llm` marker is reserved for future opt-in tests and must stay
   unselected in CI.
2. **Import-time bindings are patched on the consumer module.**
   `config.py` reads env at import, so `monkeypatch.setattr(watsonx_client,
   "WATSONX_API_KEY", ...)` — not `setenv` — is the correct lever;
   `test_config.py` uses `importlib.reload` with snapshot-restore instead.
3. **tmp_path discipline.** DB/artifact tests receive paths under `tmp_path`
   (or patch `ARTIFACT_DIR`) — the repo tree must stay unpolluted; the
   pre-commit cleanliness gate depends on it.
4. **Characterization tests flip deliberately.** Tests marked with §11.x pin
   today's stub/unwired behavior; when the gap closes, update the test in the
   same change — never silently.
5. **Contract boundary is the strict layer.** Pydantic models may default
   fields (e.g. `rationale=""`); the JSON schemas enforce required fields.
   Fixtures validate against contracts in-suite, exactly as CI runs the
   validator script.
6. **No product code changes to make tests pass.** A failing test is first
   interrogated: test bug → fix test; real defect → report (§11 style), don't
   patch product code from the test session.

## Known gaps (not covered yet)

- **Frontend**: `frontend/` has no test script or runner — dashboard is
  uncovered (out of scope for this session).
- **§11 open gaps**: unwired job queue, stub routers (`runs`/`metrics` return
  hard-coded values), `watsonx_client` past the key check, the `_dist`
  three-level-climb defect in `main.py` — characterized or explicitly
  untested, never asserted as correct.
- **Async jobs/worker**: `jobs.worker()` is an infinite loop with no test
  harness yet — add one when the queue is wired.
- **Python 3.10 floor**: dependency floor (fastapi/uvicorn/jsonschema/pytest
  all require ≥3.10) is not in the CI matrix; add if floor support matters.

## CI

`.github/workflows/tests.yml` — on push / PR / manual dispatch:
matrix `python-version: ["3.11", "3.12"]`, `fail-fast: false`, pip cache
keyed on `backend/requirements.txt`; steps: install requirements → `pytest`
→ `python scripts/validate_contracts.py`.

Both legs were executed locally before the workflow landed: **79 passed**
on 3.11.9 and on 3.12.14, validator OK ×2 on both.

## Session log (append-only)

### 2026-09-27 — Session 13: test suite scaffold + CI
- `/start` instruction: "setup the test suite". Scope confirmed with user:
  scaffold + unit tests extracted from the architecture documentation/Figure 6,
  GitHub Actions running the suite, this module record; commit only (no push).
- Created `pyproject.toml` (pytest-only: testpaths, asyncio auto + function
  loop scope, `slow`/`live_llm` markers), extended `.gitignore`
  (`__pycache__/`, `*.pyc`, `.pytest_cache/`).
- Wrote 9 test files / 76 new tests on top of the existing 3 smokes
  (79 total): gates, pipeline (+unwired-queue characterization), attestor
  policy, false-certified metric (incl. exposure-contract conformance), LLM
  layer (zero-network proof), schemas+contracts (incl. validator subprocess),
  API surface, store/db, config (reload + env snapshot/restore).
- Verification: `pytest` green on **3.11.9 and 3.12.14** (fresh pyenv venv,
  exact `requirements.txt` pins); `validate_contracts.py` OK ×2 on both —
  the full CI matrix proven locally before push.
- One test fixed during the session (its own bug): the no-network test
  initially forbade `httpx.AsyncClient` *construction*; the client is
  constructed I/O-free before `NotImplementedError` — rewritten to assert
  `send()` is never called instead. No product code was changed.
- Note: `jsonschema.RefResolver` deprecation warnings are shared with the
  product's own `scripts/validate_contracts.py` (same API) — left visible as
  debt, not suppressed.

### 2026-09-27 — Session 18: M1 contracts guard — 10 new tests (79 → 89)

- Added 10 tests to `backend/tests/test_schemas_contracts.py` (append only; no existing
  test deleted or weakened):
  - `test_every_contract_schema_has_a_pair` — loads `PAIRS` from `validate_contracts.py`
    via `importlib.util.spec_from_file_location` and asserts coverage equals every
    `.schema.json` on disk (Convention 7: asserts against the real producer).
  - `test_criterion_example_validates` — via `_validate_pair`.
  - `test_exposure_example_validates` — via `_validate_pair`.
  - `test_findings_example_validates` — via `_validate_pair`.
  - `test_exposure_example_is_the_unmeasured_state` — pins Convention 8 at the contract
    layer: `measured=False`, `null` rate, empty `by_operator`.
  - `test_findings_probe_enum_is_the_five_named_probes` — `FIVE_PROBES` module-level
    literal asserted against the schema's probe enum; parallels `SEVEN_CLASSES` in
    `test_metric.py`.
  - `test_uncovered_schemas_reports_a_missing_pair(tmp_path)` — unit test for
    `uncovered_schemas()` with a synthetic dir under `tmp_path`.
  - `test_uncovered_schemas_is_empty_when_all_covered(tmp_path)` — same setup, all paired.
  - `test_findings_result_is_unenumerated_and_tier_is_not_required` — pins two
    non-decisions: `result` stays unenumerated (M7's vocabulary), `evidence_tier` stays
    absent from required/properties (D1's call).
  - `test_verdict_example_validates` — via `_validate_pair` (added when the coverage check
    revealed `verdict.schema.json` was an existing orphan — see §5 below).
- **Declared changes to existing lines (Convention 10):**
  - `_validate_pair` helper: `(FIXTURES / fixture_name)` → `(ROOT / fixture_name)`;
    `FIXTURES` constant removed. Both existing call sites (`test_demo_run_fixture_validates_against_run_contract`,
    `test_demo_traceability_fixture_validates`) retained their string args, updated to
    `"fixtures/demo_run.json"` and `"fixtures/demo_traceability.json"`.
  - `test_pydantic_run_record_accepts_demo_fixture` and
    `test_fixture_verdicts_satisfy_verdict_contract`: direct `FIXTURES` references updated
    to `ROOT / "fixtures" / ...`.
  - `test_validator_script_exits_zero_as_ci_runs_it`: two stdout assertions updated to
    `"OK fixtures/demo_run.json"` and `"OK fixtures/demo_traceability.json"`, plus a third
    assertion added in the review pass below (the reported coverage count).
- **Discrepancy from stated expectations:** instructions specified 5 PAIRS entries, but
  `verdict.schema.json` is an existing schema on disk with no PAIRS entry (previously
  validated only via `run`'s `$ref`, not directly). The coverage check correctly identified
  it as an orphan. A 6th entry was added (`verdict.schema.json` ↔ `contracts/examples/verdict.json`),
  making PAIRS 6 entries and the count "OK 6/6 schemas covered". This is the intended
  behaviour of the coverage check: it caught a pre-existing gap.
- **Review pass, same session — one code defect, one guard, test count unchanged.** The
  validator's coverage line printed `len(PAIRS)/len(PAIRS)`, so a duplicate pair entry would
  have let the gate report coverage it did not have: a self-reported number not derived from
  what it claims to measure, in the one component whose entire job is that honesty. It now
  counts the schemas on disk. `test_validator_script_exits_zero_as_ci_runs_it` pins the
  reported number against the on-disk schema count, reusing the same subprocess rather than
  paying for a second one, so the regression cannot return. This adds an **assertion, not a
  test** — the count stays **89**, so the status header above is unaffected.
- **Verification:** `89 passed` on Python 3.14.7, isolated `/tmp/opencode/venv`,
  `PYTHONDONTWRITEBYTECODE=1 -p no:cacheprovider`. Validator: 6 OK lines + "OK 6/6
  schemas covered", exit 0. `git status --porcelain` shows only §2 files.
  3.14 is not the CI matrix — one CI run owed.
