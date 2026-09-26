# docs/modules.md — Intent Attestation Gate (module implementation briefs)

Per-module briefs that let **5 people + AI agents build this concurrently without
colliding**. Every module states: purpose, spec source, current stub I/O, target
interface, dependencies, acceptance criteria, size, and a worked input→output example.

Status: **created 2026-09-27** against `main` @ `6dda165` (working tree clean).
Scope: all 18 implementable units of the scaffold. This is the *fourth* doc in the set:

| File | Answers | Audience |
|---|---|---|
| `docs/intent-attestation-gate.md` | *What* the product is and why (6 stages, probe model, E-ladder, metric) | everyone, incl. pitch |
| `docs/architecture.md` | What is **true of the code right now** (section-by-section, as-built, plus its honest gap list) | reviewers, new maintainers |
| `docs/test-suite.md` | How the suite is organized and run | test owners |
| **`docs/modules.md` (this file)** | **What each owner must build, and how to prove it** | **the 5 implementers** |

**Precedence rule:** for *as-built* facts, `architecture.md` wins if this file drifts.
For *intent*, `intent-attestation-gate.md` wins. This file owns neither — it owns the
gap between them. Where this file proposes something the source does not define, it is
marked **PROPOSED** and carries a decision ID from the decisions section.

---

## 0. How to use this file

### 0.1 New-owner reading order (~20 min)

1. Section 1, Shared vocabulary — the data shapes every module codes against. Read fully.
2. Section 1.7, the worked end-to-end example — the single most important section. Your
   module's output appears in it; you are implementing one segment of that chain.
3. Your module's own section.
4. Section 0.3 integration rules + the decisions section for anything gating you.
5. `docs/architecture.md` component table and gap list for the as-built truth.

### 0.2 Modules at a glance

`Needs` = modules whose output you consume. `Guard` = the test file that fails when you
break your module (from `docs/test-suite.md`'s coverage map — extend it as you land).

| ID | Module | Path | Size | Needs | Guard |
|---|---|---|---|---|---|
| M1 | Contracts + validator | `contracts/`, `scripts/validate_contracts.py` | S | — | `test_schemas_contracts.py` |
| M2 | Fixtures / demo corpus | `fixtures/` | S | M1 | `test_schemas_contracts.py` |
| M3 | Pydantic mirrors | `backend/app/models/schemas.py` | S | M1 | `test_schemas_contracts.py` |
| M4 | Stage 1 Ingest | `backend/app/gates/ingest.py` | M | M2, M11 | `test_gates.py` |
| M5 | Stage 2 Extract criteria | `backend/app/gates/extract.py` | L | M4, M11 | `test_gates.py` |
| M6 | Stage 3 Deterministic parse | `backend/app/gates/parse.py` | M | M5 | `test_gates.py` |
| M7 | Stage 4 Parallel verify | `backend/app/gates/verify.py` | **XL** | M6, M11, M12 | `test_gates.py` |
| M8 | Stage 5 Adjudicate | `backend/app/gates/adjudicate.py` | M | M7 | `test_gates.py` |
| M9 | Stage 6 Emit + gate | `backend/app/gates/emit.py` | M | M8, M13, M14 | `test_gates.py` |
| M10 | Orchestrator (pipeline + queue) | `backend/app/orchestrator/` | S | M9, M14 | `test_pipeline.py` |
| M11 | LLM layer + config | `backend/app/llm/`, `config.py` | M | — | `test_llm.py`, `test_config.py` |
| M12 | Attestor read-only policy | `backend/app/attestor/policy.py` | S | — | `test_policy.py` |
| M13 | False-certified metric + mutation harness | `backend/app/metrics/` | M | M9, M14 | `test_metric.py` |
| M14 | Persistence (db + artifacts) | `backend/app/db.py`, `store/` | S | M1 | `test_store_db.py` |
| M15 | API surface | `backend/app/routers/`, `main.py` | M | M10, M13, M14 | `test_api.py` |
| M16 | Dashboard | `frontend/` | M | M2, M15 | none (gap — M17 adds) |
| M17 | Test suite + CI | `backend/tests/`, `pyproject.toml`, `.github/` | S | all | — |
| M18 | Demo runbook + env | `backend/.env.example` + runbook below | S | M11, M15 | `test_config.py` |

Sizes: **S** = half a day or less · **M** = about a day · **L** = about two days ·
**XL** = split it (see M7).

### 0.3 Integration rules (what keeps parallel work from colliding)

1. **Contracts first.** A shape that crosses a module boundary is defined in
   `contracts/*.schema.json` **before** the producing code lands. Two people must never
   invent the same shape twice. New field = schema + fixture + validator pair in the
   same change (Convention 3).
2. **One writer per file.** Each module owns its listed paths exclusively. If you need a
   change in someone else's file, raise it in the decisions section or a comment in their
   section — do not edit it. Contended files are listed in 0.4 and need a named owner.
3. **Shape stability.** `pipeline.py` threads each stage's output verbatim into the next
   stage's input. Keep every existing key (`stage`, `ok`, and your payload key) present
   and correctly named; you may **add** keys, never rename or drop one. The frontend and
   every existing test read these names.
4. **Dual-mode survives.** `MOCK_LLM=true` and the frontend fixture fallback must keep
   working at all times (demo-survival rule, `AGENTS.md` Convention 4). A module that
   cannot run without a live watsonx.ai call is not finished.
5. **Never weaken the attestor.** `edit` and `execute` are withheld from the verifier. No
   shortcut, no demo path, no one-off exception. This is the differentiator
   (`AGENTS.md` Convention 8).
6. **A gate blocks by default.** Uncertainty resolves to *not certified*. Any code path
   that cannot decide must return the blocking verdict, never a pass.
7. **Test guards flip deliberately.** Several tests pin today's stubs (`test_gates.py`
   exact-equality assertions, `test_api.py` stub responses, `test_pipeline.py`'s
   unwired-queue characterization). When you replace a stub, update its guard **in the
   same change** and say so in the commit. Never leave a passing test that describes
   behaviour you deleted (`docs/test-suite.md` Convention 4).
8. **Test bug vs product defect.** A failing test is interrogated first: test bug, fix
   the test; real defect, report it and do not patch product code to get green
   (`docs/test-suite.md` Convention 6).
9. **No secrets, no new dependencies without a decision.** Secrets go in the gitignored
   `.env`; `.env.example` only. The 7 pins in `backend/requirements.txt` are deliberate
   and all pre-installed — adding one is a decision, not a convenience.
10. **Docs are written by the session that changes the code.** Append to the session logs
    in `architecture.md` / `docs/test-suite.md`, and to `AGENTS.md` only via `/end`. Do
    not create new `.md` files (Convention 1).

### 0.4 Contended files — assign a single owner before anyone edits

| File | Needed by | Rule |
|---|---|---|
| `contracts/*.schema.json` | M1 owns; M5, M7, M9, M13 request | M1 is the only writer; others request via the decisions section |
| `fixtures/*.json` | M2 owns; M4, M16 consume | M2 is the only writer |
| `backend/app/models/schemas.py` | M3 owns; M4–M9 consume | M3 is the only writer |
| `backend/app/main.py` | M15 owns | M15 only — M10's queue wiring needs a change here, so request it |
| `scripts/validate_contracts.py` | M1 owns | M1 only |
| `pyproject.toml`, `backend/requirements.txt` | M17 owns | M17 only |
| `frontend/src/fixtures.js` | M16 owns; M2 supplies the data | M16 only — and see M2's finding: this file should probably stop existing |

### 0.5 Build waves (the order that unblocks concurrency)

- **Wave 0 — unblock everyone (parallel, no upstream):** M1 contracts · M11 LLM spike ·
  M12 attestor. Nothing depends on them being late; everything depends on them being
  early. **Start here.**
- **Wave 1 — foundation (needs M1):** M2 fixtures · M3 pydantic · M14 persistence. Small
  and independent; they let M13 and M15 be built against real storage.
- **Wave 2 — the stage chain (strictly sequential M4 to M9):** the critical path and the
  demo's spine. M4/M5 can start once M2 + M11 land. **M7 is XL — split it** (see its
  section) so two people work it concurrently.
- **Wave 3 — services (parallel with late Wave 2):** M10 orchestrator · M13 metric ·
  M15 API. M13 and M15 are independent of each other; both need M14.
- **Wave 4 — surface and proof:** M16 dashboard (needs M2 data + M15 endpoints) · M17
  test extension (continuous, not a phase) · M18 runbook.
- **Critical path:** M1 to M2 to M4 to M5 to M6 to **M7** to M8 to M9 to M10 to M15 to
  demo. Everything else floats. Protect this path; when two things compete, the critical
  path wins.

---

## 1. Shared vocabulary and data shapes

### 1.1 Contract catalogue

| Schema | Describes | Produced by | Consumed by | Validated today by |
|---|---|---|---|---|
| `criterion.schema.json` | one atomic acceptance criterion | M5 | M6, M7 | nothing — **gap** |
| `verdict.schema.json` | per-criterion verdict + evidence tier | M8 | M9, M15, M16 | via the `run` `$ref` |
| `run.schema.json` | run envelope (id, status, verdicts, measured) | M9, M10 | M15, M16 | `run` vs `demo_run` |
| `traceability.schema.json` | bidirectional criterion-to-location matrix | M9 | M15, M16 | `traceability` vs `demo_traceability` |
| `exposure.schema.json` | risk-weighted exposure + per-operator rates | M13 | M15, M16 | `test_metric.py` only — **gap** |

**Two verified gaps in M1's scope:** `criterion` and `exposure` are not checked by
`scripts/validate_contracts.py` (its `PAIRS` list has two entries). Convention 3 says no
orphan schemas, so closing this is M1 acceptance criterion 1.

### 1.2 The run envelope (canonical shape)

`fixtures/demo_run.json` — every run the API serves conforms to `run.schema.json`:

```json
{
  "run_id": "demo",
  "status": "PENDING",
  "measured": false,
  "verdicts": [
    { "criterion_id": "AC-1", "verdict": "PENDING", "evidence_tier": "E0",
      "locations": [], "rationale": "stub — gates not implemented yet" },
    { "criterion_id": "AC-2", "verdict": "PENDING", "evidence_tier": "E0",
      "locations": [], "rationale": "stub — gates not implemented yet" }
  ]
}
```

Invariants: `run_id` is `run-{8 hex}` for real runs (`demo` is the fixture's synthetic id,
pinned by `test_api.py`); `measured` stays `false` until a mutation run populates the
metric; `status` is a free string in the contract — **PROPOSED** lifecycle
`queued` to `running` to `certified` / `conditional` / `rejected` / `failed` (**D9**).

### 1.3 Criterion identity

`criterion_id` is `AC-n`, 1-based, assigned in extraction order and stable across reruns
of the same input. The two demo criteria are `AC-1` and `AC-2`. `criterion.text` is the
criterion verbatim from the requirement. `criterion.testable` is M5's quality-gate
output — an untestable criterion is rejected outright, never verified.

### 1.4 Evidence ladder E0–E6 — **PROPOSED, NOT FROM SOURCE**

The source names the ladder (`IBM BOB.pdf` section 3, "E0–E6 evidence ladder") but
**never defines the tiers** — the extracted proposal text contains the phrase and nothing
more. The mapping below is a proposal for the team to ratify or replace (**D1**). It is
shaped to match what the code already implies: `demo_run.json` puts stub verdicts at `E0`
with no locations, and `EvidenceLadder.jsx` counts criteria per tier.

| Tier | Name | Means | Typically reached by |
|---|---|---|---|
| E0 | none | no evidence gathered — stub, or criterion unexamined | default today; `emit` blocks |
| E1 | asserted | criterion recorded, no code examined | M5 output, before M7 runs |
| E2 | located | a named location in the change is tied to the criterion | `CODE_SEARCH` hit |
| E3 | traced | the implementing code path was followed and judged | `LOGIC_TRACE`, `STATE_CHECK` |
| E4 | exercised | a test or deterministic check ran against the criterion | `ERROR_PATH`, test evidence |
| E5 | refuted-checked | absence/invariant claim checked, adversarial pass applied | `ABSENCE_CHECK` + adversarial |
| E6 | corroborated | independently reproduced and hash-chained into the signed record | M9 signer |

Escalation is monotonic per criterion: a verdict carries the **highest** tier actually
reached, and `locations[]` lists everything examined. **PROPOSED (D1):** `CONDITIONAL` is
reserved for E2–E5 (found, not yet provable); `CERTIFIED` requires **E4 minimum**;
`REJECTED` may be asserted at any tier once a refutation exists.

### 1.5 Verdict semantics and the exit code

| Verdict | Meaning | Merge |
|---|---|---|
| `CERTIFIED` | every criterion met, evidence at E4 or above | allowed |
| `CONDITIONAL` | met, with recorded debt or an unproven remainder | allowed **only** with a ledger entry (**D3**) |
| `REJECTED` | at least one criterion refuted | blocked |
| `PENDING` | undecided — stub, crash, or unparsed | blocked |

`emit.exit_code` is the **only** merge signal: `0` for CERTIFIED, `1` for anything else.
It is hard-coded `1` today, which is the correct fail-closed default. A gate that cannot
decide returns `1`.

### 1.6 Two different class lists — do not conflate them

- **Adversarial failure classes** (M7, per criterion): the proposal names **six** —
  boundary, omission, contradiction, implicit, negative, concurrency.
  `docs/intent-attestation-gate.md` says "7 failure classes" while listing six, so **the
  7th is undefined in the source** (**D2**).
- **Spec-mutation operator classes** (M13, benchmark level): exactly **seven**, matching
  `OPERATORS` in `backend/app/metrics/false_certified.py` one-for-one —
  `boundary_drop`, `comparison_inversion`, `threshold_weakening`, `error_path_deletion`,
  `normative_demotion`, `negative_constraint_removal`, `untestability`. This list is
  settled in code; do not "reconcile" it with the adversarial list.

### 1.7 Worked end-to-end example (the contract every module codes against)

One demo PR, two criteria, one of them violated. This is **target** behaviour, not
today's. If your module's output does not match its segment here, that is the bug.

**Input — injected webhook body** (the tunnel-independent demo path, same endpoint as a
real GitHub delivery):

```json
{ "action": "opened", "pr": 142,
  "requirement": "AC-1: refunds over $100 require supervisor approval. AC-2: refund failures must be retried 3 times.",
  "diff_paths": ["src/refund.py"] }
```

| Stage | Module | Target output (abridged) |
|---|---|---|
| 1 Ingest | M4 | `stage: ingest, ok: true, input_keys: [...], requirement: "...", files: [{path, sha256}]` |
| 2 Extract | M5 | `criteria: [{criterion_id: "AC-1", text: "...", testable: true}, {criterion_id: "AC-2", ..., testable: true}]` — an untestable criterion is dropped here with a reason |
| 3 Parse | M6 | `ast: [{criterion_id: "AC-1", kind: "function", node: "src/refund.py::approve"}]` — **no model in this loop** |
| 4 Verify | M7 | `findings: [{criterion_id: "AC-2", probe: "ERROR_PATH", result: "refuted", location: "src/refund.py:88", note: "no retry path"}]` |
| 5 Adjudicate | M8 | `verdict: "REJECTED"`, plus per-criterion verdicts: AC-1 `CERTIFIED` at `E4` with a location; AC-2 `REJECTED` at `E2` with a location |
| 6 Emit | M9 | `exit_code: 1`, `record:` run envelope + traceability matrix + review-debt ledger + exposure, `signed:` hash chain |

**API surface that must then serve it (M15):**

```json
GET /api/runs/run-1a2b3c4d
  -> { "run_id": "run-1a2b3c4d", "status": "rejected", "measured": false,
       "verdicts": [ ...as above... ] }

GET /api/metrics
  -> { "false_certified_rate": null, "measured": false, "by_operator": {} }
```

**And after a spec-mutation run (M13 + M15):**

```json
GET /api/metrics
  -> { "false_certified_rate": 0.25, "measured": true,
       "by_operator": { "boundary_drop":        { "certified": 1, "total": 2 },
                        "comparison_inversion": { "certified": 0, "total": 1 } } }
```

**Direction of the headline number: low is good.** `false_certified_rate` is
`P(CERTIFIED | a spec violation was present)` — a gate that certifies violated specs is
lying. `measured: false` with a `null` rate is the honest pre-measurement state and must
stay visibly distinct from `0.0`: never render "0% false-certified" before you have data.
`ExposureCard.jsx` already distinguishes `unmeasured`; keep that.

---

## 2. Contract and data layer

### M1 — Contracts + validator

**Purpose:** one authority for every shape that crosses a module boundary.
**Spec source:** `AGENTS.md` Convention 3 (contracts-first). **Code:**
`contracts/*.schema.json` (5 files), `scripts/validate_contracts.py` (stdlib +
`jsonschema` only). **Today:** the validator checks 2 of 5 schema/fixture pairs; `run`
resolves `verdict` through an explicit `RefResolver` store.
**Target interface:** unchanged CLI — `python scripts/validate_contracts.py`, exit 0 or 1.

**Acceptance criteria**
- [ ] `criterion.schema.json` and `exposure.schema.json` each get a fixture pair and a
      `PAIRS` entry, closing the orphan-schema gap in 1.1.
- [ ] Every schema the stages need exists **before** its producing module lands. At
      minimum `findings.schema.json` for M7 — if M7 runs ahead, request it here.
- [ ] `test_schemas_contracts.py` passes; validator green in CI.
- [ ] Schemas stay draft-07. Do **not** loosen `additionalProperties` globally — extra
      keys are tolerated by omission, not by opening the schema.

**Size:** S. **Risk:** low individually, but it is on the critical path.
**Note:** `jsonschema.RefResolver` emits a deprecation warning shared with the test suite.
Migrating to `referencing` means a new dependency (**D10**) — leave it for the demo.

### M2 — Fixtures / demo corpus

**Purpose:** the data every stream builds against before backends exist (Convention 4),
and the substrate the metric is measured on. **Code:** `fixtures/demo_run.json`,
`fixtures/demo_traceability.json`. **Today:** two fixtures, both stubbed at `PENDING` /
`E0` with `AC-1` and `AC-2`.

**Verified finding — three divergent copies of the demo data exist:**
1. `fixtures/demo_run.json` — canonical, 2 verdicts. Correct.
2. `frontend/src/fixtures.js` — hand-copied, only **1** verdict (`AC-1`), and a different
   `rationale` string. The frontend's fallback is not the canonical fixture.
3. `frontend/public/fixtures/demo_run.json` — **misnamed**: it contains the *traceability*
   payload (`run_id` + `links`), not a run record. Nothing loads it either — `App.jsx`
   imports `fixtures.js`. It is dead weight.

**Acceptance criteria**
- [ ] One copy, not three: either delete `fixtures.js` and have `App.jsx` fetch
      `/fixtures/demo_run.json` from `public/`, or correct the `public/` file to the run
      shape and make it the single served fixture.
- [ ] The misnamed public fixture is fixed or deleted.
- [ ] Fixtures keep validating against their schemas (M1's pairs).
- [ ] Add a **realistic non-stub** fixture for the demo: at least one run mixing
      `CERTIFIED` and `REJECTED`, with non-empty `locations` and a tier above `E0`.
      Otherwise the dashboard only ever proves it can render emptiness.
- [ ] Add a mutation fixture (at least one `by_operator` entry with a non-null rate) so
      `ExposureCard` can be shown with a real number.

**Size:** S. **Needs:** M1. **Blocks:** M16 and the demo's credibility.

### M3 — Pydantic mirrors

**Purpose:** typed in-process models mirroring `contracts/`, so gates get validation
without re-parsing JSON Schema. **Code:** `backend/app/models/schemas.py`. **Today:**
`Verdict` and `EvidenceTier` literals plus `CriterionVerdict` and `RunRecord`.
**Target interface:** add a `Criterion` model (`criterion_id` / `text` / `testable`)
mirroring `criterion.schema.json`, and an `Exposure` model mirroring `exposure`. Keep
existing model names and defaults — `test_schemas_contracts.py` pins them.

**Acceptance criteria**
- [ ] A model exists for every schema in `contracts/` (parity asserted in
      `test_schemas_contracts.py`).
- [ ] `CriterionVerdict.locations` and `.rationale` keep their defaults (`[]`, `""`) —
      pydantic may default where the schema enforces (`docs/test-suite.md` Convention 5).
- [ ] `Verdict` / `EvidenceTier` literals stay in sync with the schema enums. If M1
      changes an enum, M3 changes in the same commit.

**Size:** S. **Note:** M3 owns this file exclusively; M4–M9 consume, never edit.

---

## 3. The stage chain (M4–M9) — critical path

> Rules shared by all six stages: keep `stage` + `ok` + your payload key (rule 3); accept
> the previous stage's dict **as-is**; return a **dict**, not a model, so `pipeline.py`
> and the existing tests keep working; never raise for an empty result — no findings is a
> valid result. All six are 4–8 line stubs today, pinned by exact-equality assertions in
> `test_gates.py` that you will update in the same change (rule 7). Stage order is
> asserted by `test_stage_names_follow_architecture_order` — do not reorder or rename
> the `stage` values.

### M4 — Stage 1 Ingest

**Purpose:** turn a webhook payload into a normalized bundle: the requirement text plus
the set of changed files, fingerprinted. **Spec source:**
`intent-attestation-gate.md` section 3, Stage 1 (watsonx.ai reads PDF/DOCX/XLSX/images
natively). **Code:** `backend/app/gates/ingest.py` — today returns
`{stage, ok, input_keys}`. **Target interface:** `run(payload: dict) -> dict`, adding
`requirement` (str) and `files` (list of `{path, sha256}`), keeping `input_keys`.

**Acceptance criteria**
- [ ] `files[]` is derived deterministically from the payload's path list — sorted, deduped.
- [ ] `sha256` covers file **content** when reachable; otherwise record explicitly that
      it was not reachable. Never a silent empty string — an unmeasured claim must look
      unmeasured.
- [ ] **No LLM call required.** M4 is normalization; watsonx.ai belongs in M5. If a
      document path needs a model, gate it behind `MOCK_LLM` and say so in the docstring.
- [ ] `test_gates.py::test_ingest_returns_sorted_input_keys` updated in the same change;
      the empty-payload case still returns `input_keys == []`.

**Size:** M — the real work is reading file content from the demo repo (**D4**).
**Needs:** M2 (payload shape), M11 (only for a document path).
**Worked example:** input `{action, pr, requirement, diff_paths}` to output
`{stage: "ingest", ok: true, input_keys: ["action","diff_paths","pr","requirement"],
requirement: "...", files: [{path: "src/refund.py", sha256: "<64 hex>"}]}`.

### M5 — Stage 2 Extract criteria

**Purpose:** produce **atomic, testable** acceptance criteria, quality-gated against
ISO/IEC/IEEE 29148, rejecting unverifiable ones outright. **Code:**
`backend/app/gates/extract.py` — today `{stage, ok, criteria: []}`. **Target output:**
`criteria: [Criterion]` per `criterion.schema.json`, **plus** a
`rejected: [{text, reason}]` channel so rejections are auditable rather than silent
(audit-trail convention).

**Acceptance criteria**
- [ ] Each criterion is **atomic** — one verifiable claim each. "Refunds work and are
      fast" is two criteria, or one rejected criterion.
- [ ] Vague or unverifiable criteria are rejected **with a reason**, surfaced in
      `rejected[]`. Rejection is a first-class outcome, not a silent drop.
- [ ] `criterion_id`s are assigned in order and are stable across reruns of the same input.
- [ ] **Dual-mode:** with `MOCK_LLM=true` this must still return criteria from a fixture
      (rule 4). The mock client's canned `PENDING` verdict is *not* criteria — wire a
      mock path that returns fixture criteria, or M16 has nothing to render.
- [ ] With `MOCK_LLM=false` and no key it must fail **loud** (the existing `RuntimeError`),
      never silently return `[]`.
- [ ] `test_gates.py::test_extract_stub_shape` updated in the same change.

**Size:** L. **Needs:** M4, M11. **Risk:** criteria quality is the demo's credibility —
prompt and parse-robustness work dominates. **Watch:** the ISO 29148 gate is a *filter*,
not a claim of certification; do not market it as compliance.

### M6 — Stage 3 Deterministic parse

**Purpose:** map each criterion to concrete code locations — **deterministically, with no
model in the loop** (this is a headline claim; a model call here breaks it). **Code:**
`backend/app/gates/parse.py` — today `{stage, ok, ast: []}`. **Target output:**
`ast: [{criterion_id, kind, node, locations[]}]`, where `kind` is a parsed construct
(function / method / class / statement) from the ingested files.

**Acceptance criteria**
- [ ] **No LLM client is imported or called** in this module. A test should assert that
      (the same zero-network technique as `test_llm.py`) — it protects a claim we pitch.
- [ ] Parsing uses the stdlib (`ast`) or a real parser, not regex heuristics over source.
- [ ] A criterion with no code location is **not** an error: it yields an empty
      `locations[]` and flows to M7 as unexamined (which blocks by default).
- [ ] cucumber/gherkin feature files, if the demo repo has them, parse through the same
      interface (spec calls out gherkin explicitly).
- [ ] `test_gates.py::test_parse_stub_shape` updated in the same change.

**Size:** M. **Needs:** M5. **Note:** a pure-Python parse is a selling point in the
pitch ("the extraction loop has no model in it") — keep it pure.

### M7 — Stage 4 Parallel verify — **the XL module, split it**

**Purpose:** the heart. Verify each criterion with 5 static probes plus an adversarial
pass, fanning out N independent workers (N **OS processes**, not model-invoked
subagents), all LLM reasoning via watsonx.ai, all under the read-only attestor policy.
**Code:** `backend/app/gates/verify.py` — today `{stage, ok, findings: []}`.

**Probes (fixed by the proposal):** `CODE_SEARCH`, `LOGIC_TRACE`, `STATE_CHECK`,
`ERROR_PATH`, `ABSENCE_CHECK`. **Adversarial classes:** six named, seventh undefined
(**D2** — see 1.6). **Target output:** `findings: [{criterion_id, probe, result, location,
note, evidence_tier}]`, conforming to the `findings.schema.json` M1 must add.

**Suggested split so two people can work it at once:**

| Sub-task | Owner scope | Depends on |
|---|---|---|
| **M7a** — probe execution | The 5 probes, deterministic first, no model: search, AST walk, state scan, error-path scan, absence check | M6 |
| **M7b** — fan-out + adversarial | Worker pool (OS processes), watsonx.ai reasoning per criterion, adversarial pass, findings assembly | M7a, M11, M12 |

Agree the `findings` shape between them **before** either starts — that is M1's
`findings.schema.json`. This is the single highest-risk interface in the project.

**Acceptance criteria**
- [ ] Every finding cites a `criterion_id`, the `probe` that produced it, a `location`
      (file plus line where possible), and a `note`. A finding with no location is not
      admissible evidence (audit-trail convention).
- [ ] `evidence_tier` per criterion is the **highest** tier actually reached, monotonic
      (see 1.4).
- [ ] Fan-out is N **OS processes**; each is spawned under the attestor policy. Do not
      implement fan-out as model-invoked subagents — the source is explicit, and the
      Figure 6 footer note documents the distinction.
- [ ] `assert_read_only(...)` is called on the worker capability set at startup
      (**D6** — today it is test-only). A worker that cannot prove read-only does not start.
- [ ] **Dual-mode:** with `MOCK_LLM=true` the stage completes using fixture findings.
      `MOCK_LLM=false` without a key fails loud.
- [ ] Deterministic probes run **without** the model and are labelled as such in the
      finding, so the demo can show "this tier cost no tokens".
- [ ] Budget metering: N workers x prompt size is bounded and reported. A single
      criterion group must not be able to exhaust the watsonx.ai budget (**D11**).
- [ ] `test_gates.py::test_verify_stub_shape` updated in the same change; add tests for
      probe-per-finding, tier monotonicity, and worker read-only enforcement.

**Size:** XL — do not attempt alone. **Needs:** M6, M11, M12.
**Risk:** highest in the project. If M7 slips, the demo has a spine with no muscle.
Consider a reduced demo scope: 1 criterion group, 2 probes, mock-first, live as a
stretch (**D12**).

### M8 — Stage 5 Adjudicate

**Purpose:** collapse findings into the E0–E6 ladder and a per-criterion verdict, then
one run-level verdict. **Code:** `backend/app/gates/adjudicate.py` — today
`{stage, ok, verdict: "PENDING"}`. **Target output:** run-level `verdict` **plus** a
`verdicts: [CriterionVerdict]` array conforming to `verdict.schema.json`, each with
`criterion_id`, `verdict`, `evidence_tier`, `locations[]`, `rationale`.

**Acceptance criteria**
- [ ] Output satisfies `verdict.schema.json` per element (M1 validates).
- [ ] A criterion with no findings is **not** silently certified: it becomes `PENDING`
      with a rationale saying it was not examined (rule 6).
- [ ] `locations[]` aggregates every location examined, not just the deciding one.
- [ ] `rationale` is non-empty and criterion-specific. The rationale is the artefact an
      auditor reads; "looks fine" is a defect.
- [ ] Run-level verdict: CERTIFIED only if every criterion is CERTIFIED; REJECTED if any
      is REJECTED; else CONDITIONAL if any CONDITIONAL; else PENDING (**D3**).
- [ ] `test_gates.py::test_adjudicate_returns_pending_verdict` updated in the same change;
      add table-driven tests for the aggregation rules above.

**Size:** M. **Needs:** M7. **Note:** this is pure logic over M7's output — cheap to
test exhaustively, and the highest test-coverage value per hour in the project.

### M9 — Stage 6 Emit + gate

**Purpose:** emit the artefacts an auditor accepts and compute the merge signal:
traceability matrix, signed hash-chained record, review-debt ledger, risk-weighted
exposure, and `exit_code`. **Code:** `backend/app/gates/emit.py` — today
`{stage, ok, exit_code: 1, record: verdict}`. **Target output:** `exit_code` plus
`record` conforming to `run.schema.json`, and pointers to (or inline copies of) the
traceability matrix, ledger, and exposure.

**Acceptance criteria**
- [ ] `exit_code` is derived, not hard-coded: `0` only for run-level CERTIFIED, `1`
      otherwise. Keep the current fail-closed default until the derivation is proven.
- [ ] Traceability matrix conforms to `traceability.schema.json` — criterion to location
      in both directions, so a reviewer can go from a requirement line to code and back.
- [ ] Signed record: extend the per-file `sha256` in `store/artifacts.py` to a **cross-file
      chain** (each artifact carries the previous digest) so tampering is detectable
      across the run (**D8**). Per-file hashing alone is tamper-evident, not chained.
- [ ] Review-debt ledger: one entry per `CONDITIONAL` criterion, naming the debt and its
      owner-if-known. An unrecorded conditional is a contract violation.
- [ ] Risk-weighted exposure per repo/capability with a decay curve. If the decay curve
      is not implemented, ship the unweighted number **labelled as unweighted** — do not
      imply weighting that does not exist.
- [ ] `record` still echoes the adjudicate output (the existing test asserts
      `record.stage == "adjudicate"` and `record.verdict`); extend alongside, do not
      replace.
- [ ] `test_gates.py::test_emit_blocks_by_default` updated in the same change.

**Size:** M. **Needs:** M8, M13, M14. **Note:** the signed record is a moat claim
("an evidence format an auditor accepts") — do not ship it unsigned and call it signed.

---

## 4. Services and infrastructure (M10–M15)

### M10 — Orchestrator (pipeline + queue)

**Purpose:** own run lifecycle — mint the id, execute the six stages, persist the
result, and (once wired) run off the request path. **Code:**
`backend/app/orchestrator/pipeline.py` (`enqueue_run`, `run_pipeline`) and
`jobs.py` (`submit`, `worker`). **Today:** `run_pipeline` chains the six stages
synchronously and is the only exercised path; `enqueue_run` mints `run-{8 hex}` and
returns; `jobs.submit` enqueues but **nothing ever starts `worker()`** (a characterized
gap, pinned by two tests in `test_pipeline.py`).

**Target interface:** `enqueue_run(payload) -> str` persists a `queued` row and submits
to the queue; `run_pipeline(payload) -> dict` remains the synchronous path (tests and
the injected-payload demo depend on it); `worker()` is started once at app startup.

**Acceptance criteria**
- [ ] **Wire the queue:** `enqueue_run` persists and submits; `worker()` starts from the
      app lifespan in `main.py` (**M15 owns that file** — request the change, do not
      edit it). Until then `GET /api/runs` has nothing to list.
- [ ] `run_pipeline` writes the `runs` row and calls `write_artifact` (**M14**) and flips
      the stored `status` — today nothing is persisted anywhere (M14's functions have
      zero callers).
- [ ] A stage that raises must not lose the run: catch per stage, store the failure, and
      leave the run in a blocking state (rule 6). A crash must never read as CERTIFIED.
- [ ] Flip `test_worker_is_async_but_never_started_by_app` **in the same change** (rule 7).
- [ ] The module-level `_queue` stays clean between tests — the existing suite drains it
      manually and depends on that.

**Size:** S. **Needs:** M9, M14. **Risk:** low effort, high unblock value — this is what
makes the API and dashboard show real data.

### M11 — LLM layer + config — **do the research spike first**

**Purpose:** the single sanctioned path to watsonx.ai, plus the runtime config that
selects mock vs live. **Code:** `backend/app/llm/watsonx_client.py` (`complete`),
`llm/mock_client.py`, `config.py`, `backend/.env.example`. **Today:** mock returns a
deterministic canned verdict with zero spend; the live client raises `RuntimeError`
without a key and `NotImplementedError` past it (IAM token exchange + generation call
are unimplemented). **The research spike is answered in `docs/watsonx-integration.md`;
this module is still unimplemented.**

**Spike answer (recorded 2026-09-27, full dossier: `docs/watsonx-integration.md`)**
- **Auth** — two steps, not one. The API key is exchanged at
  `POST https://iam.cloud.ibm.com/identity/token` (form-encoded
  `grant_type=urn:ibm:params:oauth:grant-type:apikey&apikey=…`) for an `access_token`, sent as
  `Authorization: Bearer …`. **`expires_in` is 3600s** — cache the token *with its TTL* and
  re-exchange on expiry. A permanent cache would pass every test and fail the live demo at minute
  61. watsonx also accepts the key directly via basic auth for dev/test; use the IAM path in
  production (key lookup costs a service-side round trip).
- **Endpoint** — `POST /ml/v1/text/chat` with `messages[{role, content}]`, `temperature=0`.
  Rejected: `/ml/v1/deployments/{id}/text/generation` (marked legacy, needs a deployment id) and
  `/v1/chat/completions` (its response envelope is documented inconsistently across two reference
  pages — do not write a parser against an ambiguous contract).
- **Output validity** — `response_format: {"type": "json_object"}` guarantees JSON;
  `{"type": "json_schema", …}` / `guided_json` constrain the model to a supplied schema. Point
  `guided_json` at the target contract and the contract becomes the model's output grammar. Needs
  **D1** ratified first to know *which* schema.
- **Spend** — every response returns `usage.{prompt_tokens, completion_tokens, total_tokens}`, so
  the D11 meter is counted, not estimated. Rate limit is `429` / code `rate_limit`; bounded
  backoff, and let the D11 ceiling be the real guard.
- **Model id** — do **not** hardcode a guess. `GET /ml/v1/foundation_model_specs` returns the ids
  this account can reach with `input_tier`/`output_tier`. `WATSONX_MODEL_ID` becomes a required
  config value.
- **Read-only, adjacent finding** — watsonx Orchestrate runs Python tools in a **read-only
  filesystem**; `ToolPermission.READ_ONLY` is deprecated and is *not* a live control. See **D6**.

**Acceptance criteria**
- [ ] **Spike: research DONE, code NOT done.** The four spike questions are answered above and in
      `docs/watsonx-integration.md`; §10 of that dossier lists the five items that still need a
      provisioned account (provisioning, region, model id, burn plan, `version`/`guided_json`
      behaviour). Close those, then land the client.
- [ ] Implement `complete()` for real, or leave it raising — but do not leave a
      half-implemented client that looks live.
- [ ] `MOCK_LLM=true` stays the default-safe path for CI and for a failed live call
      (rule 4). A live failure must degrade to fixtures, never crash the demo.
- [ ] No third model client may appear in `backend/app/llm/` — asserted today by
      `test_llm_package_has_no_third_model_client`. Keep it that way.
- [ ] Secrets never committed; `config.py` reads env at import (tests patch the
      **consumer module**, not `os.environ` — see `docs/test-suite.md` Convention 2).
- [ ] Add a spend/budget guard so one run cannot exhaust the day's tokens (**D11**).
      `usage` comes back on every response, so the meter is counted rather than estimated.
- [ ] New client behaviour needs a test marked `live_llm` that is **never selected in
      CI** (`pyproject.toml` marker already exists). `test_watsonx_with_key_pending_spike` and
      `test_watsonx_with_key_makes_no_network_call` must be flipped deliberately **in the same
      commit** that lands the client — see `docs/watsonx-integration.md` §9.

**Size:** M, but the spike is the schedule risk — do it in Wave 0.
**Needs:** nothing. **Blocks:** M5, M7, and the whole live demo.

### M12 — Attestor read-only policy (the differentiator)

**Purpose:** make the verifier **structurally incapable** of modifying what it verifies.
**Code:** `backend/app/attestor/policy.py` — `GRANTS` = read, subagent, skill, workflow;
`DENIES` = edit, execute; `assert_read_only()` fails closed on a leak or a gap. **Today:**
enforced in tests only, never in the pipeline.

**Acceptance criteria**
- [ ] `assert_read_only` is called on the real worker capability set at worker startup
      (**D6**). This is the difference between a claim and a control.
- [ ] Both failure directions stay covered: a leaked deny **and** a missing grant each
      raise `PermissionError` (asserted today — do not weaken to a warning).
- [ ] The policy is visible in the emitted record (which capabilities the run had), so an
      auditor can see the control was applied.
- [ ] **Never weakened for a demo shortcut** (rule 5, `AGENTS.md` Convention 8). If a
      demo step seems to need `edit`, that is a bug in the demo, not the policy.

**Size:** S. **Needs:** nothing. **Note:** this is the pitch's sharpest differentiator
and a direct IBM read-only-governance angle. Cheap to finish, expensive to lose.

### M13 — False-certified metric + mutation harness — **the publishable number**

**Purpose:** compute and defend `P(CERTIFIED | spec violation present)` by injecting
known spec mutations and reporting per operator class. **Code:**
`backend/app/metrics/false_certified.py` — `OPERATORS` (7, settled) and
`false_certified_rate(results)`, which already returns
`{false_certified_rate, measured, by_operator}` with `measured = total > 0` and a `None`
rate when empty. **Today:** the math is done and tested; **nothing feeds it** (no
mutation harness, no aggregation, no endpoint).

**Acceptance criteria**
- [ ] A **mutation harness** that takes a real criterion, applies one operator, re-runs
      the pipeline, and records the resulting verdict. This is what makes the metric
      measured rather than asserted.
- [ ] All 7 operators are exercised, reported per class. `by_operator` keys stay exactly
      the `OPERATORS` tuple (a test pins them).
- [ ] **The empty case stays honest:** `measured: false` with a `null` rate, never `0.0`
      (rule 6, and 1.7). A pre-measurement dashboard must not imply a good number.
- [ ] Output conforms to `exposure.schema.json`; add the missing validator pair (M1).
- [ ] Corroborating ground truth (Stryker "Survived" mutants) is a **stretch**, not a
      P0. Do not let it block the harness (**D5**).
- [ ] Per-operator rates are reported, not just the pooled rate — the per-class spread is
      the interesting result and the defensible one.

**Size:** M. **Needs:** M9, M14. **Risk:** medium — it depends on the pipeline running
end-to-end, so it is effectively Wave 3. **Note:** Session 11 recommended adjudicate +
metric as the depth-first pair; this is that recommendation, and it is the strongest
publishable claim in the project.

### M14 — Persistence (db + artifacts)

**Purpose:** the run index and the tamper-evident evidence store. **Code:**
`backend/app/db.py` (SQLite, WAL, one `runs` table) and `store/artifacts.py`
(`write_artifact` writes `{sha256, **payload}` to `$ARTIFACT_DIR/{run_id}.json`).
**Today:** both correct and both with **zero callers** — nothing persists.

**Acceptance criteria**
- [ ] `runs` rows are written by M10 and read by M15. `artifact_path` points at the JSON.
- [ ] `created_at` is an ISO-8601 **string** (the column is `TEXT`; a mutation-lab run
      showed nothing currently pins the *type*, so add a test that does).
- [ ] The artifact `sha256` continues to cover the sorted body exactly as today
      (`test_store_db.py` pins it). Cross-file chaining is M9's job (**D8**).
- [ ] `ARTIFACT_DIR` and `DATABASE_URL` remain env-driven; tests keep using `tmp_path`
      so the repo tree stays clean (`docs/test-suite.md` Convention 3).

**Size:** S. **Needs:** M1. **Note:** a `/tmp/opencode/mutation_lab.py` harness exists
from an earlier session — it injects deliberate bugs into a scratch copy of the repo and
reports whether the suite catches them. Useful for M17; it is **not** repo code.

### M15 — API surface

**Purpose:** the four endpoints plus static hosting — the whole external contract.
**Code:** `backend/app/routers/webhooks.py` (live), `runs.py` and `metrics.py` (stubs),
`backend/app/main.py`. **Today:** `POST /webhooks/github` accepts any JSON (real
delivery or hand-injected demo body on the same path) and mints an id; `GET /api/runs`,
`/api/runs/{id}`, `/api/metrics` return hard-coded stubs. **Known defect:** `main.py`
resolves `frontend/dist` by climbing **three** levels from `backend/app/`, landing outside
the project, so the static mount silently never activates even when the dashboard is
built.

**Acceptance criteria**
- [ ] `GET /api/runs` lists real rows (newest first) from M14; `GET /api/runs/{id}`
      returns the run envelope plus artifact pointers, and a `404` for an unknown id
      (**today it echoes any id with `status: "pending"`** — that is a stub, not a lookup).
- [ ] `GET /api/metrics` aggregates M13's function over stored mutation results and keeps
      the exposure contract's three keys exactly (a test pins the key set).
- [ ] **Fix the `_dist` path** (two levels, not three) and prove it: a test that the
      mount appears when a `dist` directory exists is the honest fix, not a comment.
- [ ] Webhook: verify the GitHub signature when a secret is configured (**D7**), keep the
      injected-payload path working with no secret (demo survival), and submit the run
      to the queue (needs M10 + the `main.py` lifespan change).
- [ ] GitHub write-back (PR comment + check run) is a **stretch** (**D13**), not a P0 —
      the non-zero exit is the merge-blocking claim and it already works.
- [ ] Flip the three stub-response tests in `test_api.py` in the same change (rule 7);
      the route-table test must keep passing (no routes added or removed without
      updating it).

**Size:** M. **Needs:** M10, M13, M14. **Note:** M15 owns `main.py`, so M10 and any
lifespan work must go through here.

---

## 5. Surface and proof (M16–M18)

### M16 — Dashboard

**Purpose:** show the verdict, the evidence ladder, the traceability matrix, and the
exposure number — the demo's face. **Code:** `frontend/src/` (`App.jsx`, `api.js`,
`fixtures.js`, 4 components), `vite.config.js` (dev proxy to `127.0.0.1:8000`),
`package.json` (react 18, vite 6 — **never `npm install`ed yet**). **Today:** live-API
first with graceful `null` on failure, then fixture fallback, with a `(fixture mode)`
banner. Works, but has only ever been proven against stub/empty data.

**Acceptance criteria**
- [ ] `npm install` and `npm run build` actually succeed — this has never been run.
- [ ] Fix the three-copy fixture divergence (M2) so the fallback **is** the canonical
      fixture.
- [ ] The dashboard renders a **non-stub** run: mixed verdicts, real locations, a tier
      above `E0`. Verify against M2's realistic fixture, not the empty stub.
- [ ] `ExposureCard` shows `unmeasured` distinctly from a real rate (1.7). This is the
      honesty surface — do not let a null rate render as a number.
- [ ] Production serving works end-to-end: built `dist` served by FastAPI, which depends
      on M15's `_dist` fix. Test both paths (dev proxy and static mount).
- [ ] Handle the realistic states, not just the happy one: a run with zero criteria, a
      criterion with many locations, and an API that is down (fixture mode must not look
      like a real result).
- [ ] No test runner exists for the frontend — that gap is M17's, and it is why the
      `_dist` bug survived: nothing exercised the build.

**Size:** M. **Needs:** M2, M15. **Risk:** the demo dies here if unverified — a
screenshot-quality dashboard that was never built is the classic hackathon failure.

### M17 — Test suite + CI

**Purpose:** keep the 79 green tests meaningful as stubs become logic, and extend
coverage to the modules that have none. **Code:** `backend/tests/` (10 files),
`pyproject.toml`, `.github/workflows/tests.yml` (matrix 3.11 + 3.12, pytest + validator).
**Today:** green on 3.11.9 and 3.12.14 locally; CI unverified in GitHub (the branch was
merged without a push being confirmed as green).

**Acceptance criteria**
- [ ] Every module that lands adds or updates its guard **in the same change** (rule 7).
      A replaced stub with a still-passing old test is a lie.
- [ ] Add the missing coverage that matters most: worker read-only enforcement (M7/M12),
      adjudicate's aggregation table (M8), `exit_code` derivation (M9), `created_at` type
      (M14), the `_dist` mount (M15), and a frontend smoke test (M16).
- [ ] **Zero live LLM calls, ever, in CI.** The `live_llm` marker stays unselected.
- [ ] Keep `tmp_path` discipline so the repo tree stays unpolluted — the cleanliness
      check depends on it (Convention 3).
- [ ] Push the branch and confirm CI is green on both legs; that has not been observed
      remotely yet.
- [ ] Optional hardening, in order: Python 3.10 floor in the matrix; the
      `jsonschema.RefResolver` deprecation (**D10**).

**Size:** S per module, continuous. **Note:** the mutation lab in `/tmp/opencode` is a
ready-made "does the suite actually bite?" harness — worth running once after the stages
land.

### M18 — Demo runbook + env

**Purpose:** make the demo reproducible by someone who did not build it, and survive a
failed live call. **Code:** `backend/.env.example`; the runbook lives in this section.

**Runbook (target state):**
1. `pip install -r backend/requirements.txt`
2. Copy `backend/.env.example` to `.env`; set `MOCK_LLM=true` for the offline path, or
   add `WATSONX_API_KEY` + `WATSONX_PROJECT_ID` for the live path. **Never commit `.env`.**
3. `uvicorn app.main:app --reload` from `backend/` (port 8000).
4. `npm install && npm run dev` in `frontend/` for the dev proxy — or build and let
   FastAPI serve it (needs M15's `_dist` fix).
5. Demo without a tunnel: `curl -X POST localhost:8000/webhooks/github -d '{...}'` with
   the injected payload from 1.7. The same endpoint accepts real GitHub deliveries.
6. Optional live webhook: Tailscale Funnel is already active on `arch-thinkpad`
   (`https://arch-thinkpad.tailbb0f08.ts.net` to `127.0.0.1:8000`, public TLS verified) —
   reusable, no cloudflared/ngrok needed.

**Acceptance criteria**
- [ ] The runbook is executed **by someone who did not write it**, start to finish, and
      the failure is fixed. An unrun runbook is not a runbook.
- [ ] The demo survives a dead watsonx.ai: with `MOCK_LLM=true` or pre-computed
      artifacts, the full verdict-to-exposure path still renders (rule 4).
- [ ] Fallback video recorded (Convention 6); final 4 hours are rehearsal only.
- [ ] `.env.example` documents every variable M11/M14 read, with safe defaults.

**Size:** S. **Needs:** M11, M15.

---

## 6. Decisions that gate modules

Nothing below is settled. Each item names the modules blocked, so nobody stalls silently
— if you are blocked and cannot reach the owner, take the recommended default and
record that you did.

| ID | Decision | Blocks | Recommended default |
|---|---|---|---|
| **D1** | E0–E6 tier semantics — undefined in the source (1.4) | M7, M8, M9, M16 | Ratify the 1.4 table; CERTIFIED requires E4. **Urgent (2026-09-27):** watsonx.ai `guided_json` can constrain model output to this schema, so D1 now gates the cleanest output-validity story we have — not just the tier display. See `docs/watsonx-integration.md` §4 |
| **D2** | The 7th adversarial failure class — source names six (1.6) | M7 | Ship six; say "six" in the pitch |
| **D3** | Verdict aggregation + whether CONDITIONAL may pass the gate (1.5) | M8, M9 | REJECTED blocks; CONDITIONAL needs a ledger entry |
| **D4** | Demo repo target — needs real acceptance criteria to attest against | M4, M5, M13 | Smallest repo with genuine written criteria; inject payloads until chosen |
| **D5** | Stryker corroboration of mutation ground truth | M13 | Stretch — harness first, corroboration if time |
| **D6** | Where read-only is enforced: worker startup vs pipeline wrapper | M7, M10, M12 | Assert at worker startup, fail closed. **Mechanism now specified (2026-09-27):** read-only bind mount of the workspace + a pre-flight capability check, modelled on watsonx Orchestrate's tool sandbox, which runs Python tools in a read-only filesystem. `ToolPermission.READ_ONLY` is deprecated and is *not* a live control — do not cite it. See `docs/watsonx-integration.md` §6 |
| **D7** | Webhook signature verification, and behaviour with no secret configured | M15 | Verify when a secret exists; allow injection when not |
| **D8** | Cross-file hash chain format | M9, M14 | Each artifact carries the previous digest |
| **D9** | `status` lifecycle values (1.2) | M9, M10, M15 | The PROPOSED set in 1.2 |
| **D10** | Migrate off deprecated `jsonschema.RefResolver` | M1, M17 | No — not during the build |
| **D11** | Per-run token/cost ceiling | M7, M11 | Hard cap per criterion group; report spend per run. **Data source now known:** every watsonx.ai response carries `usage.{prompt_tokens, completion_tokens, total_tokens}`, so only the policy is open. See `docs/watsonx-integration.md` §5 |
| **D12** | M7 demo scope if the clock slips | M7, M18 | 1 criterion group, 2 probes, mock-first |
| **D13** | GitHub write-back (comment + check run) | M15 | Stretch — after the API serves real data |

---

## 7. Session log (append-only)

### 2026-09-27 — Session 14: module briefs created (this file)
- `/start` instruction: add a description and initial documentation for each module so
  the project can be implemented concurrently. Option A (single new file) + full depth
  (interface, acceptance criteria, worked I/O) confirmed by the user.
- Wrote this file against `main` @ `6dda165`, reading every backend module, all 5
  contracts, the validator, both fixtures, the frontend shell, and the test suite
  directly — no claim here is inferred from a stale doc.
- **Repo state corrected vs `AGENTS.md`:** the branch is `main` (baron was merged in
  `688cc42`, then `6dda165 repo cleanup`); the tree is clean; the AGENTS.md notes about
  "not pushed to origin" are stale.
- **New findings recorded (all verified by reading code, not inferred):** three
  divergent copies of the demo data, one of them misnamed and unused (M2); `criterion`
  and `exposure` schemas have no validator pair (M1); the E0–E6 ladder is named but never
  defined in the source (D1); the "7 failure classes" are six as named (D2); the
  mutation operator list of 7 matches the code exactly and must not be conflated with
  the adversarial list.
- No code changed, no contracts changed, no dependencies added, no decisions taken —
  documentation only.
- Open at archive: all 18 modules unimplemented; D1–D13 unsettled; CI still unverified
  remotely; `AGENTS.md` repo-state section still stale.

### 2026-09-27 — Session 14 archive: committed to `baron` as `ac7a6da`
- User directed the commit to `baron`, not `main`. Committed docs-only (830 insertions,
  one file) as `ac7a6da`. **Not pushed** — no push was requested.
- `baron` had already been merged into `main` (`688cc42`), so committing there **re-diverged
  the branch**: `baron` is now 1 commit ahead of `origin/baron` and 5 behind `main`. The 5
  behind it (PR #1 uploads `ccc4736`/`1b7b647` + `6dda165 repo cleanup`) were never on
  `baron` at all, so the working tree gained no files and the commit is a clean docs-only
  change; a future `baron`→`main` PR would carry this file alone.
- **Correction made mid-session and worth keeping:** the first read of the history assumed
  the 9 root-level files deleted by `6dda165` would be restored on checkout to `baron`.
  They were not — they arrived on `main` via PR #1 (`Aixxn-patch-1`), never via `baron`.
  Verified with `ls` + `git status` before committing rather than acting on the assumption.
- Verification basis: 79/79 tests green and validator OK ×2 were run against `main`
  @ `6dda165` before the branch switch, and were **not** re-run on `baron` (trees differ
  only by the never-shared files above, so the result carries over).
- Follow-ups for the next session: decide whether this lands on `main` directly
  (`cherry-pick ac7a6da`) or ships as a `baron`→`main` PR; ratify or replace D1–D13 before
  Wave 0 starts, since D1 (evidence ladder) blocks M7/M8/M9 and D6 (read-only enforcement
  point) is a one-line change that turns the differentiator from a claim into a control.

### 2026-09-27 — Session 15: watsonx.ai integration research (docs only)
- Instruction: study watsonx.ai documentation and check how it integrates into the system;
  document it and commit.
- Created **`docs/watsonx-integration.md`** (new research dossier, matching the existing
  dossier pattern — `evidence-dossier.md`, `market-sizing-2026-09.md`,
  `ai-code-review-landscape-2026-09.md`). No duplicate created; `modules.md` and
  `architecture.md` were updated in place.
- **M11's spike acceptance criterion is now satisfied** — §M11 carries the answer inline (the
  brief instructed "record the answer in this section") plus a pointer to the dossier. D1, D6
  and D11 gained what the research settled; **no decision was taken and no module was
  rewritten.**
- Research outputs that changed plans rather than just informing them:
  - **`guided_json` / `response_format: json_schema`** can constrain model output to a supplied
    JSON schema. This gives the contracts-first rule its first actual enforcement point on model
    output, and it makes **D1** urgent rather than cosmetic — we cannot point a schema at an
    undefined evidence ladder.
  - **The read-only differentiator (M12/D6) has a platform precedent.** watsonx Orchestrate
    runs Python tools in a read-only filesystem. `ToolPermission.READ_ONLY` is deprecated and
    must not be cited; the filesystem sandbox is the real control. Recommended D6 default is
    unchanged, its mechanism is now specified.
  - **Orchestrate is not being adopted**, and two reasons are now sourced: it puts provisioning
    on the critical path, and its IBM Cloud default model is **Groq-hosted `gpt-oss-120b`**,
    which would silently move inference off watsonx.ai and break Convention 8.
- **Self-correction recorded in the dossier §2:** my earlier claim that the IAM access token
  lasts 30 days and needs no refresh was wrong (`expires_in` is 3600s). A permanent token cache
  would pass every test and fail the demo at minute 61 — the client spec is TTL-aware because of
  it.
- Open at archive: the five items in dossier §10 need a provisioned account (provisioning,
  region, model id, burn plan, `version`/`guided_json` behaviour). M11 remains unimplemented. No
  code, contract, fixture, dependency, or endpoint changed. `AGENTS.md` was updated locally but
  is gitignored and **not** in the commit.
