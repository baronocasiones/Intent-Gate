# docs/test-suite.md — Intent Attestation Gate (test suite)

Append-only module record for the project's test suite. Architecture context
lives in `docs/architecture.md` (code-faithful) and `docs/intent-attestation-gate.md`
(concept); this file records only how the suite is organized, run, and extended.

Status: **scaffold + architecture-derived unit tests + M1 contracts guard + M2 corpus guard
+ M12 attestor policy** — 151 tests (79 pre-existing + 10 M1 + 8 M2 + 54 M12). Last verified
2026-09-27 on Python **3.14.7** (isolated `/tmp/opencode/venv`, `PYTHONDONTWRITEBYTECODE=1 -p no:cacheprovider`).
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
                                   — Session 20: 9 → 63 tests. Adds the declaration resolver,
                                   the worker-startup gate, the workspace read-only proof
                                   (EROFS/EACCES, undetermined, no-residue), and the auditor record
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
- **No test exercises a real read-only mount** (Session 20). `sandbox.py`'s production refusal
  path is `EROFS` from a `--read-only` bind mount; every refusal test gets `EACCES` from a
  `chmod 555` directory, because a real `EROFS` needs root and this box has no such mount. The
  constant is pinned and the errno translation is covered by the one substituted call in the file
  — dropping `EROFS` fails 2 tests — but that is coverage by substitution, not observation.
  **M17's to close:** a CI leg that runs `test_policy.py` against an actual read-only mount.
- **The attestor enforcement path has no integration test** (Session 20). `enforce_worker_read_only`
  has zero callers outside its own unit tests, so nothing proves M7/M10 will wire it. Covered only
  when the worker lands.

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

### 2026-09-27 — Session 19: M2 corpus guard — 8 new tests, and a merge that needed a human

- **+8 tests in `test_schemas_contracts.py` (17 → 27), 89 → 151 total.** The guard file is
  now shared by M1, M2 and M3 and is the most contended file in the suite.
- **One guard flipped deliberately, in the same change** (Convention 4).
  `test_pydantic_run_record_accepts_demo_fixture` characterised the stub by asserting 2
  verdicts, all `PENDING`, all `E0`. That behaviour was deleted, so the test now pins the
  concrete worked-example values. The flip is recorded in the commit body, not only here.
- **Added:** corpus-is-not-a-stub (mixes `CERTIFIED`+`REJECTED`, non-empty `locations`, a tier
  above `E0`, no "stub" rationale); served-copy byte-equality; served copy against
  `run.schema.json`; run↔traceability coherence; and 4 on the exposure fixture (contract
  conformance, measured with a rate below 0.5, all 7 operator keys, one false-certified plus
  one unexercised operator).
- **M1/M2 merge needed a real resolution, not a pick-one-side.** M1 changed `_validate_pair`
  so its argument is a repo-relative path resolved against `ROOT`, and removed the `FIXTURES`
  constant. Git's auto-merge left M2's older `FIXTURES`-based `_validate_pair` directly
  beneath it, with no conflict marker. Taking both would have read
  `fixtures/fixtures/demo_run.json` and raised `NameError` on the deleted constant. Resolved
  to one `_validate_path(schema, Path)` plus one `_validate_pair(schema, repo-relative)`
  delegating to it. All 18 tests from both sides survive; the merged file is 27.
- **Two docstrings corrected because the merge made them false.** Both claimed a schema "has
  no validator pair (M1's criterion 1)"; M1's `PAIRS` now covers all 6 schemas. They are
  still validated in-suite, but for a different reason: `PAIRS` points `exposure` at
  `contracts/examples/exposure.json`, the unmeasured null stub, whereas
  `fixtures/demo_exposure.json` is a different artifact carrying a real measured rate.
- **Method note worth keeping:** a green suite did **not** prove the merge was clean, and a
  false "silent loss" was reported from a `grep` whose escaping was broken. A merge is
  verified by diffing the result against *both* parents — not by the tests passing, and not
  by one grep. Both parents must be diffed in both directions.

### 2026-09-27 — Session 20: M12 policy guard — 9 → 63 tests (89 → 151 total)

- `test_policy.py` grew from 9 to 63 tests, all on 3.11.9 and 3.12.14. Suite total 89 → 151.
  Validator 6/6, exit 0. No new dependency, no new test file — M12's declared guard stayed single.
- **Mutation-tested, which is the part that makes this guard mean something.** Eight mutations,
  **none survived**: probe never writes (10 fail), `os.access` shortcut (7), `EROFS` dropped from
  `REFUSAL_ERRNOS` (2), undetermined folded into refused (5), record mints `workspace_readonly`
  without a proof (1), `enforce_workspace_read_only` returns instead of raising (1), `workspace`
  made optional again (1), and — the forbidden direction — `edit` added to `GRANTS` (**22**,
  including `test_scaffold.py::test_attestor_policy_ok`, a file M12 does not own).
- **Layered deliberately, so no single test is load-bearing.** The exact-set pin is the obvious
  guard, but deleting it still leaves disjointness, the happy-path `assert_read_only(GRANTS)` call,
  the vocabulary checks, the record-shape test and `test_scaffold.py` catching a widening. A guard
  that only fires during a demo rehearsal gets disabled rather than debugged; this one would have
  to be edited in six places.
- **Two implementation traps worth remembering for any future filesystem-touching test:**
  `chmod 555` breaks `tmp_path` teardown (`shutil.rmtree` fails on a read-only dir — the mode must be
  restored in a `finally`), and running as root defeats permission bits entirely, so those tests
  `skipif` on `os.geteuid() == 0` with the reason stated rather than failing confusingly.
- **One mock exists in the file** and is named as such: `test_refusal_witness_is_the_errno_the_kernel_gave`
  substitutes the OS call, because a genuine `EROFS` needs root. Every *refusal* test still attempts
  a real write. The re-raise path is reached for real instead, via a self-referential symlink (ELOOP).
