# docs/test-suite.md — Intent Attestation Gate (test suite)

Append-only module record for the project's test suite. Architecture context
lives in `docs/architecture.md` (code-faithful) and `docs/intent-attestation-gate.md`
(concept); this file records only how the suite is organized, run, and extended.

Status: **scaffold + architecture-derived unit tests + M1 contracts guard + M3 parity guard
for all six contracts** — **118 tests** (79 pre-existing + 10 M1 + 21 M3 + 6 for the
`Finding` mirror + 2 M1-mandated parametrizations). Last verified 2026-09-27 on **four**
interpreters, not one: **3.10.21 · 3.11.9 · 3.12.14 · 3.14.7** — 118 passed on every
leg, validator exit 0 on every leg, each from a **clean venv built from
`backend/requirements.txt`** (the 3.11 leg is a fresh venv, not the polluted global
pyenv env). Since the Session 21 follow-up the file pins all 23 transitive deps, so
every leg installs the same stack — 3.11/3.12/3.14 byte-identical, 3.10 differing by
exactly the four marked lines. 3.11 + 3.12 remain the CI matrix; 3.10 is the
documented dependency floor and 3.14 is a deliberate forward-compatibility leg, and
**both are green today but enforced by nothing** — widening `tests.yml` is a **decision
owed**, not a fix (see Known gaps). 3.13 has no interpreter on this machine
and is untested.

**M14 (2026-09-27, this session):** the suite is **210 tests** — the 118 baseline
moved (`main` gained M2-fixture PR #43 and fix PR #46). **209 pass + 1
pre-existing failure** on 3.11.9 and 3.12.14 (clean venvs from
`backend/requirements.txt`; validator exit 0 both legs). The failure is
`test_models_parity.py::test_demo_traceability_fixture_loads_into_model`
(M2 fixture drift — E4/E2 in the fixture vs the test's E0 expectation;
recorded as `architecture.md` §11.15, owners M2+M3, not fixed here). M14's own
40 tests (33 `test_store_db.py` + 7 `test_store_records.py`) are green on both
legs, and all 5 new guards are mutation-proven lethal.
*MERGE (M4-ingest, Session 25): branch's 174-test Status dropped as superseded — it describes the pre-M14 world (4 pre-existing failures, no PR #43/#46, no M14). HEAD's Status above stands until the post-merge suite run recomputes it (see Session 25 entry).*

**M4-ingest merge (2026-09-27, Session 25):** the suite is **339 tests — 339 passed,
0 failed** on **3.11.9 and 3.12.14** (pins re-installed into the Session-23 venvs
per Convention 4; validator exit 0 both legs). Largest files: `test_ingest.py`
(102, new), `test_policy.py` (63), `test_models_parity.py` (46).
**§11.15 is CLOSED by this merge** — the branch's flipped agreement test
(`test_demo_traceability_fixture_loads_into_model`) passes; the E0 expectation
is gone, replaced by a run↔traceability coherence check that cannot go stale
the same way twice.

**R4 thin slice (2026-09-27, Session 25):** the suite is **399 tests — 399 passed,
0 failed** on **3.11.9 and 3.12.14** (same venvs, pins re-installed; validator
exit 0 both legs). R4's own contribution is **+36**: `test_extract.py` (11),
`test_parse.py` (4), `test_adjudicate.py` (13), `test_emit.py` (6), `test_gates.py`
+2 net (4 stub flips in the same changes per rule 7, §1.8.3 custody + end-to-end
chain tests). The remainder of the 339→399 delta is parallel lanes' (M18
`test_attest_cli.py`, R1/R2 pipeline/API extensions) — landed by their sessions,
green in the same runs. Guards mutation-proven: 9/9 behavioural kills (Session 21
rules: control green, killing test named) + both no-LLM-import AST guards proven
lethal; harness at `/tmp/opencode/r4_mutation_harness.py` (outside the repo).

**M10 (2026-09-27, R1, `a7178d2`):** `test_pipeline.py` 6 → 16 tests — both §11.1
characterizations flipped in the same commit (rule 7), 10 new guards (persist,
transitions, blocking failure, row-missing, redirect, submit shape, launch caps,
poison-refusal, sentinel processing, preset stop, lifespan start/stop). New
`backend/tests/conftest.py` autouse fixture redirects db + artifacts to `tmp_path`
(Convention 2 — consumer module, never env) and drains `jobs._queue` before/after
every test (M17 owns adoption). All 8 new guards mutation-proven lethal
(`/tmp/opencode/m10-guard-proof.py`, 0 survivors, restore byte-identical).
Targeted files green on 3.12.14 at landing; **integration proof executed** on
`refactor` @ `1b5be27`: **349 passed, 0 failed on 3.11.9 AND 3.12.14**, validator
`OK 6/6` exit 0 both legs, tree clean, no pollution. 349 = Session 25's 339 (post-M4,
pre-lane) **+ this lane's 10**. Session 25's architecture entry records `399` for the
same verification window — that count includes the main checkout's in-flight R4 files;
`349` is the committed tree at the verified SHA. §11.15 is closed (`0cac970`,
M3's Finding-mirror line) and green inside the 349. **The current committed count is
the 399 above** — R4/R2 landed as `c073dbe` + `2048e7c` after this paragraph was
written, and this rebase re-verified it: 399 passed both legs, validator 6/6.

## Layout

```
pyproject.toml                     pytest config only (not an installable package)
.github/workflows/tests.yml        CI: matrix py3.11/py3.12 → pytest + contract validator
backend/requirements.txt           runtime + test deps (pytest 9.0.3, pytest-asyncio 1.4.0)
backend/tests/
  __init__.py                      makes pytest put backend/ on sys.path (imports are `app.*`)
  conftest.py                      autouse: tmp_path redirect for db+artifacts, jobs._queue drain (M17 adopts)
  test_scaffold.py                 Session-11 smoke tests (pipeline, policy, metric-empty)
  test_gates.py                    §3 stage stubs: shapes, stage order, exit_code=1 blocks
  test_pipeline.py                 §1/§4 chain + persist/submit/worker/lifespan (R1), run-id format, both §11.1 tests flipped
  test_ingest.py                    M4 real Stage-1 ingest guard (102 tests — Session 25's Layout entry was missed here; added with the M10 lane's Status recompute)
  test_policy.py                   §8 attestor GRANTS/DENIES exact sets, fail-closed both ways
                                   — Session 20: 9 → 63 tests. Adds the declaration resolver,
                                   the worker-startup gate, the workspace read-only proof
                                   (EROFS/EACCES, undetermined, no-residue), and the auditor record
  test_metric.py                   §9 seven operators, rate math, exposure-schema conformance
  test_llm.py                      §7 mock determinism; watsonx fails loud; zero-network proof
  test_schemas_contracts.py        §10 pydantic↔contract parity, fixture validation, validator wrap
  test_models_parity.py            M3 model↔contract bijection, field coverage, strictness + honesty pins
  test_api.py                      §5 route table + health/webhook/stub endpoint shapes
  test_store_db.py                 §6 WAL mode, runs table, env wiring, commit discipline, sha256 envelope + D8 seam
  test_store_records.py            §6 typed reads, envelope→RunRecord projection, strict-model loads
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
| §1/§4 | runtime shape, data flow, pipeline chain + persist/submit/worker/lifespan (R1) | `test_pipeline.py` (+ `conftest.py` isolation) |
| §3 | six gates, schemas, config, LLM clients, metric, policy | `test_gates.py`, `test_schemas_contracts.py`, `test_models_parity.py`, `test_config.py`, `test_llm.py`, `test_metric.py`, `test_policy.py` |
| §5 | API surface (health, webhook, runs, metrics) | `test_api.py` |
| §6 | persistence (SQLite WAL, hash-sha256 artifacts) | `test_store_db.py`, `test_store_records.py` |
| §7 | LLM dual-mode + spend discipline | `test_llm.py` |
| §8 | read-only attestor (the differentiator) | `test_policy.py` |
| §9 | false-certified-rate metric (the "THE NUMBER") | `test_metric.py` |
| §10 | contracts (6 schemas), fixtures (2), validator (6 pairs + coverage check) | `test_schemas_contracts.py` |
| §11 | honest gaps — characterized, not hidden | `test_pipeline.py` (queue wired R1: §11.1 closed, §11.2/§11.5 callers landed), `test_llm.py` (spike pending) |

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
5. **Two tiers, not one strictness.** The JSON schemas are the **permissive
   interchange layer** (none sets `additionalProperties: false`); the pydantic
   models are the **strict in-process layer** (`extra="forbid"`, added Session
   18). Pydantic may still default fields (e.g. `rationale=""`); the schemas
   enforce `required`. So "which layer is strict" is only answerable per
   direction: strict on unknown keys in the model, strict on missing required
   keys in the contract. `test_models_parity.py` pins the model half so it
   cannot drift back to `ignore`. Fixtures validate against contracts in-suite,
   exactly as CI runs the validator script.
6. **No product code changes to make tests pass.** A failing test is first
   interrogated: test bug → fix test; real defect → report (§11 style), don't
   patch product code from the test session.
7. **Prove a guard fails before trusting it** (Session 16's generator rule,
   extended to tests — Session 18). A guard never seen failing is not a guard.
   `/tmp/opencode/m3_guard_proof.py` mutates `schemas.py` five ways, asserts
   the matching test fails, restores, and re-asserts green. **The fifth
   mutation initially did not fire** and exposed an overstated docstring.
8. **A test that pins a value is not a test that pins a type.** Round-trip
   equality survives a de-typing (`dict[str, dict[str,int]]` → `dict`), so a
   claim about a *type* needs its own negative assertion.
9. **Verify on every interpreter you have, not just the pin.** A single-version
   run is a statement about one interpreter, and it hides version-specific facts
   a multi-version run surfaces for free — 3.14 reported a
   `DeprecationWarning` for `asyncio.iscoroutinefunction` in `test_pipeline.py`
   (removal slated for **3.16**) that 3.10/3.11/3.12 could not report, and the
   warning-count skew between 3.11 and the rest turned out to be a real
   dependency-pinning defect (§ Known gaps). The `backend/.python-version` pin is
   a *pyenv* convenience; it is not the support matrix, and treating it as one is
   how a suite ends up "green" on a version nothing ships. Keep the matrix honest
   by adding a version *when one is available on the machine*, not when someone
   remembers.
10. **An interpreter swap is not a test run until the pins are re-installed.** A
    venv built from `requirements.txt` is the only way a leg is comparable;
    a bare system interpreter silently tests whatever happens to be installed.
    This is not hypothetical: the 3.11.9 leg initially resolved `starlette 1.0.0`
    while the 3.12.14 venv resolved `1.7.0`, because `starlette` is transitive
    and unpinned.

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
- **No fixture pair for `criterion` or `exposure`** (M1 AC 1, open). The mirrors
  for those two contracts are therefore tested with *constructed* values, not
  corpus data. This is M1's gap, not M3's — but it means the corpus and the
  mirrors are not yet cross-checked for those two shapes. Add the fixtures and
  this becomes a real end-to-end check. The `Finding` mirror is **not** in this
  state: it is checked against `contracts/examples/findings.json`, so it has a
  corpus cross-check even without a fixture pair.
- **The mirrors have no product callers** (`architecture.md` §11.10), so
  `test_models_parity.py` proves the *shapes* are faithful and nothing more. It
  cannot catch a gate that constructs a model wrongly — no gate does yet.
- **CI is still unverified on GitHub.** Every number in this file is local
  evidence from 3.10.21 / 3.11.9 / 3.12.14 / 3.14.7. The workflow has never run
  remotely, because the branch has not been pushed.
- **`requirements.txt` pins no transitive dependency, so CI is not reproducible**
  (found 2026-09-27, Session 21, by comparing legs rather than trusting one).
  The seven pins are all direct; **`starlette` arrives via fastapi and floats**.
  Measured: the 3.11.9 machine environment had `starlette 1.0.0`, a fresh
  `requirements.txt` install on 3.12.14 / 3.10 / 3.14 had **1.7.0**. The only
  visible symptom was the `StarletteDeprecationWarning` appearing on three legs
  and not the fourth — i.e. the warning-count *is* the canary. Every future CI
  run resolves transitive versions afresh, so a green run is not evidence about
  the same dependency set as last week's green run. Fix is a decision, not a
  patch: add explicit transitive pins (or a lockfile) to `requirements.txt`.
  **Worth doing before the branch is pushed**, because it is the difference
  between a CI matrix that tests something repeatable and one that does not.
  **CLOSED the same day (Session 21 follow-up, on explicit user instruction):**
  `requirements.txt` now carries all 23 transitive pins under the unchanged 7
  direct ones, with four `python_version` markers where pip genuinely diverges
  (sub-3.11 backports + the `rpds-py` floor move). Proven by deleting every venv
  and rebuilding clean on **3.10.21 / 3.11.9 / 3.12.14 / 3.14.7** from the file —
  118 passed + validator exit 0 on each, 3.11/3.12/3.14 byte-identical,
  3.10 differing by exactly the four marked lines. The 3.11 leg is now a **clean
  venv**, not the polluted global pyenv env (which carries dozens of unrelated
  packages and can never be a reference leg again). **Ownership note:**
  `requirements.txt` is M17's file (`modules.md` §0.4); edited here on the user's
  direct instruction, M17 to review and adopt. The leftover warning skew (13 on
  3.14 vs 14 elsewhere) is **explained, not open**: it is PEP 649 — 3.14 defers
  the `-> jsonschema.RefResolver` annotation at `test_schemas_contracts.py:35`,
  so the deprecated attribute is never touched at `def` time there. Proven with
  `/tmp/opencode/pep649_probe.py` (1 warning on 3.12, 0 on 3.14 for the identical
  `def`); the annotation is never introspected and the runtime access at line 40
  still warns everywhere. No action owed.
- **The CI matrix (3.11 + 3.12) does not cover the versions this session verified.**
  3.10 is the documented dependency floor (`docs/test-suite.md` Known gaps, carried
  since Session 13) and 3.14 is where the `asyncio.iscoroutinefunction` removal
  warning appeared. Both are green today, so the omission has cost nothing yet —
  which is exactly why it is cheap to fix now and expensive later. 3.13 has no
  interpreter on this machine and remains unverified. **Decision owed:** widen
  `tests.yml`, or record 3.10/3.14 as "verified locally, not enforced".
- **The enum regression guard is one layer short** (found 2026-09-27, Session 19;
  **partly closed Session 21**). `test_schemas_contracts.py` pins the **aliases**
  `Verdict` and `EvidenceTier` via `typing.get_args`, and `test_models_parity.py`
  pinned field **names** only — so nothing asserted the models actually *use*
  those aliases. De-typing `CriterionVerdict.evidence_tier`,
  `CriterionVerdict.verdict` or `TraceabilityLink.evidence_tier` from its
  `Literal` to `str` passed the whole suite. **Session 21 closed the same hole for
  the fourth enum field, `Finding.probe`**, by adding
  `test_finding_rejects_an_unknown_probe`, which pins the annotation *and* asserts
  the runtime rejection. **The three original fields are still unguarded** — the
  same one-line pattern applies to each, and the product code is correct today
  (nonsense tiers/verdicts/probes are rejected with `ValidationError`). Owner: M3
  (the mirrors) or M17 (the suite); unassigned. Left open rather than fixed here
  because it predates this session and `modules.md` rule 10 routes pre-existing
  findings to their owner.
- **A false claim in a test comment — FIXED at Session 21.**
  `_contracts_by_file`'s docstring in `test_models_parity.py` said the file name
  and the `title` "disagree for one contract" (`traceability.schema.json`). They
  disagree for **three**: also `run.schema.json` (`run` vs `RunRecord`) and
  `verdict.schema.json` (`verdict` vs `CriterionVerdict`); only `criterion`,
  `exposure` and `findings` follow the stem convention (case aside). The code was
  always correct — it keys by file name properly — but the stated *rationale* for
  keeping two lookup helpers was wrong, and acting on it ("only traceability is
  odd, so let me rename the other two") would have changed contract file identity
  in M1's directory. Recounted from source at Session 21 rather than trusting
  Session 19's note; the note was right, the comment was not.

## CI

`.github/workflows/tests.yml` — on push / PR / manual dispatch:
matrix `python-version: ["3.11", "3.12"]`, `fail-fast: false`, pip cache
keyed on `backend/requirements.txt`; steps: install requirements → `pytest`
→ `python scripts/validate_contracts.py`.

Both legs were executed locally before the workflow landed: **79 passed**
on 3.11.9 and on 3.12.14, validator OK ×2 on both. Re-run at Session 18 after
M3: **100 passed** on both legs, validator OK ×2 on both. **Still unverified
on GitHub** — the branch has not been pushed, so no remote CI run has ever
executed this workflow.

**Step-ordering fact (Session 23, read from the workflow source):** the
steps run install → `pytest` → validator, and GitHub Actions **skips
subsequent steps after a failure**. So while §11.15 stands, `pytest` exits 1
on **both** legs (`fail-fast: false` lets both run and both fail) and the
validator step **never executes** — the green `OK 6/6` we prove locally will
not appear in CI at all until the suite is red-no-more. Rehearsed locally
for the M14 merge: merged tree = **211 items → 210 passed + the same §11.15
failure** on both legs (the failure re-proven pre-existing on parent
`4b03c55`).

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

### 2026-09-27 — Session 18: M3 parity suite (+21 tests, 79 → 100)
- Driven by the `/start` instruction *"develop the pydantic mirrors (M3)"*. This
  file needed updating because a **new test file landed and the count moved**;
  it had not been touched before this entry and still claimed 79 tests.
- **Added `backend/tests/test_models_parity.py`** (21 tests), placed in
  `backend/tests/` deliberately as an **M3-exclusive file**: the M3 brief named
  `test_schemas_contracts.py` for the parity assertion, but `backend/tests/` is
  M17's path (§0.2) and that file is not in the §0.4 contended list, so editing
  it would have created the two-owner collision §0.4 exists to prevent. The new
  file **does not duplicate** the enum, fixture-load or round-trip tests already
  in `test_schemas_contracts.py`.
- What the 21 cover: the **title ↔ class bijection** over `contracts/*.schema.json`
  (fails when M1 adds a schema, until it is mirrored); per-contract field coverage
  and `required` coverage; a **strictness pin** (`extra="forbid"` on all six
  models, plus a raising check); the **`Exposure` honesty pin** (`null` rate with
  `measured: false`, never `0.0`, and the measured `0.0` stays distinct); a
  round trip per new model; `criterion`/`traceability` fixture and constructed-value
  loads; and a binding of `Exposure` to its real producer,
  `metrics.false_certified_rate`, for both the empty and measured cases.
- **Convention 5 was amended, not just appended to.** "Contract boundary is the
  strict layer" became **"Two tiers, not one strictness"**, because the models
  *are* the strict layer for unknown keys since Session 18. Left as-is it would
  have contradicted the code it describes. One sentence from the old convention
  (in-suite fixture validation mirrors the CI validator run) was preserved.
- **A guard failed to fire, and it caught a false claim.** The fifth mutation in
  `/tmp/opencode/m3_guard_proof.py` (de-typing `by_operator` to a bare `dict`)
  did **not** fail the suite: `test_exposure_accepts_metric_function_output`
  asserted only that values round-tripped, while both the test's placement and
  the model docstring claimed the *type* was checked. This is the origin of new
  Convention 8. Fixed, re-proven — **5/5 mutations now fire**, suite green after
  restore. Per Convention 6 the fix was to the *test*, not to the product model.
- **Verification:** **100 passed** on **3.11.9 and 3.12.14**; validator exit 0 on
  both legs; repo tree unpolluted (Convention 3 intact). Warnings are pre-existing:
  `jsonschema.RefResolver` (D10, deferred by decision) and
  `StarletteDeprecationWarning` on `httpx2` in fastapi's testclient — the latter
  would need a dependency change, so it is a **decision**, not a fix.
- **Open:** `criterion` and `exposure` still have no fixture pair (M1 AC 1), so
  those two mirrors are tested with constructed values rather than corpus data.
  The mirrors have zero product callers (§11.10), so this suite proves shape
  fidelity only. **CI has still never run on GitHub** — every number here is
  local evidence.
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

### 2026-09-27 — Session 19: verify the M3 parity suite (read-only, no code change)
- Instruction: *"verify all the new tests added"*. Scope = the 21 tests added at
  Session 18 in `backend/tests/test_models_parity.py`. **Verification only — no
  product code, contract, fixture, test or dependency was changed.** HEAD stayed
  `c78df43` and the tree was clean before and after.
- **Baseline re-confirmed:** 100 passed on **3.11.9 and 3.12.14**; validator exit
  0 on both legs; `79 + 21 = 100` confirmed by per-file collection counts;
  working tree unpolluted.
- **Parity claim recomputed independently.** Deliberately *not* by reusing the
  test's own `inspect`-based helpers (a shared bug would hide in both): parsed
  `schemas.py` with `ast` and globbed the contracts directly. 5 contract titles,
  6 mirrors, 1 strict base (`ContractModel`), `TraceabilityLink` the only model
  with no titled contract. The 5/5 claim holds.
- **All guards mutation-tested, 13 mutations**, each breaking one product or
  contract fact a guard claims to pin, run against a fresh throwaway copy per
  mutation so the real tree was never written to. **11 of 13 killed:** parity
  bijection (dropped model, stray model, renamed title), the self-invalidating
  `INLINE_MIRRORS` exception (M1 promoting the inline link to a real contract
  correctly *demands its own deletion*), `extra="forbid"`, Criterion's three
  mandatory fields, contract-gains-a-property coverage, `by_operator` specific
  typing, the honesty pin (2 mutations), inline link shape, and the
  `locations` default. No vacuous tests: an AST scan confirms every test
  contains an `assert` or `pytest.raises`, and there are no trivial asserts.
- **The 2 survivors were re-checked by hand, not reported** (Session 16's rule
  that an audit script returning a false alarm gets verified before it is
  believed). Both were harness artifacts, not weak guards:
  1. *dropping the `Criterion` model* looked like a survival only because the
     harness matched `file::test` IDs and missed a collection-time `ImportError`.
     The suite **does** refuse to run without the model.
  2. *`links: []` as a bare mutable default* is an **equivalent mutant** —
     pydantic 2.13.0 deep-copies mutable defaults (verified: appending to one
     instance's list does not leak into another's), so correctly not caught.
- **Finding — the enum guard is one layer short.** Both literal tests inspect the
  type *alias* (`typing.get_args(Verdict)` / `(EvidenceTier)`); the parity file
  checks field *names*. So the alias→field wiring is unpinned, and de-typing any
  of the three enum-annotated fields to `str` survives the full suite. The
  product is right today (nonsense tiers and verdicts are rejected); the safety
  net is one layer short. Recorded in *Known gaps* above and as
  `architecture.md` §11.12, because the mirrors are documented as the strict
  trust layer "these are the shapes a verdict rests on" — and a gate that
  accepted `evidence_tier="E9"` is the fail-open failure this project exists to
  prevent.
- **Finding — a false claim in a test comment.** `_contracts_by_file`'s docstring
  understates the file-name/`title` disagreement as one contract when it is
  three. The code is right, the rationale is wrong. Left unfixed and recorded,
  since fixing it is a code change and this session changed none.
- **This is the seventh documented instance of a doc in this repo being wrong
  about the code**, after §3's "7 failure classes" (six), §7's `MOCK_LLM` claim,
  Session 17's correction of that correction, Session 16's over-claiming figure
  legend, and two in Session 18. All three of this session's surviving
  doc-vs-code checks were resolved by reading source rather than the
  neighbouring doc.
- **Open, deliberately not actioned:** the enum guard needs a new negative
  assertion, and the comment needs correcting — but
  `test_models_parity.py` is an M3-exclusive path and `backend/tests/` is M17's,
  so which owner takes the fix is an assignment question, not this session's to
  make. Per `modules.md` rule 10 and the Session 16 precedent, `modules.md` was
  **not** edited for these findings.

### 2026-09-27 — Session 20: merge `origin/main` into `tests` (conflict resolution)
- Two doc conflicts, both in the Session-log tail, both resolved by **keeping
  both sides** — ours (Session 19, parity verification) and theirs (Session 18,
  M1 contracts). The `§11` enum gap renumbered 11 → 12 to clear M1's new gap 11;
  no stale `§11.11` reference survives in this file, `architecture.md` or
  `AGENTS.md`.
- **The working tree was corrupt even though git said the merge was resolved:**
  `git status` reported *"All conflicts fixed but you are still merging"* while
  both files still carried raw three-way conflict-marker fences on disk. A
  `git add .` would have committed them. Repaired with `git restore --worktree`
  from the **index** (not `HEAD`, which would have discarded the resolution).
  **Lesson worth keeping: git's "all conflicts fixed" is a statement about the
  index, not about what is on disk.**
- **Merged suite state: 112 tests — 109 pass, 3 fail.** M1's
  `contracts/findings.schema.json` has no `Finding` mirror in
  `app/models/schemas.py`, so the parity bijection fails. Expected, named, and
  correct: the parity test's docstring instructs mirroring the schema rather
  than suppressing the test. Owner M3; `modules.md` §0.4 makes
  `backend/app/models/schemas.py` M3-exclusive.
- Validator green at **6/6 schemas** (M1 extended `PAIRS` 5 → 6 and added
  `contracts/examples/{criterion,exposure,findings,verdict}.json`), so the contract
  side merged cleanly and `test_schemas_contracts.py` grew 9 → 19.
  `test_models_parity.py` grew 21 → 23 because `Finding` joins the parametrized
  title set.
- Counts: "100 tests (79 + 21)" is preserved as the `tests`-branch record; **112**
  is the merged total. Historical entries not rewritten.

### 2026-09-27 — Session 21: green the merged tree, then verify it on four interpreters
- Instruction: *"analyze the code base, make sure that it pass the tests"*, extended to
  *"verify the tests suite as well because it uses different python version instead of
  sticking to 3.12.14"*. Two deliverables: make the merged tree green, and stop treating
  one interpreter as the suite.
- **The 3 red tests were one missing model.** M1's `contracts/findings.schema.json`
  (title `Finding`) had no mirror, so the bijection and both coverage tests failed with
  `KeyError: 'Finding'`. Per that test's own docstring the fix is to mirror the schema,
  **not** to suppress the test, so the fix was product code: added `Probe` (5-value
  `Literal`) and `Finding` to `backend/app/models/schemas.py` — M3-exclusive per
  `modules.md` §0.4, so this was M3's file to fix, not a merge side-effect. Also
  corrected the module docstring's "five draft-07 schemas" to **six**.
  `Finding` deliberately has **no** `evidence_tier` (D1 unratified, and the contract's
  own `description` forbids it), keeps `result` **unenumerated** (M7's vocabulary), and
  has **no defaults** on any of its five required keys.
- **A guard is not a guard until it has been seen failing** (Convention 7), so the new
  mirror was mutation-tested: `/tmp/opencode/finding_guard_proof.py`, each mutation
  applied to a **fresh throwaway copy** so the real tree was never written to.
  **The first harness was broken and reported 7/7 killed — all false.** It passed bare
  filenames to pytest, which exits **4** ("file or directory not found", "no tests ran"),
  and `rc != 0` was being scored as a kill. Caught only because 7/7 contradicted a
  prediction of 4 survivors. After fixing the paths and **adding a control run** (the
  unmutated copy must pass, or every kill is meaningless), the true result was
  **3/7 killed, 4 survived** — exactly the predicted gap. A collection-time
  `ImportError` is also scored separately, because the module imports `Finding` by name
  and that is a *stronger* kill than an assertion (Session 19's trap, inverted).
- **The 4 survivors were real, and are now closed** — 6 new tests in
  `test_models_parity.py`, 112 → **118**: `test_finding_roundtrip`,
  `test_finding_accepts_the_contracts_own_example` (cross-checked against
  `contracts/examples/findings.json`, so `Finding` is the one new-contract mirror with a
  corpus check), `test_finding_requires_all_five_fields`, `test_finding_rejects_an_unknown_probe`
  (Convention 8 — pins the annotation *and* the runtime rejection),
  `test_finding_does_not_encode_d1_tier_semantics`, `test_finding_result_stays_unenumerated`.
  Re-proven: **all 7 mutations now killed, 0 survivors**, plus 2 extra mutations proving
  the bijection's *"only in models"* branch is independently live (a stray model is
  caught by the assertion, not the import).
- **Multi-version verification — the part the instruction actually added.** Every
  interpreter on the machine was used, each with a venv built from the exact
  `requirements.txt` pins (Convention 10):

  | interpreter | pytest | validator | notes |
  |---|---|---|---|
  | 3.10.21 | 118 passed | exit 0 | documented dependency floor, **not in the matrix** |
  | 3.11.9 | 118 passed | exit 0 | matrix leg 1 (global pyenv env) |
  | 3.12.14 | 118 passed | exit 0 | matrix leg 2, matches `backend/.python-version` |
  | 3.14.7 | 118 passed | exit 0 | forward-compat leg, **not in the matrix** |

  **3.13 has no interpreter on this machine and is untested** — recorded, not glossed.
- **Two findings came out of comparing legs, neither of which one version would show:**
  1. **A real forward-compat defect, fixed.** 3.14 alone reported
     `DeprecationWarning: 'asyncio.iscoroutinefunction' is deprecated and slated for
     removal in Python 3.16` — and the source is **our own test code**,
     `test_pipeline.py:69`, not a dependency. Swapped to `inspect.iscoroutinefunction`
     (the documented replacement) after confirming the two cannot disagree here:
     `jobs.worker` is a plain `async def` with no `markcoroutinefunction` decorator,
     which is the only case where they differ. The §11.1 characterization is unchanged —
     only the deprecated call is gone. 3.14 warnings 14 → 13, now matching 3.11.9.
  2. **CI is not reproducible: no transitive dependency is pinned.** The warning *count*
     differed (3.11.9 = 13, the other three = 14) and the only cause was
     `StarletteDeprecationWarning`. Chasing it found the real defect: **`starlette` is
     not in `requirements.txt`** — it arrives via fastapi and floats. The 3.11.9 machine
     environment had **1.0.0**; fresh pinned installs on 3.12.14 / 3.10 / 3.14 had
     **1.7.0**. So the "79 green on 3.11.9 and 3.12.14" every session record cites was
     **two different dependency sets**, and the symptom was visible only as a warning
     count. Each CI run re-resolves transitives, so consecutive green runs are not
     evidence about the same stack. Fix is a **decision** (pin transitives or add a
     lockfile), not a patch — recorded in Known gaps, not actioned.
- **Pre-existing doc-vs-code correction.** `_contracts_by_file`'s docstring claimed the
  file-name/`title` disagreement was **one** contract; it is **three** (`run`,
  `traceability`, `verdict`; `criterion`, `exposure`, `findings` follow the stem
  convention case-insensitively). Recounted from source rather than trusting Session
  19's note — the note was right, the comment was not. Fixed, since this session is
  already inside this M3-exclusive file. **This is the eighth documented instance of a doc
  in this repo being wrong about the code.**
- **Verification:** 118 passed + validator exit 0 on **all four** interpreters; repo tree
  unpolluted (Convention 3) — `git status` shows only the 3 intended files, and every
  `__pycache__`/`.pytest_cache` is gitignored. Remaining warnings are pre-existing and
  unrelated: `jsonschema.RefResolver` (D10, deferred by decision),
  `StarletteDeprecationWarning` (needs a dependency change = a decision), and
  `httpx2`-related advice in starlette's own message text (`httpx2` is **not** installed
  on any leg — the earlier `AGENTS.md` phrasing could be read as if it were).
- **Convention 6 honoured:** the 3 red tests were fixed by adding the model the test
  demanded. No test was weakened, skipped, or deleted to reach green, and the suite went
  **up** (112 → 118) rather than down.
- **Open, deliberately not actioned:** `§11.12`'s three original enum fields are still
  unguarded (the pattern to close them is now in the file, one line each);
  `requirements.txt` transitive pins; the CI matrix width decision; 3.13 unverified; and
  the mirrors still have **zero product callers** (§11.10) — so none of this moves the
  critical path. Wave 0 (**M1, M11, M12**) still gates Wave 1, and M1 was already built
  at Session 18.
- **Follow-up the same day (user instruction: do §11.14 now, defer §11.12):** the
  transitive-pins decision is **taken and implemented** — `backend/requirements.txt`
  now pins all 23 transitives (4 with `python_version` markers), proven by rebuilding
  all four venvs from the file. The Known-gaps bullet above is closed; the §11.12
  guards stay open pending the ownership question, exactly as instructed.

### 2026-09-27 — Session 22: M14 persistence guards (32 + 7 tests)
- `test_store_db.py` 9 → 32: env wiring (`_sqlite_path` table, default-from-URL, explicit-wins), `now_iso` str/UTC/ordering, `idx_runs_created_at`, commit-survives-reopen, `created_at` ISO-8601-str type pin (M14 AC 2 **and** M17's missing-coverage item — landed once, here), `set_status` rowcount-0 fail-closed signal, newest-first + limit, `prev_digest` default/threading, store-keys-win, and the D15 self-invalidating guard. **No existing test flipped.**
- New `test_store_records.py` (7, M14-exclusive like M3's parity file): envelope reads, missing→`None`, the M3-obligation-1 projection whitelist (incl. subset tolerance while the envelope is uncontracted), strict-model loads incl. a mixed CERTIFIED/REJECTED record, missing→`None`, malformed→`ValidationError` (the `sandbox.py` posture).
- **Verification (via subagent — bash denied this session):** 209 passed + 1 pre-existing failure on 3.11.9 and 3.12.14 from clean `requirements.txt` venvs; validator exit 0 both legs; guard proof `/tmp/opencode/m14_guard_proof.py` — 5/5 kills, 0 survivors (control green on the M14 files); `git status` shows only the 5 intended M14 files, no `attestation.db`/`artifacts/` pollution. The failure is the §11.15 M2 drift — M14 verified around it, per Convention 6 the fix belongs to M2+M3.
- **Follow-up the same day (verification round on user instruction — audit, then commit if changes needed):** reading the tests against their own claims found **3 weaknesses**, all fixed in `test_store_db.py`, no product code touched:
  (A) `test_write_artifact_hash_independent_of_key_order` was **vacuous** — it hashed two stdlib dumps directly and never called `write_artifact`, so it survived a `sort_keys` deletion that it purported to guard; rewritten to exercise the product.
  (B) the index test pinned the index **name** (`index_list`) but not its **target column** — `ON runs(id)` passed; `PRAGMA index_info` assertion added.
  (C) `test_list_runs_newest_first` could not distinguish `created_at DESC` from `id DESC` (its ids sort in insertion order, so both orderings satisfy the expectation) — added deterministic `test_list_runs_orders_by_created_at_not_id` with a **mocked clock** and reverse-sorted ids, so the three candidate orderings disagree without a microsecond race.
  Count **39 → 40** (33 + 7). Re-verified from scratch: **210 passed + the same 1 pre-existing failure on both 3.11.9 and 3.12.14**, validator exit 0 both legs, tree clean except the one test edit, no pollution; **the §11.15 failure re-proven pre-existing on parent `4b03c55`** via a throwaway worktree (fails there too); mutation proof rerun under Session 21's harness rules (control green, which-test-id reported) — **9/9 killed, 0 survivors, no collection errors**, including MUT6→(B), MUT7/MUT9→(C), MUT8→(A) — each new/strengthened guard seen failing before it was trusted (Convention 7).
*MERGE (M4-ingest, Session 25): the two entries below landed via this merge — branch-numbered Sessions 19/20 from Aixxn's lane (M2 guard, M12 guard). Subtitles disambiguate them from main's same-numbered sessions; kept verbatim per the Session 20 precedent.*

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

### 2026-09-27 — Session 25 (R4): M5/M6/M7-stub/M8/M9 guards (this session)
- **+36 tests, all on `refactor`:** `test_extract.py` (11: §1.7 split, empty/compound/
  vague/duplicate rejections, stable ids, threading, no-LLM-import AST guard),
  `test_parse.py` (4: unresolved anchors, threading, no-LLM-import AST guard),
  `test_adjudicate.py` (13: §1.7 pair, D3 table, fail-closed edges, contract
  conformance), `test_emit.py` (6: derivation table, echo, traceability both
  directions + link conformance, unmeasured exposure, bare-dict tolerance),
  `test_gates.py` +2 net (4 stub flips in the same changes per rule 7, §1.8.3
  custody test, end-to-end §1.7 chain test). Chain-order tests live here, not in
  `test_pipeline.py` — that file is M10's, and the pipeline-level test is Cody's.
- **Status recomputed above (399/399 both legs).** Mutation battery 11/11 lethal
  (Session 21 rules); the two AST import guards were proven separately by
  inserting `import app.llm` into throwaway copies — both fire.

### 2026-09-27 — M10 lane (R1): persist/submit/worker/lifespan guards (`a7178d2`)
- **Scope:** `test_pipeline.py` 6 → 16 tests + new `backend/tests/conftest.py`
  (autouse; the file the suite was missing — `enqueue_run` now persists and every
  webhook test writes rows, so without the redirect + drain the suite pollutes the
  repo tree and `test_jobs_submit` fails on ordering alone).
- **Flips (rule 7, same commit as the behavior):** `test_jobs_submit…` rewritten for
  the `(run_id, payload)` work-item shape; `test_worker_is_async_but_never_started_by_app`
  rewritten as `test_worker_is_started_by_app_lifespan` — dynamic proof via `with
  TestClient(app)` (task alive inside, done + not cancelled after exit), which is safe
  only because bare `TestClient(app)` (as in `test_api.py:10`) never runs lifespan.
- **New guards:** persist-queued-row, pure-path-writes-nothing, full
  `queued→running→pending` transition with artifact file, stage-raise blocking record
  (exact dict pinned), row-missing skips-stages-but-still-blocks (artifact durable,
  row stays absent), redirect-is-active (`tmp_path` in both bindings), launch-caps ==
  GRANTS with startup-path acceptance, poisoned-caps refusal before consuming
  (`qsize` untouched), sentinel processing to `pending`, preset-stop consumes nothing.
- **Proof:** targeted files green on 3.12.14 (`test_pipeline` 16/16; api/scaffold/
  config/store/policy 124/124); guard harness `/tmp/opencode/m10-guard-proof.py`
  under Session-21 rules (control green, per-test ids) — **8/8 killed, 0 survivors**,
  restore byte-identical, no `attestation.db`/`artifacts/` pollution (`git status`
  shows only the 6 lane files). **Full both-legs proof executed at integration
  (second pass):** on `refactor` @ `1b5be27` — **349 passed, 0 failed on 3.11.9 and
  3.12.14**, validator `OK 6/6` exit 0 both legs, tree clean, no pollution. §11.15 was
  fixed elsewhere (`0cac970`, M3's Finding-mirror line) and is included green in the
  349; the earlier `expect 221 → 220 + §11.15` estimate predates M4/M12/M2/S25's
  landed tests. Scope: Session 25's `399` includes the main checkout's in-flight R4
  files; `349` is the committed tree at the verified SHA. **Re-verified at `2048e7c`
  after R4/R2 committed those files: 399 passed, 0 failed both legs, validator 6/6,
  tree clean.**
