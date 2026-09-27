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
  test_schemas_contracts.py        §10 pydantic↔contract parity, fixture validation, validator wrap
  test_models_parity.py            M3 model↔contract bijection, field coverage, strictness + honesty pins
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
| §3 | six gates, schemas, config, LLM clients, metric, policy | `test_gates.py`, `test_schemas_contracts.py`, `test_models_parity.py`, `test_config.py`, `test_llm.py`, `test_metric.py`, `test_policy.py` |
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
- **No fixture pair for `criterion` or `exposure`** (M1 AC 1, open). The mirrors
  for those two contracts are therefore tested with *constructed* values, not
  corpus data. This is M1's gap, not M3's — but it means the corpus and the
  mirrors are not yet cross-checked for those two shapes. Add the fixtures and
  this becomes a real end-to-end check.
- **The mirrors have no product callers** (`architecture.md` §11.10), so
  `test_models_parity.py` proves the *shapes* are faithful and nothing more. It
  cannot catch a gate that constructs a model wrongly — no gate does yet.
- **CI is still unverified on GitHub.** Every number in this file is local
  evidence from 3.11.9 / 3.12.14. The workflow has never run remotely, because
  the branch has not been pushed.
- **The enum regression guard is one layer short** (found 2026-09-27, Session 19).
  `test_schemas_contracts.py` pins the **aliases** `Verdict` and `EvidenceTier`
  via `typing.get_args`, and `test_models_parity.py` pins field **names** only —
  so nothing asserts the models actually *use* those aliases. De-typing
  `CriterionVerdict.evidence_tier`, `CriterionVerdict.verdict` or
  `TraceabilityLink.evidence_tier` from its `Literal` to `str` passes all 100
  tests. **The product code is correct today** — the models do reject
  `evidence_tier="E9"` and `verdict="MAYBE"` with `ValidationError`; only the
  guard is missing. Owner: M3 (the mirrors) or M17 (the suite); unassigned.
- **A false claim in a test comment, left in place** (found 2026-09-27, Session 19).
  `_contracts_by_file`'s docstring in `test_models_parity.py` says the file name
  and the `title` "disagree for one contract" (`traceability.schema.json`). They
  disagree for **three**: also `run.schema.json` (`run` vs `RunRecord`) and
  `verdict.schema.json` (`verdict` vs `CriterionVerdict`); only `criterion` and
  `exposure` follow the stem convention. The code is correct — it keys by file
  name properly — but the stated *rationale* for keeping two lookup helpers is
  wrong, and acting on it ("only traceability is odd, so let me rename the other
  two") would change contract file identity in M1's directory. Not fixed: this
  session changed no code.

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
### 2026-09-27 — Session 21: M13 harness guard

- Extended `test_metric.py` with operator-by-operator transformation checks, criterion
  contract/model validation, untouched input checks, seven-case ordering and counts,
  valid/invalid emitted verdicts, runner exceptions, and the distinction between a
  measured zero and an unmeasured null exposure. No live call is made.
- Python 3.12.14, pinned dependencies in a temporary runtime: `pytest -q` with an
  explicit temporary base produced **139 passed, 3 failed**. The three failures are in
  `test_models_parity.py`: `Finding` exists in `contracts/findings.schema.json` but not
  in the M3-owned model file. The failures predate this M13 change; they were not patched
  from the test session. `python scripts/validate_contracts.py` passed, 6/6 pairs.
- The first pytest attempt used this Windows sandbox's default temp folder and nine
  `tmp_path` setups were denied; rerunning with an explicit temporary base resolved
  those environment errors. No repo-root DB or artifact directory was created.