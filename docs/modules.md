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
| M1 | Contracts + validator | `contracts/`, `contracts/examples/`, `scripts/validate_contracts.py` | S | — | `test_schemas_contracts.py` (19 tests) |
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
| M12 | Attestor read-only policy | `backend/app/attestor/policy.py`, `backend/app/attestor/sandbox.py` | S | — | `test_policy.py` |
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
| `contracts/examples/` | M1 owns | M1 only — M2's `fixtures/*.json` is untouched and remains M2's exclusive path |

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
| `criterion.schema.json` | one atomic acceptance criterion | M5 | M6, M7 | `contracts/examples/criterion.json` |
| `verdict.schema.json` | per-criterion verdict + evidence tier | M8 | M9, M15, M16 | `contracts/examples/verdict.json` (also via the `run` `$ref`) |
| `run.schema.json` | run envelope (id, status, verdicts, measured) | M9, M10 | M15, M16 | `run` vs `demo_run` |
| `traceability.schema.json` | bidirectional criterion-to-location matrix | M9 | M15, M16 | `traceability` vs `demo_traceability` |
| `exposure.schema.json` | risk-weighted exposure + per-operator rates | M13 | M15, M16 | `contracts/examples/exposure.json` |
| `findings.schema.json` | one probe result against one criterion | M7 | M8 | `contracts/examples/findings.json` |

**Orphan-schema gap is now closed.** The two previously unvalidated schemas (`criterion` and
`exposure`) each have an example in `contracts/examples/` and a `PAIRS` entry in
`scripts/validate_contracts.py`. `findings.schema.json` is new this session, added ahead of
M7. The coverage check in `main()` enforces this mechanically — it is no longer a rule
someone must remember.

**Still un-contracted (named backlog, not a silent omission):** the emitted artefact envelope
that `backend/app/receipt/render.py` already reads (`sha256`, `run_id`, `status`, `verdict`,
`exit_code`, `measured`, `verdicts[]`, `traceability`, `exposure` with `weighted` and
`by_operator{op:{certified,total}}`, `ledger`, `policy|capabilities`) has no schema at all.
Also un-contracted: the review-debt ledger, the ingest bundle, and the `ast`. Note that
`criterion.schema.json` and `findings.schema.json` describe the **item** — the `criteria[]`
and `findings[]` arrays M5 and M7 actually emit are not themselves contracted, and that is
deliberate (the arrays are stage-internal; only the items cross module boundaries).

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

### 1.4 Evidence ladder E0–E6 — **RATIFIED (D1). Still not from the source.**

The source names the ladder (`IBM BOB.pdf` section 3, "E0–E6 evidence ladder") but
**never defines the tiers** — the extracted proposal text contains the phrase and nothing
more. The mapping below was written by us, and **ratifying it ratified our own proposal,
not a definition recovered from the source.** That distinction has to survive into every
artefact that shows a tier: a pitch slide, a screenshot, a run record. "E4" means what
*we* decided E4 means. Anyone reading it as IBM's taxonomy is reading something that was
never written down anywhere but here.

It is shaped to match what the code already implies: `demo_run.json` puts stub verdicts at
`E0` with no locations, and `EvidenceLadder.jsx` counts criteria per tier.

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
reached, and `locations[]` lists everything examined. **RATIFIED (D1):** `CONDITIONAL` is
reserved for E2–E5 (found, not yet provable); `CERTIFIED` requires **E4 minimum**;
`REJECTED` may be asserted at any tier once a refutation exists.

**Ratified 2026-09-27 (Session 21).** Three consequences, all load-bearing:

1. **The tier is derived by M8, not carried by M7.** A finding states what a probe
   observed; a verdict states how far the evidence reached. `findings.schema.json`
   therefore keeps no `evidence_tier` key and M3's `Finding` mirror declares none — the
   guard `test_findings_result_is_unenumerated_and_tier_is_not_required` now tests a
   design position rather than a deferral. **Consequence to carry, not act on:** if M1
   ever adds the field for M7b, M3 must add it to the mirror in the same change or M7's
   output is rejected by its own strict mirror.
2. **M1's deferred `CERTIFIED ⇒ E4` constraint is now unblocked.** It was deferred
   precisely because D1 was open. Draft-07 `if/then` can express it. Not written — it is
   M1's file, and it belongs with the first emitter that has to honour it.
3. **M7a alone cannot exceed E4** (§1.8), so the `CERTIFIED` floor is exactly reachable and
   never cleared by the deterministic half of Stage 4. That is a property to show, not a
   limitation to apologise for: it is the honest ceiling on what no model in the loop can
   prove.


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

### 1.8 Shared vocabulary settled ahead of the first consumer (Session 21)

Three shapes cross a stage boundary and were undefined until this section. They are written
down **before** the code that produces or consumes them, because a fail-closed rule landing
on a consumer that was never ready reads as a bug — and the cheapest fix under deadline is to
weaken the rule. `AGENTS.md` Convention 13.

#### 1.8.1 The `result` vocabulary (M7 produces, M8 consumes)

`findings.schema.json` deliberately leaves `result` unenumerated — *"its vocabulary belongs
to M7, not M1"*. That is a deferral, and a deferral with two consumers is a hole. Four
values, settled here:

| `result` | Means | Counts as support? |
|---|---|---|
| `refuted` | a probe **positively observed** a construct contradicting the criterion | no — it refutes |
| `supported` | a probe positively observed a construct consistent with the criterion | yes |
| `undetermined` | the probe ran and could not decide | **no** |
| `not_applicable` | the probe does not apply to this criterion | **no** |

`refuted` is already pinned by `contracts/examples/findings.json`. **M8 must treat
`undetermined` and `not_applicable` as non-supporting** — rule 6.

**An unrecognised `result` is fail-closed AND loud — both, not a choice between them.**
M8 must not guess a new category and must not silently treat the finding as nothing:

- treat it as **non-supporting**, so it can never raise a tier or support a
  certification (rule 6);
- **name the unrecognised value in that criterion's `rationale`**, so the run record
  says "probe reported `REFUTED`, which is not a value this gate understands" rather than
  quietly producing a plausible verdict;
- raise the tier to **E1 at most** — a probe that returned something uninterpretable is a
  probe that ran and decided nothing.

The tempting shortcut is a `dict.get(result, UNDETERMINED)` default. That gets the
fail-closed half right and the loud half wrong, and the loud half is the one an auditor
needs: a producer that starts emitting a fifth value is a bug, and a gate that absorbs it
is how the bug survives to a demo.

**This table is not yet a guard, and it must become one.** A vocabulary written only in a
markdown file is a comment: M7 could emit `REFUTED` or `refute`, M8 could disagree, and
this section would still say four values. The mechanical version is owed, and the ownership
is unambiguous — `findings.schema.json` says so in as many words:

- **M7 defines the vocabulary as a module constant** in `gates/verify.py` (its file), and
  emits only those values;
- **M8 imports that constant** rather than restating it, so the two cannot drift;
- **a test asserts M7's constant equals this table.** Until M7a lands, the only anchor is
  `test_finding_result_stays_an_open_string_and_the_example_uses_a_documented_value`,
  which checks the contract's own example against these four values. That is a floor, not
  the real thing.

#### 1.8.2 Absence of evidence is `undetermined`, never `refuted`

**The load-bearing honesty rule of the stage chain.** `ERROR_PATH` not finding a retry does
**not** refute a 3-retry requirement — the retry may be three modules away. Only a *positive
observation of a contradicting construct* may refute. Two corollaries:

- **`ABSENCE_CHECK` can never return `supported` deterministically.** A negative claim is
  not decidable without a model, so M7a returns `undetermined` with a note saying why, and
  E5 stays reserved for M7b's adversarial pass. A probe that "confirms" an absence would be
  a fabricated-evidence generator — the exact failure this project exists to stop.
- **Low precision is safe; a false *match* is not.** A criterion with no location yields
  `locations[] == []` and flows on unexamined. A *wrong* location would let M7 certify
  against the wrong code, so the probes are precision-biased: emit a location only on an
  exact identifier match, and say how it matched.

#### 1.8.3 The threading contract

`pipeline.py` threads each stage's output verbatim forward and is M10's file, so a stage
gets what earlier stages **pass on**. Rule 3 permits adding keys; §0.3 rule 2 forbids
renaming or dropping one. The chain of custody, settled so nobody has to guess:

```
payload  → M4 ingest    {input_keys, requirement, files[], workspace}
         → M5 extract   {criteria[]}                     ← M5, deferred
         → M6 parse     {ast[], criteria[]}              ← threads criteria forward
         → M7a verify   {findings[], criteria[], mode, tokens_spent}
         → M8 adjudicate{verdict, verdicts[], criteria[]}
```

**Why `criteria` is threaded twice, and why it is load-bearing.** `adjudicate.run(findings)`
receives only M7's dict, so M8 **cannot enumerate a criterion it never saw** — yet rule 6
requires an unexamined criterion to become `PENDING` with a "not examined" rationale. Without
the threading, M8 emits `verdicts: []`, and the failure mode is fail-*open* in the worst
way: a run with nothing to check, which reads as "no problems found" rather than "no
evidence gathered". `verdicts: []` must therefore always resolve to run-level `PENDING`, and
that is pinned by a test rather than assumed.

M4's `workspace` and M6's re-verification of M4's hashes are the same kind of obligation: a
stage that needs something the previous stage did not emit must not quietly invent it.

#### 1.8.4 Probe → tier, for M8 to derive

§1.4's "typically reached by" column, made mechanical. **M7a emits no tier; M8 computes the
highest tier its findings justify.**

**The tier tracks the strongest probe that produced a *determinate* observation — in either
direction.** A refutation is evidence too: M2's `demo_run.json` has AC-2 `REJECTED` at `E2`
on the strength of one located contradiction and no more. A table that only counted
`supported` findings would put that verdict at E1 and contradict the fixture we ship.

| Findings for a criterion | Tier |
|---|---|
| none at all | E0 |
| only `undetermined` / `not_applicable` — ran, decided nothing | E1 |
| `CODE_SEARCH` determinate (`supported` **or** `refuted`), with a location | E2 |
| `LOGIC_TRACE` or `STATE_CHECK` determinate | E3 |
| `ERROR_PATH` — a deterministic check actually executed | E4 |
| `ABSENCE_CHECK` + adversarial | E5 — **M7b only** |
| hash-chained into the signed record | E6 — **M9 only** |

Direction and tier are orthogonal. `undetermined` and `not_applicable` never raise the tier
however many probes emit them, because they are not observations — which is exactly why
§1.8.2 forbids manufacturing one.

**M7a therefore cannot exceed E4**, which is exactly the `CERTIFIED` floor. Stated as a
design property: the deterministic half of Stage 4 can *reach* the bar and never clears it.
Crossing it requires the model, and the model is where the evidence stops being free.

---

## 2. Contract and data layer

### M1 — Contracts + validator

**Purpose:** one authority for every shape that crosses a module boundary.
**Spec source:** `AGENTS.md` Convention 3 (contracts-first). **Code:**
`contracts/*.schema.json` (6 files), `scripts/validate_contracts.py` (stdlib +
`jsonschema` only). **Today:** the validator checks all 6 schema/example pairs and fails if
any schema on disk has none; `run` resolves `verdict` through an explicit `RefResolver`
store.
**Target interface:** unchanged CLI — `python scripts/validate_contracts.py`, exit 0 or 1.

**Acceptance criteria**
- [x] `criterion.schema.json` and `exposure.schema.json` each get an example pair and a
      `PAIRS` entry, closing the orphan-schema gap in 1.1. Examples are in
      `contracts/examples/`; coverage is enforced mechanically by `uncovered_schemas()` in
      `main()`.
- [x] Every schema the stages need exists **before** its producing module lands.
      `findings.schema.json` added this session for M7. Probe names (`CODE_SEARCH`,
      `LOGIC_TRACE`, `STATE_CHECK`, `ERROR_PATH`, `ABSENCE_CHECK`) are settled and pinned
      by `test_findings_probe_enum_is_the_five_named_probes`.
- [ ] `test_schemas_contracts.py` passes; validator green in CI.
- [x] Schemas stay draft-07. Do **not** loosen `additionalProperties` globally — extra
      keys are tolerated by omission, not by opening the schema. Verified across all 6
      schemas: each declares draft-07 and none declares `additionalProperties`. Standing
      rule, not a one-off — re-check whenever a schema is added.

**Deferred deliberately (hardening pass — not this session):**
- No `$id` added — not needed to validate examples; add when referencing cross-schema
  within the same document is required.
- No `criterion_id` pattern constraint (e.g. `^AC-\d+$`) — settling the id format is M5's
  work, not M1's.
- No `measured: false ⇒ false_certified_rate: null` constraint in `exposure.schema.json`
  — JSON Schema draft-07 `if/then` would express it, but the constraint belongs to M13's
  invariant, not the wire format.
- No `by_operator` shape constraint — the key vocabulary is M13's.
- No `CERTIFIED ⇒ E4 minimum` constraint — that is D1, and D1 has not been ratified.
- The full hardening pass (patterns, `if/then` constraints, cross-schema refs, `$id`s) is
  a separate session; D1 belongs to its owner before tier constraints are written.

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
      shape and make it the single served fixture. — *half done: the `public/` file is now
      the run shape, but `fixtures.js` still exists and `App.jsx` still imports it, so the
      data is still copied. See M16 request 1.*
- [x] The misnamed public fixture is fixed or deleted. — *fixed 2026-09-27: it holds the run
      record and is byte-identical to `fixtures/demo_run.json`.*
- [x] Fixtures keep validating against their schemas (M1's pairs). — *validator green 2026-09-27;
      `demo_exposure.json` and the served copy are checked in-suite, since M1's `PAIRS` has
      no entry for them.*
- [x] Add a **realistic non-stub** fixture for the demo: at least one run mixing
      `CERTIFIED` and `REJECTED`, with non-empty `locations` and a tier above `E0`.
      Otherwise the dashboard only ever proves it can render emptiness. — *data only: the
      fixture exists (AC-1 `CERTIFIED` at E4, AC-2 `REJECTED` at E2, both located) but the
      dashboard still renders `fixtures.js`. M16 renders it.*
- [x] Add a mutation fixture (at least one `by_operator` entry with a non-null rate) so
      `ExposureCard` can be shown with a real number. — *`demo_exposure.json`, rate 0.25,
      generated by `false_certified_rate()`. Feeding it to `ExposureCard` is M16 request 2.*

**Landed 2026-09-27 (M2):** the corpus is real data now — a `rejected` run (`D9` default
lowercase lifecycle) with one criterion certified at E4 and one refuted at E2, both pointing
into `src/refund.py`; a traceability matrix describing that same run; a mutation fixture at
0.25 with all seven operator keys. Two defaults were taken because their owners were
unreachable, per §6: **D1** (CERTIFIED requires E4) and **D9** (the §1.2 lifecycle values).
Neither is ratified, so no test asserts either rule in general — only what this fixture does.

**Size:** S. **Needs:** M1. **Blocks:** M16 and the demo's credibility.

### M3 — Pydantic mirrors

**Purpose:** typed in-process models mirroring `contracts/`, so gates get validation
without re-parsing JSON Schema. **Code:** `backend/app/models/schemas.py`.
**Implemented 2026-09-27 (Session 18):** `Verdict` / `EvidenceTier` literals plus
**six** models — `Criterion`, `CriterionVerdict`, `RunRecord`, `TraceabilityLink`,
`TraceabilityMatrix`, `Exposure` — all inheriting a strict `ContractModel` base.
Parity with all five contracts is asserted in **`test_models_parity.py`**, not
`test_schemas_contracts.py` (see the deviation note below).
**Completed 2026-09-27 (Session 21):** the sixth contract, `findings.schema.json`
(title `Finding`, landed by M1 that day), had no mirror and was **blocking a green
tree**. Added the `Probe` literal and `Finding` — **seven models, six contracts,
parity 6/6** — and 6 tests. `Finding` has **no defaults** on its five required keys,
keeps `result` **unenumerated** (M7's vocabulary), and carries **no `evidence_tier`**
because D1 is unratified. **This brief reopened and re-closed within one session**;
the count of "five contracts" above is the Session 18 figure, preserved as written.
**Target interface:** keep existing model names and defaults —
`test_schemas_contracts.py` pins them.

**Acceptance criteria**
- [x] A model exists for every schema in `contracts/` (parity asserted).
      **Deviation, deliberate:** the assertion landed in a new
      `backend/tests/test_models_parity.py` rather than in
      `test_schemas_contracts.py`. `backend/tests/` is M17's path (§0.2) and that
      file is not in the §0.4 contended list, so editing it would have created the
      two-owner collision §0.4 exists to prevent. The new file is
      M3-exclusive and deliberately does **not** duplicate the enum, fixture-load
      or round-trip tests already in `test_schemas_contracts.py`.
- [x] `CriterionVerdict.locations` and `.rationale` keep their defaults (`[]`, `""`) —
      pydantic may default where the schema enforces (`docs/test-suite.md` Convention 5).
- [x] `Verdict` / `EvidenceTier` literals stay in sync with the schema enums. If M1
      changes an enum, M3 changes in the same commit. The two new enums-bearing
      mirrors reuse the existing literals rather than redeclaring them.

**Two deliberate asymmetries** (both pinned by tests, both non-obvious):
- **`Criterion` has no defaults.** `text=""` would erase the criterion and
  `testable=False` would silently drop it — and an untestable criterion is rejected
  outright, never verified (§1.3). Its three fields are the criterion's identity.
  `CriterionVerdict`'s two defaulted fields are additive, which is why the
  difference is intentional rather than inconsistent.
- **`TraceabilityLink` is M3's one invented name.** The traceability contract
  declares the link object *inline* under `properties.links.items`, so it has no
  `title` to join the parity test on. Its **shape is still contract-derived and is
  checked against that inline object**; only the name is M3's, because
  `contracts/` is M1's alone. `INLINE_MIRRORS` in the test makes the exception
  **self-invalidating**: if M1 ever promotes it to `traceability-link.schema.json`
  with a `title`, the test fails until the entry is deleted. **Request for M1:**
  promote it, so parity is a clean bijection.
**Strictness — a decision, not a default.** All six models inherit
`ContractModel` with `extra="forbid"`, making these models the **strict** in-process
trust layer while `contracts/` stays the **permissive** interchange layer (none of the
five sets `additionalProperties: false` — six as of Session 21). This matches the
gate's fail-closed

posture (rule 6: uncertainty resolves to *not certified*). It is pinned by
`test_every_model_forbids_unknown_keys` so it cannot silently drift to `ignore`.
**The stage chain is unaffected** — `pipeline.py` passes plain dicts and rule 3
lets gates add keys; these models are for *records*, never for the pass-through.

**Two obligations this strictness creates — both M9/M14's, neither fixable here:**
1. `store.write_artifact` writes `{"sha256": ..., **payload}` (envelope, pinned by
   `test_store_db.py`). Reading an artifact back into `RunRecord` must **project
   the owned keys first**.
2. Stage 6's record is a **superset** of `run.schema.json` — it also carries the
   traceability matrix, debt ledger, exposure and `signed` (§1.7). M9 **cannot**
   validate its own output into `RunRecord` unprojected.

Both are recorded here rather than papered over, because a model that raises on the
real path is a landmine M9 should meet deliberately. Note the alternative
(`extra="ignore"`) would have silently dropped `sha256` instead — a quieter
failure, and a byte-for-byte round-trip through a model would stop reproducing the
artifact.

**Size:** S — done. **Note:** M3 owns `backend/app/models/schemas.py` exclusively;
M4–M9 consume, never edit. `models/__init__.py` was deliberately left alone (no
re-exports; the brief names one file and callers use the full path).

---

## 3. The stage chain (M4–M9) — critical path

> Rules shared by all six stages: keep `stage` + `ok` + your payload key (rule 3); accept
> the previous stage's dict **as-is**; return a **dict**, not a model, so `pipeline.py`
> and the existing tests keep working; never raise for an empty result — no findings is a
> valid result. All six are 4–8 line stubs today, pinned by exact-equality assertions in
> `test_gates.py` that you will update in the same change (rule 7). Stage order is
> asserted by `test_stage_names_follow_architecture_order` — do not reorder or rename
> the `stage` values.
>
> **Two additions settled in Session 21, both in §1.8 — read them before writing your
> stage.** (a) The **threading contract** (§1.8.3): `pipeline.py` is M10's file and
> threads verbatim, so a stage gets what earlier stages pass on. `criteria` is threaded
> forward through M6 and M7a on purpose, because M8 cannot enumerate a criterion it never
> saw and an empty `verdicts[]` is a fail-*open*. (b) The **`result` vocabulary**
> (§1.8.1) and the **absence rule** (§1.8.2): absence of evidence is `undetermined`,
> never `refuted`, and `ABSENCE_CHECK` can never return `supported` without a model.
>
> **And note the constraint the existing order-test imposes on all six:** every gate is
> called with a bare `{}` by `test_stage_names_follow_architecture_order`, so every gate
> must tolerate a foreign empty dict and still return its `stage` name. That is
> fail-closed behaviour by construction. It also means `enforce_worker_read_only` stays
> at **worker startup** (D6) and never inside `verify.run()` — there it would raise
> `PermissionError` with `ATTESTOR_CAPS` unset, in CI, on the order test.

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

**Acceptance criteria (Session 25 — landed on `refactor`, R4 thin slice)**
- [x] Each criterion is **atomic** — via the brief's second alternative: a compound
      candidate is one *rejected* criterion ("split into one verifiable claim each").
- [x] Vague or unverifiable criteria are rejected **with a reason**, surfaced in
      `rejected[]`.
- [x] `criterion_id`s come from the `AC-n:` markers and are stable across reruns
      (no reassignment to drift).
- [x] **Dual-mode: superseded by D-c/D-f.** Extraction is deterministic with no LLM
      in the stage, so both modes behave identically — there is no switch to guard.
      The consumer control §11 gap 9 asks M5 for is the no-import test
      (`test_extract_imports_nothing_from_the_llm_package`), not a fixture path.
- [x] **Loud failure without a key: moot** — no key is ever needed (no client).
      Malformed input (missing/non-string `requirement`) yields empty channels, never a raise.
- [x] `test_gates.py` extract assertion flipped in the same change; behaviour owned
      by new `backend/tests/test_extract.py` (11 tests).
- **Threading (beyond the brief, required by §1.8.3):** `files` + `workspace` pass
  through verbatim — the pipeline threads verbatim, so M6-real's hash
  re-verification depends on keys only M5 can carry forward.

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

**Session 25 (R4 pass-through, landed on `refactor`):** stub threads `criteria` /
`files` / `workspace` (§1.8.3) and anchors one `unresolved` ast entry per criterion.
No-LLM AC ticked (source-asserted in new `test_parse.py`); stdlib-parse and gherkin
ACs stay open for M6-real. `test_gates.py` parse assertion flipped in the same change.

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

**Session 25 (R4 mock stub, landed on `refactor` — probes still out of scope):**
`verify.py` emits the verbatim §1.7 demo findings for AC-1/AC-2 and `undetermined`
for anything else, with machine-readable provenance (`mode: "mock"`,
`tokens_spent: 0`), and threads `criteria` (§1.8.3 — without this M8 emits
`verdicts: []`, the fail-open the threading contract exists to prevent).
Runbook must state the provenance next to the demo (Convention 4); no AC above
is claimed by this stub. `test_gates.py` verify assertion flipped in the same change.
Consider a reduced demo scope: 1 criterion group, 2 probes, mock-first, live as a
stretch (**D12**).

### M8 — Stage 5 Adjudicate

**Purpose:** collapse findings into the E0–E6 ladder and a per-criterion verdict, then
one run-level verdict. **Code:** `backend/app/gates/adjudicate.py` — today
`{stage, ok, verdict: "PENDING"}`. **Target output:** run-level `verdict` **plus** a
`verdicts: [CriterionVerdict]` array conforming to `verdict.schema.json`, each with
`criterion_id`, `verdict`, `evidence_tier`, `locations[]`, `rationale`.

**Acceptance criteria (Session 25 — landed on `refactor`, R4 thin slice)**
- [x] Output satisfies `verdict.schema.json` per element — asserted with
      `jsonschema` in `test_adjudicate_verdicts_conform_to_the_verdict_contract`.
- [x] A criterion with no findings becomes `PENDING` "not examined" (rule 6);
      `verdicts: []` resolves to run-level `PENDING`, never fail-open (§1.8.3).
- [x] `locations[]` aggregates every location examined, not just the deciding one.
- [x] `rationale` is non-empty and criterion-specific (carries id, verdict, tier,
      and — for CONDITIONAL — the E4 remainder the ledger would record).
- [x] Run-level verdict per D3 (CERTIFIED iff all CERTIFIED; REJECTED on any
      refutation; else CONDITIONAL if any; else PENDING) — table-driven tests.
- [x] `test_gates.py` adjudicate assertion flipped in the same change; behaviour
      owned by new `backend/tests/test_adjudicate.py` (13 tests).
- **Tier interpretation committed (Session 25, recorded because §1.8.4's table is
  silent on the cell):** higher tiers measure confidence in a *satisfying*
  implementation — a `refuted` finding with a location is a located
  contradiction at **E2**, never higher on probe strength (demo-anchored:
  AC-2 REJECTED@E2). Unrecognised `result` values are fail-closed AND loud
  (§1.8.1: non-supporting, named in the rationale, tier capped E1).

**Size:** M. **Needs:** M7. **Note:** this is pure logic over M7's output — cheap to
test exhaustively, and the highest test-coverage value per hour in the project.

### M9 — Stage 6 Emit + gate

**Purpose:** emit the artefacts an auditor accepts and compute the merge signal:
traceability matrix, signed hash-chained record, review-debt ledger, risk-weighted
exposure, and `exit_code`. **Code:** `backend/app/gates/emit.py` — today
`{stage, ok, exit_code: 1, record: verdict}`. **Target output:** `exit_code` plus
`record` conforming to `run.schema.json`, and pointers to (or inline copies of) the
traceability matrix, ledger, and exposure.

**Acceptance criteria (Session 25 — thin slice landed on `refactor`; user-scoped
per the refactor plan, full brief below marked accordingly)**
- [x] `exit_code` is derived, not hard-coded: `0` only for run-level CERTIFIED, `1`
      otherwise. Fail-closed default kept for every undecided path.
- [x] Traceability matrix — criterion to location in both directions; link shape
      validated against `traceability.schema.json` (run_id attaches at persist, M10).
- [ ] Signed record / cross-file chain (**out of scope this build**): M14's
      `prev_digest` seam waits; contracts frozen (D-f) so D15's envelope is unwritten.
- [ ] Review-debt ledger (**out of scope this build**): no CONDITIONAL occurs in the
      demo; CONDITIONAL rationales already name the E4 remainder for the ledger to claim.
- [ ] Risk-weighted exposure (**out of scope this build**): harness dropped (D-a).
      Shipped instead: an honestly-unmeasured stub (`null` rate + `measured: false`,
      contract-conforming) — never a synthetic number.
- [x] `record` echoes the adjudicate output (`stage` + uppercase `verdict`) and extends
      it (D9 `status`, `measured`, `verdicts`, `traceability`, `exposure`). D16 kept
      open deliberately — both keys present, badge mismatch not papered over here.
- [x] `test_gates.py::test_emit_blocks_by_default` kept (still truthful) + extended by
      new `backend/tests/test_emit.py` (6 tests: derivation table, echo, both-direction
      traceability, unmeasured exposure, bare-dict tolerance).

**Size:** M. **Needs:** M8, M13, M14. **Note:** the signed record is a moat claim
("an evidence format an auditor accepts") — do not ship it unsigned and call it signed.

---

## 4. Services and infrastructure (M10–M15)

### M10 — Orchestrator (pipeline + queue)

**Purpose:** own run lifecycle — mint the id, execute the six stages, persist the
result, and (once wired) run off the request path. **Code:**
`backend/app/orchestrator/pipeline.py` (`enqueue_run`, `run_pipeline`) and
`jobs.py` (`submit`, `worker`), plus `orchestrator/persistence.py` (the M14-call
glue — conn lifecycle + transitions, zero SQL) and `main.py`'s lifespan (R1-held
this session). **Today (landed R1, `a7178d2`):** `enqueue_run` mints the id,
persists a `queued` row and submits the work item; `run_pipeline(payload,
run_id=None)` stays pure without an id and persists (`running` → `pending` /
`failed` + artifact) with one; `worker()` runs items via `to_thread` under the
read-only capability check and the lifespan starts/stops it cooperatively. The
§11.1 unwired-queue gap is closed — both characterization tests flipped
same-change.

**Target interface:** `enqueue_run(payload) -> str` persists a `queued` row and submits
to the queue; `run_pipeline(payload) -> dict` remains the synchronous path (tests and
the injected-payload demo depend on it); `worker()` is started once at app startup.

**Acceptance criteria**
- [x] **Wire the queue:** `enqueue_run` persists and submits; `worker()` starts from the
      app lifespan in `main.py` — landed R1 (`a7178d2`; Role 1 held M15's file this
      session per the refactor plan, `_dist` untouched). `GET /api/runs` has rows to
      list; serving them is R2's.
- [x] `run_pipeline` writes the `runs` row and calls `write_artifact` (**M14**) and flips
      the stored `status` — row creation is `enqueue_run`'s (AC1; M14's `save_run`
      raises on duplicates so `run_pipeline` cannot re-insert), transitions +
      artifact are `run_pipeline`'s. M14's zero-caller halves are closed.
- [x] A stage that raises must not lose the run: catch per stage, store the failure, and
      leave the run in a blocking state (rule 6). Blocking record
      `{run_id, stage, ok: False, exit_code: 1, error}` is defined inline (add-only
      if M9's `run.schema` ever governs it); detail lives in the artifact — the
      `runs` table has no `error` column by M14's design.
- [x] Flip `test_worker_is_async_but_never_started_by_app` **in the same change** (rule 7).
      Flipped to `test_worker_is_started_by_app_lifespan` (dynamic: `with
      TestClient` proves start + cooperative stop); `test_jobs_submit…` rewritten
      for the `(run_id, payload)` shape in the same commit.
- [x] The module-level `_queue` stays clean between tests — new
      `backend/tests/conftest.py` autouse fixture (module-attr redirect to `tmp_path`
      + sync drain before/after); the manual drains are retired. M17 owns adoption.
- **Tick convention used here** (Session 19 left this project-wide question open): tick
  the module's own deliverable and file downstream wiring as a request — hence AC1
  ticks with serving noted as R2's, while §M14 AC1 (written-by-M10 *and* read-by-M15)
  stays unticked with the write half annotated.

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
      — **half done, Session 21, and the two halves are deliberately not the same
      work.** The *switch* is built: `llm/__init__.py::select_client()` returns the right
      client and a guard proves nothing reaches one except the switch. The *degradation*
      is deliberately **absent** — a live outage falling back silently would emit a record
      indistinguishable from a real attestation, so degrading is the caller's explicit,
      recorded decision. Still open: no caller (§11.9), and the default is **live**, so
      an unconfigured environment raises rather than returning fixtures.
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
**Code:** `backend/app/attestor/policy.py` — `GRANTS` = read, subagent, skill, workflow
(harness groups) + `llm_egress` (an OS-level network property; `§1.6`, do not conflate
them); `DENIES` = edit, execute; `resolve_worker_caps()` parses the `ATTESTOR_CAPS`
declaration and fails closed; `assert_read_only()` fails closed on a leak or a gap;
`policy_record()` refuses to mint a record that advertises a control it does not have.
**Second file:** `backend/app/attestor/sandbox.py` — the observation layer.
`probe_workspace_readonly()` attempts the forbidden write and reports what the kernel
did, plus which of the two refusals it was, plus the mount's own `ST_RDONLY` answer.
`enforce_worker_read_only()` is the single worker-startup call.
**Today (post-merge, 2026-09-27):** the module is **complete and partly wired.** Both
layers exist and both fail closed. *This paragraph previously read "**unwired in the
product** … `app.attestor` has **zero product callers** — no gate, orchestrator or router
imports it", which was true until R1 (`a7178d2`, D-g) gave `worker()` its call site:*
`orchestrator/jobs.py:39` imports `assert_read_only` + `resolve_worker_caps` and vets them at
worker startup, so the *capability* half is live in the product path. What is still unwired is
the *workspace* half — `enforce_worker_read_only` has no caller, because no stage reads a
workspace yet (D4 open) — and the `attestor_policy` fragment, which M9 has yet to embed in the
emitted record. `assert_read_only` is a set comparison and proves nothing on its own; the
control is the refused write, which is why the second file exists at all.

**The emitted fragment, which is the auditor's whole view of this control** —
`to_dict()`, 10 keys, no key renamed or dropped in any session (rule 3):
`capabilities`, `granted`, `denied`, `enforcement_applied`, `workspace_readonly`,
`workspace_witness`, `workspace_path`, `workspace_mechanism`,
`workspace_mount_readonly`, `workspace_mount_witness`. The last four are Session 22's
and they are the ones that make the fragment evidence rather than reassurance: a
refused write is **two different findings** and the record says which.

**Acceptance criteria**
- [x] Both failure directions stay covered: a leaked deny **and** a missing grant each
      raise `PermissionError` (do not weaken to a warning). Pinned on the gated path
      **and** the ungated one — Session 22 closed a hole where the not-probed record
      path never consulted `DENIES` and would mint a record whose `capabilities` was
      `["edit"]` while its own `denied` said `["edit", "execute"]`.
- [x] The policy is visible in the emitted record, as a fragment M9 can embed verbatim.
      `to_dict()` is JSON-ready, frozen, clock-free and hashable. **The producer is
      still M9's** — see the open item below, so this box is ticked for the fragment
      and not for the pipeline.
- [x] **Never weakened for a demo shortcut** (rule 5, `AGENTS.md` Convention 5). No
      session has moved `DENIES`, and the two widening routes are pinned: a `network`
      grant is rejected as outside the vocabulary, and a *narrower* label is rejected
      too — `no_write_bit` must never be worded as a read-only anything.
- [x] `assert_read_only` is called on the real worker capability set at worker startup
      (**D6**). This is the difference between a claim and a control.
      — **CLOSED by R1 (`a7178d2`, D-g), verified on the merged tree:** `orchestrator/jobs.py`
        line 39 vets `assert_read_only(resolve_worker_caps(...))` at worker startup, before
        consuming. M12 built the primitive (`9c7343d`) and its 75 tests all pass; the call site
        is M10's file, which R1 held. *Merge note: the incoming #49 records this AC as still
        open and names `orchestrator/pipeline.py`; the wiring landed one module over, in
        `jobs.py`, also M10's — read from source, not taken from the commit message.*
      The one wiring still owed is the workspace half (`enforce_worker_read_only` on the
      first workspace-reading stage), which transfers to the first stage that reads code —
      D4 is open, so none does yet.
- [ ] The D6 **read-only bind mount** exists. The M12 follow-up made it *attestable* — the
      record now distinguishes a read-only mount from a missing write bit, and reports
      `ST_RDONLY` — but **nothing in the repo creates a read-only mount** (re-verified on the
      merged tree: the only mount call is the dashboard `StaticFiles`). Owner **M10**, which
      `sandbox.py` already names as the holder of the long-lived boundary. Note this module
      deliberately does **not** require one to start a worker, so the gate does not refuse
      everywhere a deployment cannot mount read-only.
      M12 follow-up: `75 tests` pass (63 before, +12 in the follow-up). `PolicyRecord` grew
      6 keys → 10 (`workspace_path`, `workspace_mechanism`, `workspace_mount_readonly`,
      `workspace_mount_witness`), none renamed or dropped (rule 3); both record paths now
      refuse a denied capability through one shared `_refuse_leaked`.

**Session 20 addendum (M12, `9c7343d`, branch `M12-attestor`; the M12 follow-up above is the
same module, relabelled `Session 22` by a parallel session per `AGENTS.md` Convention 18).**
`GRANTS` is now
`HARNESS_GROUPS | OS_PROPERTIES` and includes **`llm_egress`**: M7b workers call watsonx.ai
themselves, so a worker needs egress. Named for the capability *kind*, never a host, because
egress must cover both the auth and inference endpoints and the region is env config. A blanket
`network` grant is deliberately absent and pinned by a test. New `backend/app/attestor/sandbox.py`
proves the workspace is read-only by attempting the forbidden write — the part that was missing
entirely, and the reason withholding `edit` was previously theatre. Wiring, one line each, for the
owners: `enforce_worker_read_only(os.environ.get(ATTESTOR_CAPS_ENV), workspace)` at M7/M10 worker
startup (**landed by R1**), and `record["attestor_policy"] = policy.to_dict()` in M9 (**still
owed**). Stdlib only; no endpoint, contract, schema, or dependency changed.

**Two things this module deliberately does not do.**
- **It does not require a read-only mount to start a worker.** Both refusals start one;
  the record names which control answered. Requiring the mount would refuse to start
  wherever the deployment cannot mount read-only — this laptop, and CI — and that
  refusal says nothing about whether the control held. Session 22 considered requiring
  it (the strict reading of D6) and rejected it for that reason. Revisit only if M10
  can guarantee the mount.
- **It does not observe `llm_egress`.** The grant is declared because M7b workers call
  watsonx.ai themselves, and **no code exercises it yet** — there is no worker pool, and
  `MOCK_LLM` is read nowhere in `backend/app` (`architecture.md` §11.9). The allowlist
  that would pin egress to watsonx.ai is an OS-level control that does not exist; the
  token names the *kind* of egress and nothing more. Session 22 chose to record that
  in prose rather than add a per-run key, because a key saying "we never enforce this"
  is a thing an auditor can misread as enforcement.

**Size:** S — and now done except for the two wirings above, which are other modules'.
**Needs:** nothing. **Note:** this is the pitch's sharpest differentiator and a direct
IBM read-only-governance angle. Cheap to finish, expensive to lose. It is in Wave 0
because everything else waits on it, not because it is large.

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
`backend/app/db.py` (SQLite, WAL, one `runs` table + `idx_runs_created_at`;
`get_db` derives from `DATABASE_URL` unless given an explicit path;
`save_run`/`set_status` hold the commit; `get_run`/`list_runs` serve reads;
`now_iso` is the single clock), `store/artifacts.py` (`write_artifact` writes
`{**payload, sha256, prev_digest}` — payload-first so the store's keys win —
plus the `prev_digest` D8 seam and the shared `artifact_path_for`), and new
`store/records.py` (`read_artifact`, `project_run_payload`,
`read_run_record` — discharges §M3 obligation 1, first product caller of the
mirrors). **Today:** the seams exist and are guarded (40 tests); **no product
caller yet** — M10/M15 wire them.

**Acceptance criteria**
- [ ] `runs` rows are written by M10 and read by M15. `artifact_path` points at the JSON. **M14's half is done** (`save_run`/`set_status`/`get_run`/`list_runs` + the artifact path); the callers are pending. **Write half landed R1 (`a7178d2`)** — M10 persists rows + artifacts through `orchestrator/persistence.py`; read half (`get_run`/`list_runs` from routers) is R2's, checkbox stays open until then.
- [x] `created_at` is an ISO-8601 **string** (`now_iso`, UTC tz-aware; type pinned by `test_save_run_created_at_is_iso8601_string` — landed once, here, not in M17).
- [x] The artifact `sha256` continues to cover the sorted body exactly as today (`test_store_db.py` pins it, plus the store-keys-win negative). `prev_digest` rides alongside as a PROPOSED, UNCONTRACTED D8 seam (D15) with a self-invalidating guard. Cross-file chaining stays M9's.
- [x] `ARTIFACT_DIR` and `DATABASE_URL` are env-driven (`DATABASE_URL` now has a reader — `_sqlite_path` strips `sqlite:///`; `config.py` untouched); tests keep using `tmp_path` so the repo tree stays clean (`docs/test-suite.md` Convention 3). **Known limitation, accepted:** both defaults are CWD-relative (recorded in `docs/architecture.md` §6).

**Size:** S. **Needs:** M1. **Note:** a `/tmp/opencode/mutation_lab.py` harness exists
from an earlier session — it injects deliberate bugs into a scratch copy of the repo and
reports whether the suite catches them. Useful for M17; it is **not** repo code.

### M15 — API surface

**Purpose:** the four endpoints plus static hosting — the whole external contract.
**Code:** `backend/app/routers/webhooks.py` (live), `runs.py` (real since R2), `metrics.py`
(stub, deliberately — D-a), `backend/app/main.py`. **Today:** `POST /webhooks/github` accepts
any JSON (real delivery or hand-injected demo body on the same path) and — since R1 — persists
a queued row and submits it; `GET /api/runs` lists index rows newest-first, `/api/runs/{id}`
serves row + artifact and 404s an unknown id; `/api/metrics` returns the honest unmeasured stub.
**Defect closed (R2):** the `_dist` climb is two levels, and `mount_dashboard()` is extracted
so a test proves the mount appears when a `dist` exists.

**Acceptance criteria** (Session 25: R2 `ab2849c`)
- [x] `GET /api/runs` lists real rows (newest first) from M14; `GET /api/runs/{id}`
      returns the run envelope plus artifact pointers, and a `404` for an unknown id
      (**it used to echo any id with `status: "pending"`** — that was a stub, not a
      lookup). *Superseded detail:* the detail route reads the artifact defensively
      (`.get` defaults) rather than through the strict `RunRecord`, because M9's record is
      a contract *superset* (D15) and an M8-only record carries no `status` — a strict read
      would 500 on real output. `read_run_record` stays the enforcing reader; revisit when
      the envelope is contracted.
- [ ] `GET /api/metrics` aggregates M13's function over stored mutation results and keeps
      the exposure contract's three keys exactly (a test pins the key set). **Deferred by
      decision (D-a):** the mutation harness is out, so there is nothing to aggregate; the
      three-key honest stub is a *surface*, not a gap.
- [x] **Fix the `_dist` path** (two levels, not three) and prove it: a test that the
      mount appears when a `dist` directory exists is the honest fix, not a comment.
- [ ] Webhook: verify the GitHub signature when a secret is configured (**D7**), keep the
      injected-payload path working with no secret (demo survival), and submit the run
      to the queue (needs M10 + the `main.py` lifespan change). *Two thirds done:* the
      submit + lifespan half landed with R1 (`a7178d2`); D7 HMAC remains open and
      out of scope for this build.
- [ ] GitHub write-back (PR comment + check run) is a **stretch** (**D13**), not a P0 —
      the non-zero exit is the merge-blocking claim and it already works.
- [x] Flip the stub-response tests in `test_api.py` in the same change (rule 7);
      the route-table test keeps passing (no routes added or removed without
      updating it). Two flipped, four added, `test_api.py` 8 → 13.

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

**Requests filed by M2 (2026-09-27)** — M2 owns the data, M16 owns the dashboard, so these
sat outside M2's write scope:
1. Delete `frontend/src/fixtures.js` and have `App.jsx` fetch the corrected
   `/fixtures/demo_run.json` from `public/`, so the demo data is genuinely single-copy.
   `test_public_demo_run_is_byte_identical_to_canonical_fixture` now guards the two JSON
   copies against each other; it cannot guard a third copy written in JS.
2. Feed `fixtures/demo_exposure.json` to `ExposureCard` so the mutation number is displayed.
   `App.jsx` seeds `metrics` as `{false_certified_rate: null, measured: false}` and only
   `fetchMetrics()` can change it, and `GET /api/metrics` still returns a hard-coded stub
   (`architecture.md` §11.2) — so nothing on screen shows 0.25 today.
3. **Defect, verified, not fixed — M16's files.** `App.jsx:23` passes `run.status` into
   `<VerdictBadge>`, but `VerdictBadge.jsx:2` compares it against the uppercase verdict enum
   (`'CERTIFIED'` / `'REJECTED'`). A D9-conformant lowercase status matches neither branch
   and renders **orange** — the same colour as `PENDING` — so the demo's rejected run looks
   undecided. Normalise case in the component, or give the badge its own status mapping.
   `EvidenceLadder` and `TraceabilityMatrix` read `run.verdicts` and are unaffected.

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
failed live call. **Code:** `backend/.env.example`; `scripts/attest.py` (landed, Session 25);
the runbook lives in this section — **still to be appended**, and it is not a runbook until a
foreign pair of hands has run it.

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

**Acceptance criteria** (Session 25: `ab2849c`)
- [ ] The runbook is executed **by someone who did not write it**, start to finish, and
      the failure is fixed. An unrun runbook is not a runbook. **Not yet:** the CLI half is
      built and smoke-proven end to end, but the written runbook (steps 1–6 below, plus
      the Bob invocation) has not been appended or walked by anyone else.
- [x] The demo survives a dead watsonx.ai: with `MOCK_LLM=true` or pre-computed
      artifacts, the full verdict-to-exposure path still renders (rule 4). *Partly this
      session:* the whole chain runs with no LLM call at all (M7 is a mock stub carrying
      its provenance in-band), and `attest.py --direct` needs no server and no network.
      The dashboard half still depends on M16 (never built).
- [ ] Fallback video recorded (Convention 6); final 4 hours are rehearsal only.
- [x] `.env.example` documents every variable M11/M14 read, with safe defaults. Verified
      against source, not from memory: `WATSONX_API_KEY`, `WATSONX_PROJECT_ID`,
      `WATSONX_URL`, `DATABASE_URL`, `MOCK_LLM`, `ARTIFACT_DIR` — all six present.

**Shipped this session — `scripts/attest.py` (M18), stdlib-only so Bob can run it with any
interpreter.** HTTP mode (default): POST `fixtures/demo_payload.json` to `/webhooks/github`,
poll `GET /api/runs/{id}` until the status leaves `{queued, running}`, print the verdict and
traceability, exit derived from `status` (0 iff `certified`). `--direct`: run the pipeline
in-process, exit with the record's `exit_code`. Fail-closed everywhere — no run id, refused
connection, unparseable payload, or a run that never terminates all exit 1.
**Deviation from the plan, recorded:** the plan says "exit with the run's `exit_code`", but
no served field and no contract carries it (§1.7's response has `status` only, and
`run.schema.json` requires `run_id, status, verdicts, measured`). Contracts are frozen (D-f),
so the CLI **derives** the exit from `status` instead of adding a key — §1.5 makes the two
equivalent, and the derivation can only ever be too strict, never too lax.

**Size:** S. **Needs:** M11, M15.

### Bob IDE integration (Session 26, 2026-09-27) — the gate as an MCP tool

Deliberately **not** "point Bob at `attest.py`". That route needs Bob to run a shell command, and
granting a shell to verify a diff is the capability §3.3 withholds. The finding that changed the
design: **Bob's `mcp` tool group is separate from its shell group**, so a custom mode can reach an
MCP server and still have no terminal. The read-only claim is then something the *client enforces*,
not something our process asserts about itself.

**Shipped:** `scripts/mcp_attest_server.py` (MCP stdio server, stdlib only — rule 9),
`.bob/custom_modes.yaml` (the `attestor` mode: `groups: [read, mcp]`, `allowedSubagents: []`),
`.bob/mcp.json` (stdio registration, `alwaysAllow` on both tools), and
`backend/tests/test_mcp_attest_server.py` (36 guards).

**Runbook — the Bob path, from a clean checkout.** Rehearsed end to end on 2026-09-27 against
`bobshell@2.0.5`; the transcript below is measured, not aspirational.

0. **Do not put a credential in `.bob/`.** Export `BOB_API_KEY` in the shell. `test_bob_directory_contains_no_secret`
   fails the suite if a key-shaped string ever lands in a committed config, because `.bob/` is
   version-controlled and MCP's config has an `env` key whose whole purpose is carrying a secret.
1. **Put Bob on the PATH.** `npm i -g bobshell` installs to `~/.npm-global/bin`, which is not on
   PATH by default. `export PATH="$HOME/.npm-global/bin:$PATH"`.
2. **Authenticate.** First `bob run` opens a browser to `bob.ibm.com/login`. Export the key, or sign in
   once interactively — it lands in `~/.bob/settings/auth-secrets.json` and is then picked up
   automatically. **Spend discipline (Convention 7): always pass `--max-cost` and `--max-turns`.**
   The hackathon grant is $40; a bare `bob run` has no ceiling.
3. **Accept the licence, once:** `bob run --accept-license ...` (it persists `licenseConsent: true`).
   Note the standalone forms `bob --accept-license` and `bob --list-tasks` are **broken in 2.0.5** —
   they fail with `Invalid --prompt: Too small` before dispatch, so use the subcommand form.
4. **Trust the folder, once, from the repo root:** `bob run --trust ...`. Without it Bob stops on an
   interactive "Do you trust this folder?" prompt, which a headless run cannot answer.
5. **Check the wiring is seen — free, no model call:** `bob mcp list` →
   `attest-gate: python3 scripts/mcp_attest_server.py | enabled | stdio | workspace`.
6. **The demo moment:**
   ```
   bob run --trust --max-turns 3 --max-cost 0.40 --mode attestor -f json \
     "Call attest_run with payload_path fixtures/demo_payload.json, then report the status and exit_code it returned."
   ```
   **Measured result:** `status: rejected`, `exit_code: 1`, `AC-1 CERTIFIED [E4] src/refund.py:64`,
   `AC-2 REJECTED [E2] src/refund.py:88`, 2 traceability links, exposure reported unmeasured.
   `session_costs` 0.153 of a 0.40 cap, `tool_calls: 1`, ~19 s. Bob's own summary repeated the
   unmeasured marker verbatim — the mode's instruction and the tool's output agreed, which is the
   point of shipping both.
7. **Fallback if the mode file is rejected** (a `custom_modes.yaml` key Bob does not like):
   `bob run --disable-tool-groups edit,execute "…"` — still no shell, and needs no mode file at all.

**Why there is no `cwd` in `.bob/mcp.json`.** The `attest_run` tool calls `run_pipeline(payload)`
with no `run_id`, which is the documented pure path: the six stages run and **nothing is persisted** —
no row, no artifact, no chain. The read-only posture therefore holds at the storage layer as well as
the capability layer, and holds from any working directory (proven by launching from `/`). Since
relative-path semantics for `cwd` are undocumented, pinning one would trade a real guarantee for
undefined behaviour. `test_mcp_config_pins_no_working_directory` is where a future change to the
server's write behaviour has to be revisited.

**Tool-group vocabulary — read from the shipped bundle, not the docs.** `bobshell@2.0.5`
(commit `2dc180906`) builtin mode definitions use `read` `edit` `execute` `browser` `mcp` `skill`
`todo` `artifact` `subtask` `subagent` `mode`. **Bob's Bob Shell custom-modes documentation page is
wrong**: it advertises a `command` group that does not exist in the binary, and omits four real
ones. The mode file cites the bundle as its provenance and a guard asserts the citation is still
there, so a reader of the YAML can see why those names were chosen. The docs also document
`--chat-mode`; the binary has no such flag (0 occurrences) — it is `--mode <slug>`, default `agent`.

**Verified against the real client (the Phase C gap, now closed for Bob Shell):** `bob mcp list`
discovers the server from the committed config; `bob run --mode attestor` loads the mode, connects
the MCP server, calls `attest_run`, and returns the §1.7 verdict. **Not verified:** Bob **IDE** — the
desktop app is not installed, so the IDE-specific surfaces (its own `~/.bob/settings/` global paths
and its mode picker) are unexercised. Project-level `.bob/` is the same path for both clients, so
the artifacts are shared; only the *global* paths differ.

**Still open, and it is the same AC as before:** the runbook has now been walked by a second party,
but the actor was the session that built the tool, so M18's "executed by someone who did not write
it" criterion is **still unticked**. A teammate running steps 1–7 cold is what closes it.

---

## 6. Decisions that gate modules

Nothing below is settled. Each item names the modules blocked, so nobody stalls silently
— if you are blocked and cannot reach the owner, take the recommended default and
record that you did.

| ID | Decision | Blocks | Recommended default |
|---|---|---|---|
| **D1** | E0–E6 tier semantics — undefined in the source (1.4) | ~~M7, M8, M9, M16~~ **all unblocked** | **RATIFIED 2026-09-27 (Session 21):** the 1.4 table as written, `CERTIFIED` requires E4. The ladder is *our* proposal — the source names it and never defines it — so that provenance must travel with every artefact that shows a tier. Three consequences in 1.4: the tier is **derived by M8, not carried on a finding** (so `findings.schema.json` keeps no `evidence_tier`, and M1's deferred `CERTIFIED ⇒ E4` constraint is now unblocked); M7a cannot exceed E4 (§1.8.4); watsonx.ai `guided_json` can now be pointed at a schema whose tiers mean something. See `docs/watsonx-integration.md` §4 |
| **D2** | The 7th adversarial failure class — source names six (1.6) | M7 | Ship six; say "six" in the pitch |
| **D3** | Verdict aggregation + whether CONDITIONAL may pass the gate (1.5) | M8, M9 | REJECTED blocks; CONDITIONAL needs a ledger entry |
| **D4** | Demo repo target — needs real acceptance criteria to attest against | M4, M5, M13 | Smallest repo with genuine written criteria; inject payloads until chosen |
| **D5** | Stryker corroboration of mutation ground truth | M13 | Stretch — harness first, corroboration if time |
| **D6** | Where read-only is enforced: worker startup vs pipeline wrapper | M7, M10, M12 | Assert at worker startup, fail closed. **Mechanism now specified (2026-09-27):** read-only bind mount of the workspace + a pre-flight capability check, modelled on watsonx Orchestrate's tool sandbox, which runs Python tools in a read-only filesystem. `ToolPermission.READ_ONLY` is deprecated and is *not* a live control — do not cite it. See `docs/watsonx-integration.md` §6. **Session 20 (M12) accepted the recommended default and built the pre-flight:** `enforce_worker_read_only(declared, workspace)` resolves the worker's own `ATTESTOR_CAPS` declaration and probes the mount, failing closed on both. The call site remains M7/M10's, so D6 is *answered, not closed* |
| **D7** | Webhook signature verification, and behaviour with no secret configured | M15 | Verify when a secret exists; allow injection when not |
| **D8** | Cross-file hash chain format | M9, M14 | Each artifact carries the previous digest |
| **D9** | `status` lifecycle values (1.2) | M9, M10, M15 | The PROPOSED set in 1.2 |
| **D10** | Migrate off deprecated `jsonschema.RefResolver` | M1, M17 | No — not during the build |
| **D11** | Per-run token/cost ceiling | M7, M11 | Hard cap per criterion group; report spend per run. **Data source now known:** every watsonx.ai response carries `usage.{prompt_tokens, completion_tokens, total_tokens}`, so only the policy is open. See `docs/watsonx-integration.md` §5 |
| **D12** | M7 demo scope if the clock slips | M7, M18 | 1 criterion group, 2 probes, mock-first |
| **D13** | GitHub write-back (comment + check run) | M15 | Stretch — after the API serves real data |
| **D14** | `--disable-subagents` vs the granted `subagent` cap — which launch posture the workers take | M7 | **OPEN. Keep GRANTS as-is.** The tension is real on both sides: Bob Shell subagents are "model-invoked and non-deterministic" (`ibm-bob.txt`, Stage 4), which motivates a `--disable-subagents` launch — but option (b) fan-out *is* subagents (each M7b worker calls watsonx.ai itself; `policy.py` documents why `subagent` is granted), so disabling it removes the mechanism the architecture prescribes. Determinism should come from deterministic probes, not from removing the capability the fan-out depends on. (Known wording tension kept-as-is since Session 7; `architecture.md` §8.) |
| **D15** | The emitted artefact envelope, review-debt ledger, ingest bundle, and `ast` have no contract. This blocks M9 (emitter), M14 (artifact store), and the receipt renderer's consumer wiring. The `criteria[]` and `findings[]` array wrappers are also uncontracted (the item schemas exist; the array envelopes do not). | M9, M14, M1 (next pass) | **OPEN — and now specified (Session 21).** M1 owns `contracts/` alone, so this is a formal request, not something M9 may invent. What M9 needs, in the order it needs it: (1) an **artefact envelope** — `run_id`, `status`, `measured`, `verdicts[]`, plus `traceability`, `ledger`, `exposure`, `attestor_policy`, `signed`, `exit_code`; (2) a **review-debt ledger** — one entry per `CONDITIONAL` criterion (D3 makes an unrecorded conditional a contract violation, so the shape is load-bearing, not cosmetic); (3) the **ingest bundle** — `requirement` + `files[]` where each entry must distinguish *measured* from *unreached and why* (never a silent empty string); (4) the **`ast`** entry shape. Two hard constraints on the answer: **M3's models are `extra="forbid"`**, so M9's record cannot be loaded into `RunRecord` unprojected — `schemas.py` says so at lines 17–24 — and `write_artifact` prepends `sha256`, so the reverse projection is needed too. Recommended default stands (**hold; do not invent a shape without a real emitter to validate against**) — but the emitter now exists in draft, so the request is answerable rather than hypothetical |
| **D16** | **Two verdict vocabularies in two keys, and the dashboard renders the wrong one.** M8's run-level `verdict` is **uppercase** (`REJECTED` — it is the `verdict` enum). `run.schema.json` carries **no aggregate verdict field at all**; the only run-level key is `status`, which D9 makes **lowercase** (`rejected`). `App.jsx:23` passes `run.status` into `<VerdictBadge>`, and `VerdictBadge.jsx:2` compares it against the **uppercase** enum — so a D9-conformant `"rejected"` matches neither branch and renders **orange**, the `PENDING` colour. A perfectly correct M9 record would make the demo's rejected run look undecided. | M8, M9, M15, M16, and M1 (a contract) | **OPEN. Do not paper over it in one module.** Three owners, one question: does `run` gain an aggregate `verdict` field (uppercase enum, alongside `status` as the lifecycle), or does `status` change case, or does `VerdictBadge` grow its own mapping? M1 owns the contract, M15 owns the router, M16 owns the component. Recommend the first — a lifecycle (`queued`→`running`→`rejected`) and a verdict (`REJECTED`) are different concepts and forcing one key to carry both is what produced the orange badge. **Until it is decided, M8 must emit `verdict` and must not assume anything about `status`**, and any artefact showing a tier or verdict must label the vocabulary's provenance per §1.4 |


| **D17** | What spawns the N Stage-4 OS processes, now that `bob run` is gone | M7 | **OPEN. Stdlib only (rule 9).** The source prescribes "N independent `bob run` processes ourselves" (`ibm-bob.txt`, Stage 4) — and Sessions 8–10 removed `bob run` from the architecture entirely (no Bob custom-mode syntax, no harness runs), so the spawner is unspecified. Recommended: `asyncio` subprocesses owned by M7b itself; M10's pool stays 1 (D-f) and is not the fan-out. |
| **D18** | M10 worker contract — the shape R2/M17/M18 build against | M15, M17, M18 | **ANSWERED by R1 (`a7178d2`, this lane).** Work item `{"run_id", "payload"}`; `submit(run_id, payload)`; pool of one; items run via `asyncio.to_thread`; launch-site `ATTESTOR_CAPS` default = the five GRANTS tokens, vetted by `resolve_worker_caps` + `assert_read_only` at worker startup (D-g; `policy.py` untouched); cooperative shutdown = stop event + `None` sentinel (lifespan cancels nothing). Pure path `run_pipeline(payload)` persists nothing — M18's `--direct` depends on it. |
| **D19** | What a "criterion group" is — the unit M7 fans out over | M7, M8 | **OPEN. Recommended: one group per criterion (`criterion_id`).** The source says "one per criterion group" (`ibm-bob.txt`, Stage 4) and never defines the grouping; per-criterion matches M6's criterion-anchored `ast[]` and R4's per-criterion findings. M7 decides; M8 aggregates whatever M7 groups. |
> **D16** was reserved here for Role 2's verdict-vocabulary question and has since been **filled by the M4-ingest merge** (the VerdictBadge row above) — no collision; numbering reads D13–D19 contiguously.

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

### 2026-09-27 — Session 17: prioritization briefing (`/start` only, no code change)
- Instruction: *"from our software architecture, what modules are needed to be prioritized."*
  `/start` protocol only. Target module, session state, completed/remaining work and
  conventions were displayed, and the user chose no follow-on before `/end`. **No decision
  taken, no file written by this session, no code changed.**
- **The prioritization was read from §0.5 rather than re-derived.** §0.5 already fixes the
  critical path (`M1→M2→M4→M5→M6→M7→M8→M9→M10→M15→demo`) and the five waves. A second
  ordering would compete with the one this file owns, which is precisely the drift §0.5
  exists to prevent. The standing answer is unchanged: **Wave 0 = M1 + M11 + M12, start
  now**; everything off the critical path floats.
- **Rule 4 in §0.3 is the line that needs fixing, not `AGENTS.md` Convention 4.** Session 16
  recorded that AGENTS.md Convention 4 "assumes a switch that does not exist"; checked
  against the file, that is false — Convention 4 is about the *frontend* fixture fallback,
  which works, and makes no claim about the backend LLM switch. Rule 4 is the one that says
  "`MOCK_LLM=true` **and** the frontend fixture fallback must keep working", so it is the
  one carrying the false half. The `MOCK_LLM` half is a **requirement, not a description** —
  M11 still has to build the switch — so rule 4 stands as a target and should be marked that
  way rather than deleted. The underlying gap is real: `architecture.md` §11.9, owner M11.
- **API endpoints:** none. **Dependencies:** none. **Contracts/fixtures/code:** unchanged.
- **Open at archive:** the user was offered (a) ratify D1–D13, (b) assign the 18 modules to
  the 5 people, (c) start Wave 0 (M1, M11, M12), (d) something else — and took none. D1 still
  blocks M7/M8/M9/M16, and M11 remains the schedule risk. 0 of 18 modules implemented.

### 2026-09-27 — Session 18: M3 pydantic mirrors implemented (first module shipped)
- Instruction: *"develop the pydantic mirrors (M3)"*, via the `/start` protocol. **This is
  the first of the 18 modules actually implemented** — the standing headline moves from
  0 of 18 to 1 of 18.
- **Shipped:** `backend/app/models/schemas.py` went from 2 models to **6** — added
  `Criterion`, `TraceabilityLink`, `TraceabilityMatrix`, `Exposure` behind a new
  `ContractModel` base with `extra="forbid"`. Parity with all five contracts is now
  **5/5** and asserted mechanically. New guard: `backend/tests/test_models_parity.py`.
  **100 tests green** (79 baseline + 21 new) on **Python 3.11.9 and 3.12.14**; validator
  OK ×2 on both legs.
- **A false claim in the file's own docstring is now fixed.** Line 1 read *"per-criterion
  verdict, traceability, exposure, run envelope"* — traceability and exposure models **did
  not exist**. Found by reading the source, not the docstring. It happens to be true now.
- **`extra="forbid"` was chosen deliberately, over a recommendation of `ignore`.** The
  user's position was that strictness matches the gate's fail-closed posture; the counter
  was that `forbid` fails *loudly* (downtime) where `ignore` fails *silently* (corruption).
  Resolved as **two tiers, not one setting**: contracts stay permissive, models are strict.
  The user's principle was right; only the position needed narrowing. It is pinned by a
  test so it cannot drift back.
- **The parity test caught its own exception on its first run**, unplanned: `TraceabilityLink`
  is a model with no contract, because the traceability contract declares that object
  *inline* (no `title` to join on). M3 cannot add a schema file — `contracts/` is M1's
  alone (§0.4). Resolved with an explicit, **self-invalidating** `INLINE_MIRRORS` entry:
  the shape is still checked against the inline object, and if M1 ever gives it a `title`
  the test fails until the exception is deleted. **Request for M1: promote it to
  `traceability-link.schema.json`** so parity is a clean bijection.
- **A guard was proven not to fire, and the claim it backed was overstated.** The first
  draft of `test_exposure_accepts_metric_function_output` asserted only that values
  round-tripped, so de-typing `by_operator` to a bare `dict` (the contract's own
  `{"type": "object"}`) still passed — the *type* was never pinned, although the model
  docstring claimed it was. Fixed by asserting a malformed count is rejected. Caught by a
  5-mutation guard harness (`/tmp/opencode/m3_guard_proof.py`, self-reverting, outside the
  repo): **all 5 mutations now fire**, and the suite is green after restore. Same rule as
  Session 16 — a guard never seen failing is not a guard.
- **Deviation from the brief, recorded rather than silently taken:** AC 1 named
  `test_schemas_contracts.py` for the parity assertion, but `backend/tests/` is M17's path
  (§0.2) and that file is not in the §0.4 contended list. A new M3-exclusive test file
  avoided a two-owner collision, and it deliberately does **not** duplicate the enum,
  fixture-load or round-trip tests already living in `test_schemas_contracts.py`.
- **API endpoints:** none defined, changed or removed. **Dependencies added:** none — reused
  the 7 `backend/requirements.txt` pins (rule 9). **Contracts/fixtures changed:** none, so
  the validator result is a non-regression check rather than a new assertion.
- **New conventions/patterns:**
  1. **A mirror is strictly stricter than its contract, and that is stated as a two-tier
     design** — contracts are the permissive interchange layer, models are the strict
     in-process trust layer. Without the framing it reads as a bug.
  2. **An exception must be self-invalidating.** A hand-maintained allowlist rots; pairing
     it with an assertion that *fails when the exception is no longer needed* is what makes
     it safe to have one at all.
  3. **When a strict model makes a not-yet-written path raise, write the obligation down
     instead of loosening the model.** Two such paths are recorded (the `sha256` artifact
     envelope; M9's superset record). A documented landmine M9 meets deliberately beats a
     silent key drop.
  4. **A test that pins a value is not a test that pins a type.** The `by_operator` miss is
     the generalisable lesson: round-trip equality survives a de-typing, so type claims
     need their own negative assertion.
  5. **First module shipped; 17 remain.** Wave 0 (M1, M11, M12) is still unbuilt, and
     **Wave 0 gates Wave 1** — M4 needs M2 + M11, M5 needs M4. M3 was cheap and is done;
     it does not unblock the critical path.
- **Open at archive:** D1–D13 still unsettled (D1 still blocks M7/M8/M9/M16); the models
  have **zero product callers** (`architecture.md` §11.10) until M4–M9/M13/M15 consume
  them; M1 has two open requests from this session (promote the traceability-link schema,
  and the `findings.schema.json` its own AC 2 calls for); `criterion` and `exposure` still
  have no fixture pair, so they are tested with constructed values rather than corpus data.
### Session 18 (M1 contracts, orphan closure + findings): 2026-09-27

- **`/start` protocol run.** Target: M1 "Contracts + validator". Scope chosen with the
  instructions: close the two orphan schemas (`criterion`, `exposure`), add
  `findings.schema.json` for M7, and make "no orphan schemas" a check that fails.
  Hardening pass deliberately skipped (see deferred list in §M1). D1 not ratified — no
  tier constraint added.
- **Branch base:** `m1-contracts` created from `origin/main` @ `bd1df28`.
- **Baseline:** 79 tests on `origin/main`. The 37 receipt-renderer tests are on
  `receipt-renderer` (PR #26 open, unmerged). 79 is correct; the absence of the 37 is
  not a defect.
- **Files written:** `contracts/findings.schema.json` (new), `contracts/examples/`
  (new directory), `contracts/examples/criterion.json`, `contracts/examples/exposure.json`,
  `contracts/examples/findings.json`. **Files edited:** `scripts/validate_contracts.py`,
  `backend/tests/test_schemas_contracts.py`, `docs/modules.md`, `docs/architecture.md`,
  `docs/test-suite.md`.
- **Declared changes to existing lines (Convention 10):**
  1. `_validate_pair` in `test_schemas_contracts.py`: `(FIXTURES / fixture_name)` →
     `(ROOT / fixture_name)`; the `FIXTURES` constant was removed (now unused). Both
     existing call sites kept their string arguments unchanged; two new call sites use
     repo-relative paths.
  2. `test_validator_script_exits_zero_as_ci_runs_it`: the two `"OK demo_run.json"` /
     `"OK demo_traceability.json"` stdout assertions updated to the repo-relative forms
     `"OK fixtures/demo_run.json"` / `"OK fixtures/demo_traceability.json"`, matching
     the updated validator output.
- **Two unanswered questions resolved by default (not escalated):**
  1. Should examples live in `contracts/examples/` or `fixtures/`? Default taken:
     `contracts/examples/` (M1 owns `contracts/`; `fixtures/` is M2's exclusive path per
     §0.4). M2's paths are untouched.
  2. Should `exposure.json` show a measured state or the pre-measurement state? Default
     taken: pre-measurement (`measured: false`, `null` rate, empty `by_operator`) —
     Convention 8 / §1.7 say "unmeasured must look unmeasured".
- **Verdict orphan found and closed:** `verdict.schema.json` was already on disk with no
  direct PAIRS entry (previously "validated" only via `run`'s `$ref` resolution, not by
  a standalone example). The coverage check in `main()` caught it. A 6th PAIRS entry and
  `contracts/examples/verdict.json` were added. The §1.1 catalogue already noted "via the
  `run` `$ref`" — that indirect validation is now supplemented by a direct example.
- **Delivery:** two branches, deliberately. `m1-contracts` carries bobIDE's commit
  `b0c224c` **plus** the review pass committed on top, and is the **only** branch that
  gets a PR into `main`. `bob-sessions` points at `b0c224c` alone — the pristine agent
  output before any human correction — and is pushed as an **archive ref, deliberately
  not PR'd**: a PR from it would carry the same five contract files as `m1-contracts`
  and the second one to merge would be empty or conflict. Keeping it unmerged is what
  makes the review pass auditable as a *correction* of an agent's output rather than
  as the only version that ever existed. `bob-sessions/` at the repo root holds the
  tool's own session summary, two screenshots, 243 KB total:
  `Screenshot_20260927_065255.png` (branch/baseline, new files, what each is for) and
  `Screenshot_20260927_065340.png` (key code changes, the 10 new tests, and the
  `verdict.schema.json` orphan discovery). **Every claim in both was checked against
  the code and holds** — which is why they are worth keeping. They document `b0c224c`,
  *not* the review pass on top; that gap is the point of the archive. PR number to be
  recorded here once opened. **Neither branch pushed at the time of writing** — record
  the real state here, don't let this line drift.
- **What was deliberately not done:** no `$id`, no `criterion_id` pattern, no
  `measured:false ⇒ null` constraint, no `by_operator` shape, no `CERTIFIED ⇒ E4`
  constraint (all D1 or hardening-pass), no `additionalProperties: false` (AC4). D1 was
  not ratified. The `FIXTURES` constant in the validator was removed (now unused) — stated
  in the commit.
- **Review pass, same session — ten corrections, no behaviour change to product code.** A
  read-back of the session's own output against the code found statements the change had
  invalidated and left in place. Corrected: `modules.md` M1 header ("5 files", "2 of 5
  pairs"), `modules.md` §1.1's `verdict` row (still "via the `run` `$ref`" only), the
  unticked draft-07 criterion, `architecture.md` §10 and its Session 18 log (both said 5
  pairs where `PAIRS` has 6 — the as-built authority was contradicting its own log),
  `test-suite.md`'s coverage map (5 pairs), `intent-attestation-gate.md`'s layout line
  (5 schemas, no examples), and the module docstrings of `validate_contracts.py` and
  `test_schemas_contracts.py`, which still described a fixtures-only world.
- **One code defect came out of the same pass:** the coverage line printed
  `len(PAIRS)/len(PAIRS)` rather than the schemas on disk, so a duplicate pair entry would
  have let the gate claim coverage it did not have. Now counted from disk, with
  `test_validator_script_exits_zero_as_ci_runs_it` pinning the reported number against the
  on-disk schema count. The gate that exists to make an unmeasured thing look unmeasured
  was itself reporting a number it had not measured.
- **Owed, not done: Figure 6 is now stale and no one can regenerate it.** The Contracts (M1)
  box still reads "5 JSON Schemas" / "validator covers 2 of 5 pairs" and the Exposure (M9)
  box still reads "exposure schema has no PAIRS entry" — all three now false. The generator
  `gen_fig6_architecture.py` is not committed on any branch, so the figure is unregeneratable
  and must not be hand-edited. Recorded as `docs/architecture.md` §11 gap 11. **Any module
  that changes a number the figure prints owes the same audit** — the figure asserts ~38 box
  lines against the code, and a count that moves in code but not in the PNG is a lie with a
  legend.
- **Correction to this log's own framing, same day:** the instruction this session worked
  from specified **5 pairs for 6 schemas**, leaving `verdict.schema.json` still an orphan
  under the rule it was creating. The coverage check caught it — which is the check
  working, not a near-miss. Recorded here because the mistake was in the specification, and
  the log should not read as though the first pass got it right.

### 2026-09-27 — Session 21: M3 reopened and re-closed — the `Finding` mirror

Instruction: *"analyze the code base, make sure that it pass the tests"*, extended to verify
the suite across Python versions rather than the pinned one. This session **implemented**
M3's outstanding half, so per rule 10 the log lands here as well as in
`docs/architecture.md` / `docs/test-suite.md`; the **verification-only** findings were
kept out of this file, per Session 19's precedent.

- **The gap this closed:** M1 shipped `contracts/findings.schema.json` (title `Finding`)
  on 2026-09-27 with no mirror, which made `test_contract_model_parity_is_a_bijection`
  and both coverage tests fail — **112 tests, 109 passing, tree red.** The parity test's
  own docstring names the remedy (*"do not suppress it, mirror the schema"*), and
  `modules.md` §0.4 makes `backend/app/models/schemas.py` **M3-exclusive**, so this was
  M3's file to fix rather than a merge side-effect. Added `Probe` (5-value `Literal`) and
  `Finding`. Parity **5/5 → 6/6**; mirrors **six → seven**; suite **112 → 118**.
- **The three properties of `Finding` that are decisions, not defaults** — each written
  into the model docstring and pinned by a test, because each one is a place where a
  later session could "helpfully" diverge from the contract:
  - **No `evidence_tier`**, because **D1 is unratified** and the contract's own
    `description` forbids adding it. This is the sharpest case in the module: a
    *helpful* addition would have encoded a ladder nobody has agreed, and nothing in the
    suite would have complained. `test_finding_does_not_encode_d1_tier_semantics` now
    makes the omission loud.
  - **`result` stays unenumerated** — its vocabulary is **M7's** to define, not M1's or
    M3's.
  - **No defaults** on any of the five required keys, matching `Criterion`'s asymmetry
    rather than `CriterionVerdict`'s: a probe defaulting `location`/`note` to `""` would
    attest that something was examined when it was not.
- **Two asymmetries in the M3 brief are now three-plus-one:** `TraceabilityLink` remains
  the one *invented name* (the link object is declared inline, so it has no `title` to
  join on) and the **`INLINE_MIRRORS` exception is still outstanding** — M1's request to
  promote `traceability-link.schema.json` is unanswered, so parity is still not a clean
  bijection. `Finding` did **not** add to that set: `findings`/`Finding` agrees
  case-insensitively, so the filename/`title` disagreements stay at **three**
  (`run`, `traceability`, `verdict`) — recounted from source, not taken on trust.
- **Proven, not asserted:** 9 mutations against fresh throwaway copies. The **first
  harness was broken and reported 7/7 killed — all false** (bare filenames make pytest exit
  4, and `rc != 0` scored as a kill). Only a **control run** and reading *which* test
  died exposed it; the true baseline was 3/7 with 4 real survivors, all now closed and
  re-proven 7/7.
- **AC 1 note:** still ticked, and now true for the sixth contract as well. AC 3 ("literals
  stay in sync with the schema enums") extends to `Probe`, whose enum-sync check lives in
  `test_schemas_contracts.py::FIVE_PROBES` while its **wiring** check lives here — the
  two are deliberately in different files, which is what let the wiring go unguarded until
  this session.
- **M3 is still not load-bearing** (`architecture.md` §11.10): the mirrors have **zero
  product callers**, so this session made the *shapes* trustworthy and nothing more. The
  two strictness obligations (artifact-envelope projection, M9's superset record) are
  untouched and remain M9/M14's.
- **Owed, not done:** §11.12's three original enum fields are still unguarded; nothing
  in this session widens the support matrix (that is M17's file, §0.4); and `requirements.txt`
  still pins no transitive dependency, so **no leg of this verification is reproducible**
  until M17 decides on pins or a lockfile.

### 2026-09-27 — Session 24: refactor plan — module decisions (no code change)
- **Plan-mode session, zero code/contract/fixture/dependency changes.** Trigger: LabLab Admin
  made the **Bob IDE a showcase requirement for judging eligibility** ~5h before submission;
  all developers paused; $40 Bob credits on join remove the coin blocker. The decisions below
  change module scope or ownership — owners fold them into their briefs when they land
  (rule 10 records findings in `architecture.md`; these are *decisions*, logged at their source).
- **M13 — the mutation harness is OUT of the current architecture (user decision).**
  `origin/bob/m13-mutation-harness` (GiGi, 2 commits) is unpruned dead work and will be
  **deleted**; the harness acceptance criteria in §M13 are superseded for this build.
  **What stays as-coded:** `metrics/false_certified.py` + its tests, `exposure.schema.json`
  + validator pair, and the honest `measured: false` stub on `/api/metrics` (never remove a
  shape tests and the coverage check depend on — presentation is the cheap fix, removal is
  not). Consequence: the false-certified rate **cannot be measured in this build**; the demo
  shows no number at all rather than a synthetic one.
- **M16 — scope change:** **hide `<ExposureCard>` for the demo** (frontend-only; this
  supersedes M2's request #2 to feed it `demo_exposure.json` for now). Rest of M16 unchanged:
  `npm install`/`npm run build` at Phase 0, the `VerdictBadge` lowercase-`status` defect,
  triple-fixture cleanup, and proof that the matrix renders **live** (no fixture-mode banner).
- **M18 — scope change:** the runbook gains the **Bob integration**: new `scripts/attest.py`,
  **HTTP mode** (POST `/webhooks/github` → poll `GET /api/runs/{id}` → print verdict +
  traceability → exit with the run's `exit_code`; `--direct` in-process fallback), plus
  `fixtures/demo_payload.json` holding the §1.7 body. HTTP mode is deliberate — it dodges §6's
  CWD-relative SQLite trap. Bob's demo moment is **invoke only** (one command-tool call, no
  live code authoring mid-demo).
- **Ownership / build assignments (one writer per file, §0.4 honored):**
  - **Role 1 → Cody:** M10 + M15 (R1 loop wiring, R2 serve + `main.py` `_dist` fix; the
    stub-test flips are in scope and must land in the same commits — rule 7).
  - **Role 2 → Aixxn:** merge their own **`M4-ingest`** (45-min timebox; fallback =
    cherry-pick `b1689c3` `select_client` + `6c69c04` D1 ratification, then stub-passthrough
    ingest), **§11.15** fix inside that merge, M3-file conflicts resolved (main's Finding
    mirror wins; docs keep both — Session 20 pattern).
  - **Role 3 → baron:** R4 thin slice on **M5/M8/M9** — real extract parsing, real
    adjudicate ladder per §1.4 (D1), derived `exit_code` per §1.5; parse/verify stay
    stub-shaped with mock-backed §1.7 findings (Convention 4, provenance in the runbook).
    Plus integration merges of every green lane.
  - **Role 4 → GiGi:** M18 deliverables above (freed by the harness drop).
  - **Role 5 → FE dev:** M16 scope as changed.
- **§1.7 is the demo contract** for R4's target outputs. Budget: **3h build / 2h rehearsal**
  (authorized deviation from Convention 6's nominal final-4h). D1 rides the `M4-ingest` merge;
  no contract changes are planned, so the validator stays 6/6 throughout.
### 2026-09-27 — Session 19: M2 — demo corpus landed (commit `88095b2`)

### 2026-09-27 — Session 19: M2 — demo corpus landed (commit `88095b2`)

- **M2 implemented.** 6 files: 3 fixtures, the served copy under `frontend/public/`, the
  shared guard `test_schemas_contracts.py`, and this file. No router, no contract, no
  dependency, no new `.md`. Acceptance criteria 2–5 met; **criterion 1 stays open** because
  `frontend/src/fixtures.js` is M16's file and `App.jsx` still imports it.
- **Two decisions were taken by default because their owners were unreachable**, per §6, and
  are recorded rather than assumed: **D1** (CERTIFIED requires E4 minimum, applied to fixture
  data only) and **D9** (`status` takes the §1.2 lowercase lifecycle, hence `"rejected"`).
  Neither is ratified, so **no test asserts either rule in general** — only what this fixture
  does. That is deliberate: a provisional decision must not calcify into a contract.
- **Open question this session could not settle for the project, recorded rather than
  decided unilaterally:** the acceptance checkboxes are now marked *inconsistently*. Criteria
  4 and 5 are ticked although each is half done (the data landed; the dashboard wiring is
  M16's), while criterion 1 is left unticked although it is also half done. Both situations
  are the same, and they are marked differently. Either convention is defensible — tick when
  the module's own deliverable exists and file the downstream wiring as a request, or tick
  only when the stated outcome is achieved end-to-end — but the mix is not, and M1, M3, M14
  and M16 will all hit the same question. **This belongs in §0.3 as a stated rule, decided
  once by the project, not per module.**
- **Three M16 requests filed** (see the M16 section): delete `fixtures.js` and fetch the
  served copy; feed the exposure fixture to `ExposureCard`; and a verified defect —
  `App.jsx:23` passes `run.status` into `VerdictBadge`, which compares it against the
  *uppercase* verdict enum, so a D9-conformant `"rejected"` renders **orange**, the `PENDING`
  colour. Root cause is deeper than case: `run.schema.json` carries no aggregate verdict
  field, so a lifecycle string is rendered by a verdict renderer, and no product code
  computes `status` at all today.
- **Not archived here:** the §M2 "Landed" block and the M16 requests were committed with the
  code in `88095b2`. `AGENTS.md` is gitignored and so is not in any commit.

### 2026-09-27 — Session 20: M12 attestor read-only policy (`9c7343d`, branch `M12-attestor`)

- M12 only; no endpoint, contract, schema, or dependency touched. Stdlib only.
- `GRANTS` gained **`llm_egress`** because M7b workers call watsonx.ai themselves
  (`docs/intent-attestation-gate.md:33` already said so — this ratified the spec rather than
  inventing it). Named for the capability kind, never a host: egress must cover both the auth
  and inference endpoints and the region is env config, so a host-bearing token would need a code
  change per region. A blanket `network` grant stays rejected and is pinned — open egress would
  let a worker exfiltrate the source it reads, which is the read-only claim itself.
- **Decision taken deliberately before M7, not after it failed:** the vocabulary question was
  settled while nothing depended on it, precisely so M7b would not meet a `PermissionError` at
  worker startup and be tempted to loosen the policy under deadline. Widening the policy is
  mutation-tested at 22 failures, so it cannot happen quietly.
- New `backend/app/attestor/sandbox.py` supplies the half that was missing entirely: proof that
  the workspace is read-only, by attempting the forbidden write. Without it, withholding `edit`
  while the workspace is writable was theatre.
- **AC status: 1 and 3 are partly open** — the primitive and the record fragment exist and are
  pinned, but the worker-startup call is M7/M10's file and the `attestor_policy` key is M9's.
  Neither was faked into a stub that M7/M9 would delete.
- **New forward dependency:** M7b now hard-depends on M10 provisioning a read-only workspace.
  If M10 probes before mounting, the worker refuses to start — correct, and it looks like a bug.
- **Open, and a hard blocker on M7b shipping rather than a follow-up:** the egress allowlist does
  not exist, so `llm_egress` is declared and enforced by nothing. Also unresolved: the
  `--disable-subagents` vs granted-`subagent` tension, kept-as-is since Session 7.
- **Honest gap:** no test has watched a real read-only mount refuse a write. Production refuses
  via `EROFS`; every refusal test gets `EACCES` from a `chmod 555` directory. Dropping `EROFS`
  does fail the suite (2 tests), so the translation is pinned — but that is substitution, not
  observation. M17's to close.

### 2026-09-27 — Session 25: M1–M3 execution — module decisions

- **Commit discipline (user instruction): one commit per module done.** M2's
  `fixtures/demo_payload.json` landed alone (`1b5be27`); `scripts/attest.py` +
  `backend/tests/test_attest_cli.py` stay untracked for M18's lane commit, not bundled
  with M2's. Docs for this session land as a second, separate commit. M1 and M3 ship
  no code this build (freeze + merged state), so they have no commits.
- **M3's `traceability-link` promotion request stays deferred** — promoting it would be
  a schema change and conflicts with the M1 freeze (refactor-plan D-f). The
  `INLINE_MIRRORS` self-invalidating exception remains the safe holding pattern.
- **Ownership ignored by instruction:** the user is finishing everything under the time
  constraint, so §0.4 lane assignments were not consulted; §0.4 itself is unchanged.
- **Branch note:** `refactor` @ `1b5be27`, still not pushed; the `origin/refactor`
  divergence stands (`7f65009` has an identical tree to `a869622`, so the pending
  pull/merge is content-trivial — reconcile before push).
- **Follow-up (same session, /end):** the divergence is gone with **no merge needed** —
  the `m10-orchestrator` merge (`932ca68`) already carries `7f65009` in its ancestry, so
  the `origin/refactor` tip is contained in HEAD: **ahead 12, behind 0** (verified via
  rev-list count + `merge-base --is-ancestor`). `git fetch` fails on this machine (no
  remote access), so the remote tip cannot be re-confirmed and **push is still pending**
  — push `refactor` when the network allows; if rejected as non-fast-forward, fetch +
  merge, re-run the suite gate, then push.

### 2026-09-27 — Session 25 (R4): M5/M6/M7-stub/M8/M9 landed (this session)
- **Scope as user-confirmed at /start:** wait for M4 merge (done locally as `27ec711`,
  no network) → include M8 → M9 thin slice → build on `refactor`. M5/M8/M9 ACs ticked
  above with supersede notes (M5 dual-mode, M9 chain/ledger/exposure); M6 pass-through
  and M7 mock stub recorded in their sections (no real-probe AC claimed).
- **Cross-lane contracts honored:** §1.8.3 threading implemented exactly as settled
  (M5 threads files/workspace; M6 threads criteria; M7-stub threads criteria with
  mock findings; M8 threads criteria to M9). Custody tests in `test_gates.py` (the
  file that owns what no single stage owns); chain-order E2E there too, not in
  M10's `test_pipeline.py`. `verify.py` touched minimally under R4 authority (M7
  ownerless this build) — probes untouched, still XL and still M7's.
- **Two interpretations committed and recorded** (not silently assumed): (1) refuted+
  located caps at E2 (§1.8.4's silent cell; demo-anchored); (2) M5's brief dual-mode
  ACs are superseded by deterministic extraction (D-c/D-f) — the no-import test is
  the §11-gap-9 consumer control.

### 2026-09-27 — M10 lane (R1): loop wired, both §11.1 tests flipped (`a7178d2`)
- **Executed the refactor plan's R1 on an isolated worktree** (`/tmp/opencode/m10-lane`,
  branch `m10-orchestrator` off `refactor` @ `7f65009`): Role 2's `M4-ingest` merge was
  found **in progress on `main`** (MERGE_HEAD `c229861`, five UU paths — exactly the
  dry-run's five; files touched minutes before execution started), so the lane never
  touched `main`. None of the merge's files overlap M10's (`pipeline.py`, `jobs.py`,
  `main.py`, `test_pipeline.py`, new `persistence.py`/`conftest.py` untouched there).
- **Shipped (single atomic commit, rule 7):** `enqueue_run` persists + submits;
  `run_pipeline(payload, run_id=None)` pure without id, persisting with one
  (`running` → `pending`/`failed` + artifact; row-missing skips stages but still
  writes the blocking artifact); `worker(queue, stop)` vets caps at startup,
  `to_thread`s items, stops on event + `None` sentinel; `main.py` lifespan starts/stops
  it (R1-held; `_dist` untouched); `persistence.py` wraps `db` helpers only (no SQL,
  no `commit()`); `conftest.py` redirects db + artifacts to `tmp_path` and drains the
  queue (M17 to adopt). **Both §11.1 tests flipped same-commit** (submit-shape rewrite
  + dynamic lifespan flip via `with TestClient`); 6 → 16 tests in `test_pipeline.py`.
- **Guard proof (`/tmp/opencode/m10-guard-proof.py`, Session 21 rules): 8/8 killed,
  0 survivors** — rowcount bypass, catch removal, insert drop, caps-check drop (hang-kill,
  rc=124 — the check's absence is catastrophic, which is why it exists), shape drop,
  rowcount-force-true, lifespan unwire, conftest removal (ordering pollution breaks the
  submit guard). Restore verified byte-identical; tree clean.
- **§6: filed D14/D17/D18/D19; D16 deliberately skipped** — it lived on Role 2's
  `M4-ingest` branch (verdict vocabularies) and a second D16 would have collided at
  integration, so the reservation was noted in-table. **The reservation has since been
  filled:** the M4 merge landed D16 as predicted and the table now reads D13–D19
  contiguously. D18 (worker contract) is answered by this lane. Tick convention stated
  in §M10 (Session 19's open question: tick the module's own deliverable, file
  downstream as request).
- **Landing + integration verification (second pass of this entry):** the behavior
  commit `a7178d2` reached `refactor` early via `932ca68`; this docs commit was
  stranded and lands now by rebasing onto `refactor` (Session-20 keep-both — M4's
  Sessions 19/20 and Session 25's record preserved above; §11.5 merged with M12's
  narrowing instead of overwriting it). **Chain tests re-run against Role 2's real
  `ingest`: 349 passed, 0 failed on 3.11.9 AND 3.12.14 at the verified tip
  (`1b5be27`), validator 6/6 both legs, tree clean** — §11.15 closed on this branch
  via `0cac970` (M3's Finding-mirror line), not this lane. Scope note: Session 25's
  `399` includes the main checkout's in-flight R4 files; `349` is the committed tree
  at the verified SHA.
- **Still open:** lane branch unpushed (push for Phase-2 integration); `test_api.py`'s
  three stub flips + `_dist` + serving are R2's; `refactor` moved twice during this
  verification (`1b5be27`, `ba6eec0`) — re-run the suite if it moves again before
  merge. **Re-verified at `2048e7c` after R4/R2 landed (`c073dbe`, `2048e7c`): 399
  passed, 0 failed both legs, validator 6/6, tree clean — all 16 guards green against
  the real chain.**

### 2026-09-27 — Session 25 (M15/R2 + M18): serve real runs, `_dist` fix, Bob CLI (`ab2849c`)
- **Session shape:** `/start` planned M14 + M17 + M18 against the refactor plan; the user then
  reassigned the whole build to one agent and said "execute". Postures settled at `/start` and
  honoured here: **M14 verify-only** (no edits — done and frozen by the plan), **M17
  gate-keeper** (define green, police rule 7, no new coverage), **M18 build**. The M4 + R1
  merges and R2 landed here; **R4 was explicitly skipped** (user instruction; another lane
  shipped `c073dbe`), and the lanes were kept strictly disjoint by file.
- **M14 — verified, not touched.** All six checklist items pass; AC-1 is discharged by its
  *callers* (M10 writes, M15 reads), which is the shape the brief predicted when it ticked
  the seam and left the callers open. Its 40 guards ran twice — before and after R2 started
  reading the same store — green both times.
- **M15/R2 — the API stopped lying.** `GET /api/runs` lists index rows newest-first;
  `GET /api/runs/{id}` serves the row's lifecycle status plus the artifact's
  `verdicts`/`measured`, points at `artifact_path`, and 404s an unknown id instead of echoing
  it. `_dist` climbs two levels now, with `mount_dashboard()` extracted so a test proves the
  mount appears *and* no-ops — the honest fix the criterion asked for, not a comment claiming
  one. Why the detail route reads the artifact defensively rather than through the strict
  `RunRecord` is documented at the brief, not only here.
- **M17 — one micro-task, no scope creep.** `.gitignore` now covers the CWD-relative
  `attestation.db` / `artifacts/`. The brief's optional hardening (3.10 in the matrix, D10
  `RefResolver`) stays out: D10 is "not during the build", and the matrix was left alone.
- **M18 — the Bob CLI, and one thing the plan got wrong.** `scripts/attest.py` (stdlib-only)
  + 9 guards. The plan's "exit with the run's `exit_code`" has no such field anywhere in the
  served or contracted surface, so the CLI derives the exit from `status` rather than adding
  a contract key under a frozen contract. Recorded consequence: a `pending` status is
  **terminal** (D-e — the chain completed), so listing it as in-flight would hang every
  finished run. Caught by the first real cold E2E, not by the fake-gate test.
- **Not claimed:** the runbook append, the foreign dry-run, the fallback video, the push.
  **M18 is not done** — one of its four criteria is met.

### 2026-09-27 — Session 25 (Phase 3 prove): M9's record is flat, and the E2E that proved it
- **M9 correction (product, not just tests):** the stage output no longer nests the run record under `record`. It is flat beside the `stage`/`ok` envelope — the only shape every other stage in the chain already used, and the only shape `run.schema.json` (frozen, required keys at top level), M14's `project_run_payload`, and M15's `runs.py` all read. Found by running the plan's Phase 3 cold end-to-end: the artifact was correct on disk while the API served `pending` + `[]`. **The brief's "extends it" AC is unchanged — the echo and the extension are both still there; only the wrapper level moved.** Two guards that had pinned the nesting were flipped in the same change, and a new seam guard now pins the record against its committed consumers (contract / M14 / M15's read path) rather than against this module's own design.
- **M15/M16 finding, recorded not fixed:** `GET /api/runs` (list) and `GET /api/runs/{id}` (detail) both return a key named `status` with **different meanings** — row lifecycle vs. artifact verdict. The dashboard reads only the detail endpoint, so the demo is unaffected; settling the name is the API surface owner's call, and D16 already tracks the `status` vocabulary tension.

---

*MERGE (`33e02bd`, M12 follow-up #49 into `refactor`): the two entries above and below are the same session-log tail on both sides — whole-paragraph appends with no overlapping edited lines — so both are kept verbatim, Session 20/25 precedent. The incoming side carried M12's `Session 22`-labelled entry; this file's M12 record is the same module under the older `Session 20` label, retained with the equivalence noted at §M12 rather than renumbered here. Both sides also claimed the `assert_read_only` worker-startup wiring as open; it is closed on the merged tree (`orchestrator/jobs.py:39`, R1 `a7178d2`), verified from source.*

### 2026-09-27 — M12: fits the current architecture (A + B + C)

> **Heading relabelled, content untouched.** This entry was "Session 22" until the merge
> that unblocked PR #48, because `main` independently carries a *"Session 22: M14
> persistence"* and a *"Session 23"* from a parallel session and two entries with the same
> number in one log is a legibility defect in a record whose entire premise is that
> claims must be checkable. Numbering dropped per `AGENTS.md` Convention 18 (cite date +
> module). **Prose inside this entry still says "Session 22"** and refers to this same
> entry — deliberately not swept, so the diff into a file with an incoming merge conflict
> stays as small as possible. That is a recorded inconsistency, not a silent one.

- **Instruction:** *"I am working on the M12 attestor read-only policy. The llm layer is
  only using mock data for it, because there have been changes"* — clarified to *"update
  m12 to fit the current system architecture."* `/start` protocol first, then a plan agreed
  as three named changes: **A** attest the D6 mechanism, **B** let the record name the
  workspace, **C** close the ungated leak. `llm_egress` was decided explicitly: **keep
  it, record it as unexercised.**
- **The premise was half right, and the right half was not where the problem was.** The
  LLM layer *is* mock-only — `MOCK_LLM` is read nowhere in `backend/app`, `mock_client` is
  imported only by tests, and `watsonx_client.complete` is `NotImplementedError` past the
  key check (§11.9). But that touches M12 in exactly one token, and the module's real
  mismatch was elsewhere: **the docs described a module that had not existed for a
  session.** `sandbox.py`, `resolve_worker_caps`, `PolicyRecord`, `enforce_worker_read_only`
  and the fifth grant were all on disk and in no brief.
- **The finding that shaped the change:** a refused write is **two different findings**,
  and the module reported them as one boolean. A 0555 directory — a permission on one
  inode that whoever owns it can restore — produced a record byte-identical to a real
  read-only mount, which is the boundary D6 actually asks for. So the record now names
  the mechanism (`read_only_mount` vs `no_write_bit`) and carries the mount's own
  `ST_RDONLY` answer alongside the kernel's errno. The mount flag is read **after** the
  write and can never override it, because an implementation that let the flag win would
  report a workspace as read-only immediately after accepting a write — the fail-open
  inversion of everything this module claims. That ordering is pinned by a test that makes
  the write land and the flag lie.
- **The hole in C was real and ungated by design.** `policy_record(..., enforcement_applied
  =False)` returned without ever consulting `DENIES`, so it would mint a record whose
  `capabilities` was `["edit"]` while its own `denied` said `["edit", "execute"]` — the
  module whose purpose is that those cannot both be true, producing both. Both record paths
  now refuse, with distinct messages, because a run that never gated has no policy to
  violate and its defect is incoherence rather than a leak. The check was deliberately
  **not** extended to completeness: an ungated record legitimately reports a partial set,
  and requiring all five grants there would make the not-probed marker unusable.
- **Three guards flipped deliberately in the same change (rule 10), each labelled
  `CHANGED THIS SESSION` in the test:** two exact-dict record-shape assertions, and the
  module docstring's claim that *exactly one* test substitutes the OS call. The last was
  a false claim the moment the second substitution landed, and the inventory was recounted
  from the file rather than estimated — the first draft of that recount said three
  `statvfs` substitutions where there are four.
- **A test whose docstring overstated what its body checked was rewritten rather than
  left.** `test_the_two_readings_are_reported_separately_not_collapsed` described a
  contrast between two deployments and then asserted one; it now actually makes both
  readings and asserts they differ, which is the argument for carrying the field at all.
  A test that describes more than it checks is the same defect as a docstring that
  describes more than the code does.
- **A strict reading of D6 was considered and rejected, on the record.** Requiring a real
  read-only mount to start a worker is the honest maximal reading — and it would refuse to
  start on any machine that cannot mount read-only, including this one and CI, saying
  nothing about whether the control held. D6's "fail closed" attaches to the capability
  check, not to a demand for one specific kernel mechanism. Both refusals still start a
  worker; the record now says which one it got. Revisit only if M10 can guarantee the mount.
- **`llm_egress` kept, and the admission recorded in prose rather than in the record.** A
  per-run key saying "this grant is never enforced" is a thing an auditor can misread as
  enforcement; a sentence in the brief cannot. The token stays because M7b's workers call
  watsonx.ai themselves, and **nothing exercises it yet** — there is no worker pool.
- **Docs updated, no new files (Convention 1):** this brief rewritten to the as-built two
  layers, `sandbox.py` added to M12's row in §0.2 (**it was owned by nobody**), plus the
  `architecture.md` §3 row / §8 / §11.5 / §11.11 / §12 layout, `test-suite.md` layout and
  §8 coverage row, the `intent-attestation-gate.md` file-layout line, and a **dated
  supersession note** on `watsonx-integration.md` §6 rather than a rewrite of that
  dossier's point-in-time snapshot.
- **Debt found and recorded, not fixed:** the two-layer policy, the fifth grant and the
  whole of `sandbox.py` landed with **no session-log entry in any doc** — this file ends at
  Session 21, `architecture.md` at Session 21, and `AGENTS.md` at **Session 15**. It is
  recorded here as a finding reconstructed from source rather than as a fabricated entry
  attributed to a session that did not write it. `AGENTS.md`'s history is six sessions
  stale and is updated only by `/end`.
- **Also found and deliberately left:** `test_enforce_workspace_readonly_returns_the_proof_
  on_a_read_only_workspace` carries a **duplicated `@SKIP_AS_ROOT` decorator**. Harmless by
  construction, pre-existing, and unrelated to this change — noted rather than quietly
  fixed inside someone else's line.
- **No contract, fixture, dependency, endpoint or gate file was touched.** No
  `conftest.py` — the root-skip marker stayed in `test_policy.py`, where it was already
  reasoned about. `validate_contracts.py` output is a non-regression check, not a new
  assertion: the `attestor_policy` fragment remains part of the un-contracted artefact
  envelope (**D15**), which is M9's and M14's obligation.
- **Verified, not asserted.** **192 collected, 191 passed** — identical on **3.11.16,
  3.12.14 and 3.14.7**. Both CI-matrix legs were **provisioned fresh** for this session
  because neither was installed and a 3.14 result does not count (rule 9). Validator exit
  0 on every leg. `test_policy.py` **75 passed, 0 skipped** (baseline 63, **+12**), run as
  uid 1000 so all 21 root-guarded cases actually executed instead of skipping — which is
  what makes the 0555/`EACCES` evidence real rather than bypassed. Zero probe residue;
  source tree byte-identical before and after.
- **Convention 7 satisfied, and the control run earned its keep again.** Seven mutations,
  seven kills, no survivors; the fail-open inversion (M5) died on the guard's own message.
  **The harness's first score was a false kill for the second time in two sessions** — an
  imported-constant rename breaks *collection* (pytest exit 2, zero tests collected), and
  `rc != 0` would have scored it as a kill. Session 21's first harness reported 7/7 false
  kills the same way. Hardened to accept only exit 0/1 plus a node id outside the known
  baseline, and M3 re-expressed so the guard actually ran.
- **The suite's one failure is not M12's, and not "unfinished work" either.**
  `test_models_parity.py::test_demo_traceability_fixture_loads_into_model` asserts
  all-E0 links while M2's merged corpus (`88095b2` → `4b03c55` = HEAD) set E4/E2. That is
  a **missed guard flip in the M2 merge** — `test_schemas_contracts.py` was updated,
  `test_models_parity.py` was not — and there are **two** stale assertions, not one.
  Proven pre-existing by running a pristine `git archive HEAD` extraction (`1 failed, 179
  passed`, M12 absent). **Not actioned:** `test_models_parity.py` is M3's and the fixture
  is M2's, so fixing it here would be a two-owner edit (rule 2/§0.4). **It will not clear
  itself when the remaining modules land**, which is the part of "still unfinished" that
  does not hold — filed in `docs/test-suite.md` for its owner.
- **Provenance of the baseline, found last and worth recording because the record was
  missing it entirely.** The two-layer policy, `sandbox.py`, the fifth grant and the first
  63 tests were **not** unlogged improvisation — they are commit **`9c7343d`**, authored
  by `Aixxn <adrianazures6@gmail.com>`, merged as **PR #42** (head `M12-attestor`,
  2026-09-27). `9c7343d` reached `main` as a *side effect* of PR #43 merging first: #43's
  branch had `9c7343d` as its parent, so #43 pulled it in and #42 then merged with nothing
  left to merge — which is why it is absent from main's first-parent chain and why two PRs
  show one landing. So the debt recorded above is narrower than "nobody logged it": the
  commit and PR exist, and only the **doc record** was never written. Session 22's entries
  are the first and only record of it.
- **Delivery: `936db35`, 8 files, 1003 insertions / 70 deletions, PR
  [#48](https://github.com/baronocasiones/Intent-Gate/pull/48) OPEN** against `main` from
  `m12-attestor-policy`, pushed with the explicit refspec
  `git push -u origin m12-attestor-policy:m12-attestor-policy`. The PR body opens by
  naming #42, because a reviewer who sees 314 test lines and no `assert_read_only` would
  otherwise conclude the differentiator was never built. The merged `M12-attestor` ref was
  **not** touched (`9c7343d`, verified still at that SHA after the push).
- **The rebase onto `main` was attempted and ABORTED on conflict, and the branch is 1
  behind.** `main` moved to `bf52608` (M14, #47) and both sides append to the same
  session-log tails, so `docs/architecture.md` and `docs/test-suite.md` conflict
  append-vs-append. The rebase was aborted rather than resolved, so `936db35` survives
  byte-for-byte. **Resolution is "keep both entries"** and it belongs to whoever merges.
- **A session-number collision, which is this log's problem and not the merger's:** `main`
  now carries entries titled **"Session 22: M14 persistence"** and **"Session 23:
  verification round archived"** from a parallel session. This entry is *also* Session 22.
  The two are unrelated and both are real. Renumbering here would only trade a duplicate
  label for a different lie about the sequence, so the collision is recorded instead —
  **the numbering scheme is per-session-local and does not survive parallel work, and
  someone should decide what replaces it before the next four sessions land.**
- **Correction to a false claim that has been propagating across sessions.** Session 15
  recorded *"no credential helper and no `gh` in this environment, so no PR exists yet and
  write access for `Cody-me` is untested."* **All three parts are false.** `gh` **2.101.0
  is installed** at `/home/cody-laptop/.local/bin/gh` and merely **not on `PATH`**, which
  is why `which gh` failed and the absence was concluded. There *is* a credential helper —
  it is URL-scoped, `credential.https://github.com.helper = !/home/cody-laptop/.local/bin/gh
  auth git-credential`, so git authenticates without `gh` ever being on `PATH`. `gh auth
  status` shows a live `repo`-scoped session for `Cody-me`. **Write access is now tested
  and confirmed** (`git push --dry-run` exit 0, then a real push to `936db35`). The lesson
  generalises past git: *a tool reported missing by a `which`-style probe may be present
  and merely unpathed, and "we could not find it" is not the same claim as "it does not
  exist."*
- **One trap found in the local config, left in place and documented rather than silently
  fixed:** `branch.m12-attestor-policy.merge` pointed at `refs/heads/main`, so `@{u}`
  resolved to `origin/main`. A bare `git push` is actually **aborted** by git
  (`push.default=simple` refuses when the upstream name differs, exit 128) rather than
  silently hitting main — but git's own error message suggests `git push origin HEAD:main`,
  which would, and anyone setting `push.default=upstream` turns it into a silent push to
  main. `git push -u` with an explicit refspec fixed it, and that is the form recorded in
  the module docstring's wiring instructions.



