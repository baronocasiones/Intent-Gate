# docs/test-suite.md — Intent Attestation Gate (test suite)

Append-only module record for the project's test suite. Architecture context
lives in `docs/architecture.md` (code-faithful) and `docs/intent-attestation-gate.md`
(concept); this file records only how the suite is organized, run, and extended.

Status: **scaffold + architecture-derived unit tests + M1 contracts guard + M3 parity guard
for all six contracts + the M12 attestor mechanism/record suite + M14 persistence guards** —
**223 collected: 222 passed, 1 failed, 0 skipped.** The one failure is **pre-existing and
inherited from `main`** (recorded below and as §11.15 by M14 independently); `test_policy.py`
is **75 passed, 0 failed, 0 skipped** and is byte-identical to the tree whose guards were
mutation-proven.

**Composition, and it closes exactly** (both branches were cut from `4b03c55`, so their
deltas are separable and the arithmetic is a check rather than a guess):
```
  180   4b03c55  — the merge base, measured directly in a throwaway worktree
+  12   M12       — test_policy.py 63 → 75
+  31   M14       — test_store_db.py 9 → 33, plus new test_store_records.py (+7)
= 223   measured, on both matrix legs
```
**M14's own log states its contribution as "+40", and that is wrong by 9.** It counted the
*final size* of its two files (33 + 7 = 40) as its *delta*, but `test_store_db.py` already
held 9 tests at `4b03c55` from an earlier module, so the real delta is **+31**. Its implied
baseline of ~171 is therefore not a real count; **180 is**, confirmed by direct measurement
rather than by picking a side. Not a functions-vs-items confusion either — at `4b03c55` there
were 180 items against 165 `def test_` functions (a 15-case parametrised spread), and 171 is
neither number. Recorded rather than edited: the M14 entry is not this session's to rewrite
(append-only, and it is another module's log), so the correction lives here and in the M12
entry below. **Third count in three sessions to be wrong in-tree, and all three were
"contribution" figures rather than totals** — a total is measured, a contribution is
arithmetic, and the arithmetic is where the errors are.

Last verified 2026-09-27 on **both CI-matrix legs — 3.11.16 and 3.12.14**, `1 failed, 222
passed` **identical on each**, validator exit 0 with `OK 6/6 schemas covered` on both, and
**0 skipped measured via `-rs`** (no skip section at all, so it is observed rather than
inferred). 3.14.7 was also green pre-merge at 192/191 and is a deliberate
forward-compatibility leg. Run as **uid 1000, not root**, so all 21 `SKIP_AS_ROOT`-decorated
cases actually executed rather than skipping — the 0555-directory and `EACCES` paths were
genuinely exercised, which is the stronger result. **Zero residue**:
`find . -name '.attestor_write_probe'` returns nothing, no `attestation.db`, no `artifacts/`,
and the tree was clean before and after. 3.10 is the documented dependency floor and 3.14 a
forward-compat leg, and **both are green but enforced by nothing** — widening `tests.yml` is
a **decision owed**, not a fix (see Known gaps). 3.13 has no interpreter and is untested.

> **The one failure, stated precisely, because "unfinished work" is the wrong label.**
> `test_models_parity.py::test_demo_traceability_fixture_loads_into_model` asserts every
> link in `fixtures/demo_traceability.json` is tier `E0`, but M2's realistic corpus
> (`88095b2`, merged as `4b03c55` = HEAD) set them to **E4 and E2** and updated
> `test_schemas_contracts.py` — **not** `test_models_parity.py`. It is a **missed test-guard
> flip (rule 4 / Convention 10) in a merge**, not a stub that later work will resolve, and
> it is **two** stale assertions (lines 385 and 387; the `locations == []` one fails next),
> not one. Proven pre-existing by running the suite against a pristine `git archive HEAD`
> extraction: `1 failed, 179 passed` — same test, same failure, with M12 absent.
> **Not actioned by this session:** `test_models_parity.py` is M3's file (§0.4) and the
> fixture is M2's, so fixing it from here would be a two-owner edit. Owner: M3, one line,
> and it needs a decision rather than a green-washed rerun.

**M14 (2026-09-27, this session):** the suite is **210 tests** — the 118 baseline
moved (`main` gained M2-fixture PR #43 and fix PR #46). **209 pass + 1
pre-existing failure** on 3.11.9 and 3.12.14 (clean venvs from
`backend/requirements.txt`; validator exit 0 both legs). The failure is
`test_models_parity.py::test_demo_traceability_fixture_loads_into_model`
(M2 fixture drift — E4/E2 in the fixture vs the test's E0 expectation;
recorded as `architecture.md` §11.15, owners M2+M3, not fixed here). M14's own
40 tests (33 `test_store_db.py` + 7 `test_store_records.py`) are green on both
legs, and all 5 new guards are mutation-proven lethal.

## Layout

```
pyproject.toml                     pytest config only (not an installable package)
.github/workflows/tests.yml        CI: matrix py3.11/py3.12 → pytest + contract validator
backend/requirements.txt           runtime + test deps (pytest 9.0.3, pytest-asyncio 1.4.0)
backend/tests/
  __init__.py                      makes pytest put backend/ on sys.path (imports are `app.*`)
  conftest.py                      autouse isolation: DB + artifacts → tmp_path, queue drained (M15)
  test_scaffold.py                 Session-11 smoke tests (pipeline, policy, metric-empty)
  test_gates.py                    §3 stage stubs: shapes, stage order, exit_code=1 blocks
  test_pipeline.py                 §1/§4 chaining, run-id format, queue wiring + persistence (flipped M15)
  test_policy.py                   §8 attestor: the 5-grant/2-deny sets, fail-closed both ways,
                                   the worker-capability resolver, the real workspace write-probe
                                   (which mechanism refused + the mount's own ST_RDONLY answer),
                                   and the auditor record M9 embeds
  test_metric.py                   §9 seven operators, rate math, exposure-schema conformance
  test_llm.py                      §7 mock determinism; watsonx fails loud; zero-network proof
  test_schemas_contracts.py        §10 pydantic↔contract parity, fixture validation, validator wrap
  test_models_parity.py            M3 model↔contract bijection, field coverage, strictness + honesty pins
  test_api.py                      §5 route table + health/webhook + live runs/metrics + _dist mount (M15)
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
| §1/§4 | runtime shape, data flow, pipeline chain | `test_pipeline.py` |
| §3 | six gates, schemas, config, LLM clients, metric, policy | `test_gates.py`, `test_schemas_contracts.py`, `test_models_parity.py`, `test_config.py`, `test_llm.py`, `test_metric.py`, `test_policy.py` |
| §5 | API surface (health, webhook, runs, metrics) | `test_api.py` |
| §6 | persistence (SQLite WAL, hash-sha256 artifacts) | `test_store_db.py`, `test_store_records.py` |
| §7 | LLM dual-mode + spend discipline | `test_llm.py` |
| §8 | read-only attestor (the differentiator) | `test_policy.py` (declaration + observation + record) |
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
11. **Absence of evidence is three-valued, and never rounds down to a finding**
    (Session 22). When a second, corroborating reading is added next to a
    control — `mount_readonly` beside the refused write — "we could not ask" must
    be `None`/`null` and not `False`, or an unaskable platform starts asserting a
    fact about a mount nobody read. Assert with `is None`, never `not ...`, so
    the falsy value cannot satisfy the test. Corroboration **never gates**: if the
    corroboration were required, a platform without the call would refuse to start
    and the refusal would say nothing about whether the control held. The control
    keeps gating on its own evidence; the second reading only makes the record
    more specific. The mirror-image rule is that a corroborating reading must not
    be allowed to *override* the control either — a flag claiming a read-only
    mount on a directory that just accepted a write is a fail-open, so the
    precedence is asserted in the test that makes the two disagree.

## Known gaps (not covered yet)

- **Frontend**: `frontend/` has no test script or runner — dashboard is
  uncovered (out of scope for this session).
- **§11 open gaps**: `watsonx_client` past the key check. (The unwired queue, stub
  routers and the `_dist` three-level climb were closed by M15's core slice —
  their characterization tests were flipped in the same change, per convention 4.)
- **`app.attestor` has no non-test caller** (Session 22). `enforce_worker_read_only`
  is covered thoroughly here and invoked by nothing — the wiring belongs to M7/M10,
  and M9 owns embedding `PolicyRecord.to_dict()` in the emitted record. The gap is
  recorded in `architecture.md` §11.5. It is a wiring gap, **not** a coverage gap,
  and the distinction matters: adding a caller from this session would have meant
  editing another module's exclusive file (rule 7).
- **The positive read-only-mount case is unreachable without root**
  (`architecture.md` §11.5's mount gap, adjacent). No test can put `tmp_path` on a
  read-only mount, so `mount_readonly is True` is covered by substituting
  `os.statvfs` — named as a substitution in the test, per the module docstring's
  inventory. A real mount is not something CI can produce, so the reading stays
  synthetic; when M10 deploys the D6 bind mount, that is where it gets proven for real.
- **Async jobs/worker**: the lifespan start/cancel path and the persistence side of
  the queue are covered (`test_pipeline.py`), but the worker's "one failed run must
  not kill the queue" branch is exercised only indirectly — add a direct harness when
  M10 does its full pass.
- **Python 3.10 floor**: dependency floor (fastapi/uvicorn/jsonschema/pytest
  all require ≥3.10) is not in the CI matrix; add if floor support matters.
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

### 2026-09-27 — M12: declaration, observation, and the mechanism between them

> **Heading relabelled, content untouched.** This entry was "Session 22" until the merge
> that unblocked PR #48: `main` independently carries *"Session 22: M14 persistence guards"*
> from a parallel session, and two entries sharing a number in one log is a legibility
> defect in a record whose premise is that claims must be checkable. Numbering dropped per
> `AGENTS.md` Convention 18 (cite date + module). **Prose inside this entry still says
> "Session 22"** and means this same entry — deliberately not swept, to keep the diff small
> in a file with an incoming merge conflict. A recorded inconsistency, not a silent one.

- **Target:** `backend/tests/test_policy.py`, the guard `modules.md` §0.2 assigns to M12.
  **Code under test:** `attestor/policy.py` + `attestor/sandbox.py`. No other test file
  needed to change, and no other module's file was touched.
- **Three changes, three shapes of new test.** **A** (a refused write is two findings, so
  the record names the mechanism and reports the mount's own `ST_RDONLY` answer) added the
  mount-reading cases; **B** (the record names the workspace) added the path assertions;
  **C** (the ungated path leaked a denied capability) added the raise cases. The A tests
  are the ones worth arguing about, and the argument is in the tests themselves.
- **The fail-open direction is the one tested for real.** `test_a_writable_workspace_
  reports_a_writable_mount_too` reads a genuinely writable directory with no mock, because
  a mount reading that only ever returns `False` would pass every test while claiming a
  mount nobody asked about. `test_the_write_is_the_authority_and_the_mount_flag_cannot_
  override_it` then makes the two disagree — the write lands, the flag claims ST_RDONLY —
  and asserts the finding follows the write. That test is the whole reason the ordering
  exists; an implementation that read the flag first would pass everything else here.
- **The absent-answer path has its own test**, because it is where a three-valued field
  usually degrades to two: `os.ST_RDONLY` is deleted and the result asserted with
  `is None` rather than `not ...`, so the falsy value cannot satisfy it. Convention 11
  records the generalisation.
- **Three guards flipped deliberately, each labelled `CHANGED THIS SESSION` in place**
  (rule 4 / `AGENTS.md` Convention 10): `test_probe_does_not_raise_for_an_ordinary_refusal`
  (the `WriteProof` shape grew three keys), `test_enforced_record_shape_is_json_ready` and
  `test_ungated_record_shape_is_json_ready` (`PolicyRecord` grew four). The old shapes no
  longer describe what the code carries, and a shape test that checks only the old keys is
  how a record quietly stops being evidence.
- **A docstring claim that the change falsified, and an inventory recounted rather than
  estimated.** The module docstring said *exactly one test substitutes the OS call*; there
  are now five interactions substituted (one `Path.write_text`, four `os.statvfs`, one
  `ST_RDONLY` deletion), each named where it happens. **The first draft of that recount
  said three `statvfs` substitutions where there are four** — caught by grepping the file
  instead of trusting the count in my head, and corrected before it was written into a doc.
  A second overstatement: `test_the_two_readings_are_reported_separately_not_collapsed`
  described a contrast between two deployments and asserted one, so it was rewritten to
  actually make both readings and assert they differ.
- **Convention 6 honoured:** no product code was changed to make a test pass, and no test
  was weakened or skipped to reach green. The suite **grew** — the new cases are new
  behaviour, and the three flips are shape widenings that keep every existing key.
- **Left alone on purpose:** a pre-existing duplicated `@SKIP_AS_ROOT` decorator on
  `test_enforce_workspace_readonly_returns_the_proof_on_a_read_only_workspace`. Harmless,
  unrelated to this change, and fixing a line nobody asked about inside a diff about
  something else is how diffs get unreviewable.
- **Open at archive:** `app.attestor` still has **zero non-test callers** — a wiring gap in
  M7/M10 and M9, not a coverage gap, and the distinction is recorded in Known gaps above.
  The positive read-only-mount reading stays synthetic until M10 deploys a real D6 mount.

### 2026-09-27 — M12 verification: 192 collected, 191 passed, guards proven

> **Heading relabelled, content untouched** — see the note at the head of the preceding
> M12 entry. This sub-entry was "Session 22 verification"; the number is gone for the same
> reason and its prose still uses it to mean this session.
>
> **The 192 in this heading is a point-in-time figure** describing commit `936db35` before
> the merge with `main`. It is preserved rather than rewritten, per the same rule this file
> applies to every other historical number. **The shipped figure is 223 collected / 222
> passed / 1 failed** — see the `Status:` block for the composition.

- **Run as uid 1000, not root** — so all **21** `SKIP_AS_ROOT`-decorated cases executed
  rather than skipping. That matters: the 0555-directory and real-`EACCES` paths are the
  ones this change reasons about, and a root run would have skipped every one of them and
  proved almost nothing. **Zero skips, zero residue** (`find / -name
  '.attestor_write_probe'` → nothing), source tree byte-identical before and after.
- **The CI matrix was satisfied, but only after provisioning it.** Neither 3.11 nor 3.12
  was installed on this box (`python3.11`/`python3.12` absent, `pyenv versions` empty, no
  conda/uv). **3.11.16 and 3.12.14 were built fresh from `backend/requirements.txt` into
  `/tmp/opencode`** rather than accepting a 3.14.7 result as a pass — Convention 9 is
  explicit that a single-version run is a statement about one interpreter, and the
  platform-sensitive surface here is exactly the errno/`statvfs` behaviour. **Identical
  `1 failed, 191 passed` on 3.11.16, 3.12.14 and 3.14.7**; validator exit 0 on each,
  6/6 schemas.
- **`test_policy.py`: 75 passed, 0 failed, 0 skipped** — baseline `4b03c55` was **63**, so
  **+12**, all twelve passing.
- **Convention 7 satisfied, with a control run and a false kill caught.** Seven mutations
  were applied to a throwaway copy and each was required to kill a *named* test:

  | Mutation | Guard that died | Verdict |
  |---|---|---|
  | M1 ungated `_refuse_leaked` commented out | `test_ungated_record_cannot_advertise_a_denied_capability`, `test_the_ungated_leak_check_is_not_a_completeness_check` | killed |
  | M2 `_refusal_mechanism` always `no_write_bit` | `test_refusal_witness_is_the_errno_the_kernel_gave` | killed |
  | M3 `MECHANISM_NO_WRITE_BIT` reworded to contain `read_only` | `test_mechanism_names_are_distinct_and_none_of_them_blurs_the_weak_one` | killed |
  | M4 mount flag collapsed to two-valued on failure | both `..._undetermined...` tests | killed |
  | M5 `writable = not mount_readonly` (the fail-open inversion) | `test_the_write_is_the_authority_and_the_mount_flag_cannot_override_it` | killed |
  | M6 ungated `workspace_path=""` | `..._names_no_workspace_rather_than_an_empty_one`, `test_ungated_record_shape_is_json_ready` | killed |
  | M7 ungated `workspace_mount_readonly=False` | same two | killed |

  **7 mutations, 7 kills, no survivors.** M5 died on the author's own message —
  *"the mount flag overrode a write that landed"* — which is the exact fail-open the plan
  called impossible, so that one is not incidental.
- **The harness's first score was a false kill, and the control run is what exposed it.**
  M3's naive form (rename the constant in `sandbox.py` only) makes `test_policy.py`'s
  `from ... import MECHANISM_NO_WRITE_BIT` fail at **collection** — pytest exit **2**,
  **zero tests collected**. A harness scoring `rc != 0` as a kill would have credited the
  guard with work it never did, which is the **same defect as Session 21's** first harness
  reporting 7/7 false kills. The control run made it visible; the harness was then hardened
  to accept only exit 0/1 plus a node id outside the known-baseline set, and M3 was
  re-expressed semantically (rename **plus** a resolving alias) so the guard actually ran.
  **Two sessions apart, the same harness bug — worth a standing rule, not a coincidence.**
- **The repo was not clean when verification started, and that is this session's own diff.**
  8 modified files, 875 insertions / 61 deletions, nothing staged, HEAD `4b03c55`, branch
  `m12-attestor-policy`. An earlier verifier caught the tree being rewritten under it
  mid-run (hashes changing between reads) and re-ran against a settled window; the reported
  numbers are for the settled tree, and the source tree was byte-identical after every run.
- **Not fixed, deliberately:** the one pre-existing failure. See the `Status:` block above —
  it is a missed guard flip in the M2 merge, in M3's file, and it will not resolve itself
  when other work finishes. **Filed here rather than left as a remembered red.**
- **Delivery: `936db35`, PR [#48](https://github.com/baronocasiones/Intent-Gate/pull/48)
  OPEN** from `m12-attestor-policy` against `main`. `test_policy.py` is 63 → **75** test
  functions, a strict superset — `comm` against the merged baseline shows **12 added, 0
  removed**, so nothing inherited was dropped.
- **This file is the second of the two that block the merge.** `main` moved to `bf52608`
  (M14, #47) and both sides append a session entry to this log's tail; the rebase was
  attempted and **aborted** on append-vs-append, so `936db35` survives byte-for-byte.
  Resolution is "keep both entries", and see the note in `architecture.md` for why that is
  not purely mechanical: `main` already titles two of its entries *"Session 22"* and
  *"Session 23"*, so this branch's *"Session 22"* collides with them and a keep-both merge
  interleaves unrelated sessions out of date order. **A naming decision is owed, not just a
  merge.**
- **The count in the `Status:` block is the measured one, and it is worth restating its
  composition** so the next reader does not have to re-derive it: 192 collected = 179 at the
  `4b03c55` baseline **+ 12** from this session's `test_policy.py` **+ 1** from the M2
  fixture merge, of which **1 is a pre-existing failure**. A bare count is how "118" went
  stale twice in three sessions; the composition is what actually transfers.
- **Post-merge addendum — the shipped tree is 223, and this session's 7/7 proof still
  applies.** After merging `origin/main` (`bf52608`, M14) at `555f4da`: **223 collected, 222
  passed, 1 failed, 0 skipped**, identical on **3.11.16 and 3.12.14**, validator exit 0 on
  both. **`backend/app/attestor/{policy,sandbox}.py` and `test_policy.py` are byte-identical
  to `936db35`** (blob hashes matched), so the mutation proof was not re-run and did not
  need to be: the artefact that was proven is the artefact that ships. Re-proving ceremony
  on an unchanged file would have been a way of appearing thorough.
- **The merge also settled a cross-session count disagreement, by measurement.**
  M14's log claims a contribution of **+40**; the real delta is **+31**, because
  `test_store_db.py` already held 9 tests at the merge base `4b03c55`. Re-measured in a
  throwaway worktree: **180 at `4b03c55`** is correct, and 180 + 12 + 31 = 223 closes
  exactly. So M14's implied ~171 baseline was never a real count. **Recorded here rather
  than edited in the M14 entry** — append-only, and it is another module's log. Worth
  naming the pattern: this is the *third* wrong in-tree count in three sessions and **all
  three were contributions, not totals.** A total is measured; a contribution is
  subtraction, and the subtraction is where the errors live. When a session reports
  "N tests, M of them new", check the arithmetic against a worktree before it is written down.
- **The pre-existing failure has a second stale assertion, and it is currently invisible.**
  `test_demo_traceability_fixture_loads_into_model` aborts at line 385, so line 387 never
  executes — meaning **no run has ever reported it**. Both were evaluated read-only through
  the model: `evidence_tier` is `['E4','E2']` against an all-`E0` expectation, and
  `locations` is `[['src/refund.py:64'], ['src/refund.py:88']]` against an all-`[]`
  expectation, so **both fail**. **The fix is one guard with two assertions, not one**, owned
  by M2+M3. A reviewer patching only the line the failure names would ship a still-red
  suite and conclude the fix did not work. (This correction supersedes the "lines 385 and
  386" wording above: it is 385 and 387.)


> **Merge point — both entries below are from parallel sessions on the same date, and
> their order here is not a claim about sequence.** The M12 entries (above) and the M14
> guard entry (below) were both branched from `4b03c55` and developed concurrently; the
> merge resolved append-vs-append on this log's tail, purely additive, zero context lines.
> **Both are kept whole.** M12 is placed first because that is the lower-risk edit inside an
> already-conflicted file, not because it happened first. **Two useful agreements between
> the sessions:** M14 independently predicted this exact conflict and named the Session 20
> remedy, and M14 independently diagnosed the same single red test as **§11.15** (M2 fixture
> drift from PR #43) and did not fix it either. The numbering scheme remains owed a decision
> (`AGENTS.md` Convention 18).

### 2026-09-27 — Session 22: M14 persistence guards (32 + 7 tests)
- `test_store_db.py` 9 → 32: env wiring (`_sqlite_path` table, default-from-URL, explicit-wins), `now_iso` str/UTC/ordering, `idx_runs_created_at`, commit-survives-reopen, `created_at` ISO-8601-str type pin (M14 AC 2 **and** M17's missing-coverage item — landed once, here), `set_status` rowcount-0 fail-closed signal, newest-first + limit, `prev_digest` default/threading, store-keys-win, and the D15 self-invalidating guard. **No existing test flipped.**
- New `test_store_records.py` (7, M14-exclusive like M3's parity file): envelope reads, missing→`None`, the M3-obligation-1 projection whitelist (incl. subset tolerance while the envelope is uncontracted), strict-model loads incl. a mixed CERTIFIED/REJECTED record, missing→`None`, malformed→`ValidationError` (the `sandbox.py` posture).
- **Verification (via subagent — bash denied this session):** 209 passed + 1 pre-existing failure on 3.11.9 and 3.12.14 from clean `requirements.txt` venvs; validator exit 0 both legs; guard proof `/tmp/opencode/m14_guard_proof.py` — 5/5 kills, 0 survivors (control green on the M14 files); `git status` shows only the 5 intended M14 files, no `attestation.db`/`artifacts/` pollution. The failure is the §11.15 M2 drift — M14 verified around it, per Convention 6 the fix belongs to M2+M3.
- **Follow-up the same day (verification round on user instruction — audit, then commit if changes needed):** reading the tests against their own claims found **3 weaknesses**, all fixed in `test_store_db.py`, no product code touched:
  (A) `test_write_artifact_hash_independent_of_key_order` was **vacuous** — it hashed two stdlib dumps directly and never called `write_artifact`, so it survived a `sort_keys` deletion that it purported to guard; rewritten to exercise the product.
  (B) the index test pinned the index **name** (`index_list`) but not its **target column** — `ON runs(id)` passed; `PRAGMA index_info` assertion added.
  (C) `test_list_runs_newest_first` could not distinguish `created_at DESC` from `id DESC` (its ids sort in insertion order, so both orderings satisfy the expectation) — added deterministic `test_list_runs_orders_by_created_at_not_id` with a **mocked clock** and reverse-sorted ids, so the three candidate orderings disagree without a microsecond race.
  Count **39 → 40** (33 + 7). Re-verified from scratch: **210 passed + the same 1 pre-existing failure on both 3.11.9 and 3.12.14**, validator exit 0 both legs, tree clean except the one test edit, no pollution; **the §11.15 failure re-proven pre-existing on parent `4b03c55`** via a throwaway worktree (fails there too); mutation proof rerun under Session 21's harness rules (control green, which-test-id reported) — **9/9 killed, 0 survivors, no collection errors**, including MUT6→(B), MUT7/MUT9→(C), MUT8→(A) — each new/strengthened guard seen failing before it was trusted (Convention 7).
### 2026-09-27 — M15: API surface core slice (branch `api-surface`)

> **Heading relabelled per `AGENTS.md` Convention 18 (date + module)** — the draft
> called this "Session 22", which collides with the other "Session 22" entries this
> log now carries from parallel sessions (see `architecture.md`'s log for the full note).

- **Layout:** added `backend/tests/conftest.py` (M15-session-created, M3 deviation pattern —
  `backend/tests/` is M17's path and this is a new file, not an edit to one of M17's).
  It is **autouse**: every test's `pipeline.DB_PATH` + `artifacts.ARTIFACT_DIR` go to
  `tmp_path` and the module-level queue is drained before/after each test. Required
  because product code now persists (Convention 3) and webhook tests enqueue for real
  (`test_pipeline.py`'s queue-starts-empty assertion depends on the drain).
- **Flipped, per convention 4, in the same change as the code:** the three `test_api.py`
  stub-response tests (list / detail-echo / metrics shape) and `test_pipeline.py`'s
  `test_worker_is_async_but_never_started_by_app` (→ `..._and_lifespan_starts_it`).
  `test_route_table_matches_documented_surface` unchanged and still passing. Added:
  webhook-persists, runs-empty/newest-first, detail-404, envelope+artifact-pointer,
  queued-no-artifact, metrics-unmeasured, metrics-aggregation, `_dist` path oracle,
  mount-on/off, enqueue-persists, run-persists, crash→`failed`.
- **Stale guard fixed outside M15 (rule 8):** `test_models_parity.py::test_demo_traceability_fixture_loads_into_model`
  pinned the pre-M2 fixture (`E0`, empty locations) — **already failing on main before this
  session** (baseline 13 failed / 167 passed). Fixed to the fixture's actual E4/E2 + locations.
- **Result:** **179 passed / 12 failed** on Python 3.12.10 in a fresh venv built from the
  fully-pinned `requirements.txt` (built in `%TEMP%`, so no venv polluted the tree);
  validator exit 0 (6/6). **All 12 remaining failures are pre-existing on `main`**:
  `test_policy.py` — M12's sandbox probes POSIX read-only directories and Windows does not
  enforce `chmod` on directories, so the probe finds them writable and fails closed.
  Platform gap (Linux CI expected green), owner M12/M17, **reported not patched**.
- **New convention worth carrying:** when product code gains a side effect (DB/artifact/queue),
  isolate it in the autouse conftest rather than in each test — one patch point, and the
  cleanliness gate stops depending on every future test author remembering Convention 3.

### 2026-09-27 — M17: Windows-proofing test_policy.py (branch `m17-policy-windows`)
- **Baseline:** `test_policy.py` failed on Windows at `main` — M12's POSIX read-only probe vs Windows not enforcing directory `chmod`; plus one missing-symlink-privilege failure at fixture setup. **Fix is test-only** (rule 8, no product code).
- **Fixes, in order:** `dd5e9a8` — capability check in `ro_workspace` (probe write attempted; stated skip where the platform accepts it), `ro_mode_workspace` for the three consistency tests, ELOOP stated skip. Post-merge run — `SKIP_NO_STATVFS` on three of #49's mount-corroboration tests (they pin Linux's real `os.statvfs` reading; Windows has neither `os.statvfs` nor `os.ST_RDONLY`, and the product's `undetermined` answer is correct but not what they assert).
- **Post-merge result (Windows):** **223 collected → 201 passed, 21 skipped, 1 failed** — every skip carries a stated reason; the single failure is §11.15 (`test_demo_traceability_fixture_loads_into_model`, pre-existing main parity, owners M2+M3). Validator exit 0 (6/6). **Pre-merge** at `dd5e9a8`: `179 passed, 12 skipped` of the then-191-test suite, validator 6/6.
- **Merge with `origin/main` (`d6b7139`):** 3 conflicts in `test_policy.py`, all keep-both — two docstring blocks (union: #49's five-OS-substitution inventory + this branch's three-hazard count and ELOOP note) and the ungated-record region (#49's four new tests kept; this branch's `ro_mode_workspace` swap kept, because the merged body references that fixture).
- **Linux CI expectation:** every refusal case and all three mount-corroboration tests run for real (skip conditions fire only where the platform cannot produce the observation); the same §11.15 parity red as `main`, nothing else.

### 2026-09-27 — M15/M10: persistence moved onto M14's helpers (branch `api-surface`)
- **What the tests now pin:** the pipeline's persistence *is* `db.py`'s, so the suite redirects storage at `app.db.DATABASE_URL` — db.py's own contract (Convention 2: the consumer module, never `os.environ`) — instead of a pipeline-private path attribute. The autouse fixture still isolates every test's DB + artifacts to `tmp_path` and drains the module-level queue around each test, so Convention 3 does not depend on any test author remembering it.
- **Guard flip (rule 7, same change):** `test_jobs_submit_enqueues_and_drains_cleanly` no longer claims "nothing consumes it … the app never starts worker()" — the lifespan starts the worker now, and consumption is pinned by `test_worker_is_coroutinefunction_and_lifespan_starts_it`. What stands: `submit()` puts exactly one envelope on the queue, and the test still drains it so the module-level queue stays clean for other tests.
- **Deliberately unchanged by the rewire:** queued row on enqueue, ISO-8601 `created_at`, crash → `failed` **and** re-raise, 404 on unknown id, 500 when a row points at a missing artifact, `/api/metrics` honest-unmeasured, `test_route_table_matches_documented_surface` untouched and green. The rowcount-0 rule-6 path is new *product* behavior (a loud raise), not a new endpoint.
- **Result on Windows, on top of the m17 absorb:** **213 passed, 21 skipped (each with a stated reason), 0 failed**, validator exit 0 (6/6). The 21 skips are M17's platform statements (read-only-directory capability, symlink privilege, `os.statvfs`); Linux CI runs all of them.
- **Against the earlier record on this branch:** the core-slice commit's own run was `179 passed, 12 failed` — all 12 in `test_policy.py`, pre-existing on `main` (M12's POSIX probe vs Windows). The branch is green on Windows because PR #53 was absorbed, **not** because the rewire changed any test outcome.

### 2026-09-27 — Ledger after both merges (branch `api-surface`, at `640f8a9`)
- **Suite as it stands:** **234 collected → 213 passed, 21 skipped, 0 failed** on Windows; `scripts/validate_contracts.py` **6/6**, exit 0. Re-run after `5f6f5c6`, `abdfa6a`, `ac9b373` and `640f8a9` alike — **the merge commits moved no test outcome.**
- **The 21 skips are all M17's stated platform statements** (read-only-directory capability, missing symlink privilege, no `os.statvfs`) plus the root-ignores-the-bit case. None is a disguised red: every one carries its reason at the skip site. **Linux CI runs all of them**, so the skip count is a Windows fact, not a coverage reduction.
- **#52 (Static Frontend) touched no test file**, so the count above is unchanged by that merge and the frontend's static fixtures bring no new backend assertions. Its only collision with this branch was `.gitignore`.
- **The one red this branch inherited, §11.15, is closed** — and the guard that closed it (`test_models_parity.py::test_demo_traceability_fixture_loads_into_model`) now pins the fixture's real E4/E2 content. Because the red was pre-existing on parent `4b03c55`, **a future merge will not flag it**; if M2 or M3 land their own version of that file, check the assertion survived.

### 2026-09-27 — CI close-out and the two-writer rule (M15/M10, M17)
- **Linux CI, current head: both matrix legs pass** (py3.11 + py3.12) on #54 — the §11.15 parity red is closed on that branch, so it is green on both platforms: Linux green in CI, Windows `213 passed, 21 skipped` locally with every skip carrying a stated reason. The Windows run and the Linux run together are the honest picture; neither alone is.
- **#53 stays red until #54 lands, and that is expected.** Its legs fail on the same §11.15 test `main` fails (`1 failed, 222 passed`, run `36313930272`) — a parity red, not a regression, since the branch's diff is test-only. It is documented on the PR rather than papered over locally.
- **Two writers, one worktree (this session):** a parallel session committed in the same tree throughout. The rule that held is **commit explicit paths, never `git add -A`** — one session's commits must never absorb another's in-flight edits. A commit that landed on a foreign branch was recovered by verifying the content and moving the branch ref (`git branch -f`), not by cherry-picking, so no duplicate sha and no second copy of the same change entered history. After absorbing the other session's commits, the suite was re-run rather than assumed.
- **A skip must explain itself:** the 21 Windows skips each name the exact platform limit (read-only-directory capability, symlink privilege, `os.statvfs`) and state that Linux CI runs them. A skip that cannot say what it gave up is not allowed to stand as a pass.
