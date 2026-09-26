# docs/test-suite.md — Intent Attestation Gate (test suite)

Append-only module record for the project's test suite. Architecture context
lives in `docs/architecture.md` (code-faithful) and `docs/intent-attestation-gate.md`
(concept); this file records only how the suite is organized, run, and extended.

Status: **scaffold + architecture-derived unit tests + receipt-renderer guard** — 116
tests (79 pre-existing + 37 receipt). Last verified 2026-09-27: **116 passed** on
Python **3.14.7**. The 79-test baseline remains green on 3.11.9 and 3.12.14, but
the 37 receipt cases have **not** yet run on the CI matrix — see the session log.

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
  test_schemas_contracts.py        §10 pydantic↔contract parity, fixture validation, validator wrap
  test_api.py                      §5 route table + health/webhook/stub endpoint shapes
  test_store_db.py                 §6 WAL mode, runs table, sha256-of-sorted-body artifacts
  test_config.py                   §3 env defaults/overrides, MOCK_LLM parsing, reload-restore
  test_receipt.py                  receipt renderer: determinism, digest round-trip against
                                   write_artifact, six honesty rules, tamper detection,
                                   no-network, no-llm-import, self-containment, escaping
```

## How to run

```bash
# from the repo root (CI runs exactly this):
pytest                                  # uses pyproject testpaths → backend/tests
python scripts/validate_contracts.py    # contracts ↔ fixtures gate (exit non-zero on fail)
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
| §10 | contracts, fixtures, validator | `test_schemas_contracts.py` |
| §11 | honest gaps — characterized, not hidden | `test_pipeline.py` (queue), `test_llm.py` (spike pending) |
| §3 (receipt renderer) | receipt renderer — determinism, digest integrity, honesty rules | `test_receipt.py` |

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
7. **Assert against the real producer, not a re-implementation.** Where a
   contract exists between two modules, the guard must pin the *actual*
   function's output. `test_receipt.py` round-trips through `write_artifact`
   rather than recomputing the digest itself, so a change to the hashing
   computation cannot pass by both sides drifting the same way.
8. **Content assertions skip the stylesheet.** A whole-document grep for a
   rendered string will collide with the renderer's own CSS (`width: 100%`
   contains `0%`). `test_receipt.py` exposes a `_content()` helper that strips
   the `<style>` block; use the equivalent wherever a renderer emits styles.
9. **Gap wording is a named constant.** Absent/unsigned/unmeasured states are
   asserted against exported constants (`GAP`, `UNSIGNED`, `UNMEASURED`), never
   against incidental markup — so rewording a document does not fail the suite
   while *removing* a claim does.

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

### 2026-09-27 — Session 15: receipt guard added (37 cases, 79 → 116)
- Added `backend/tests/test_receipt.py` — 33 functions: 31 original (one of them
  parametrized 5 ways, so 35 cases) plus 2 regression tests added mid-session =
  **37 collected, 37 passed**. No pre-existing test was modified; the 79 remain green.
- **Coverage:** determinism and key-order independence; the digest round-trip
  asserted against `write_artifact` itself (Convention 7); unsigned / mismatched
  / tampered digest states; the six honesty rules (`measured: false` never a
  number, absent artefacts named, `PENDING` styled as undecided, ladder marked
  provisional, chain state stated, attestor policy visible); self-containment
  (no `http(s)://`, no `<script>`); no-network via the `test_llm.py` send spy;
  no-llm-import via an `ast` walk; escaping of untrusted text; `tmp_path`
  discipline; malformed and hostile artefact shapes.
- **Two failures, both caught by running the suite — neither by reasoning:**
  - *Test bug.* `assert "0%" not in out` grepped the whole document and matched
    the renderer's own `width: 100%`. Fixed via a `_content()` helper stripping
    the `<style>` block; recorded as Convention 8.
  - *Real product defect.* `write_receipt` was handed the pre-digest payload, so
    the receipt rendered **"unsigned" for an artefact that was signed on disk**.
    Fixed by reading the stored `{run_id}.json`. `test_write_receipt_does_not_launder_a_tampered_artefact`
    now pins the security consequence: a tampered artefact must *not* re-verify.
- **Verification environment — read this before trusting the 3.14 number.** The
  dev machine had **no pytest, no pip, and no virtualenv**; only a system
  Python 3.14.7. The 7 pins were installed into an isolated `/tmp/opencode/venv`
  and run with `PYTHONDONTWRITEBYTECODE=1 -p no:cacheprovider`. Result:
  `37 passed`, full suite `116 passed`, validator OK.
  - **3.14.7 is not the CI matrix (3.11 + 3.12).** f-strings were audited for
    PEP 701 same-quote nesting (3.12-only syntax) and none were found, and the
    pre-existing 79 pass on 3.14 too — but **one CI run is still owed** before
    the receipt guard is trusted on the matrix.
  - Repo integrity was proven by hashing all 85 files before and after:
    **byte-identical**, no `__pycache__`, no `.pytest_cache`, no in-repo venv.
- New Conventions 7–9 recorded above.
- **Deliberately untested:** the HTTP route. `GET /api/runs/{id}/receipt` does
  not exist (M15 owns `runs.py`), so there is nothing to cover.
