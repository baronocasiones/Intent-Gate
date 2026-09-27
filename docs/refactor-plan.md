# docs/refactor-plan.md — Bob IDE demo integration (Session 24, 2026-09-27)

> **Execution handoff, not a new record.** As-built facts live in `docs/architecture.md`,
> intent in `docs/intent-attestation-gate.md`, the gap between them in `docs/modules.md`
> (precedence per the Figure 6 rule). This file compiles the Session 24 decisions, the
> exact doc updates made at its `/end`, and the per-module refactor tasks — so the five
> lanes can start without digging through three records. Created on explicit user
> instruction (Convention 1 otherwise forbids new `.md` files); do not fork it — append
> outcomes to the source records, not here.
>
> **Baseline:** `main` == `origin/main` @ `bf52608`, clean tree, `MOCK_LLM=true` for
> demo/CI. **Suite is 210 pass + 1 known red** (§11.15) — the only thing between `main`
> and a green badge. Submission closes **15:00 UTC**; budget is **3h build + 2h rehearsal**.

## 1. Locked decisions (Session 24 — user-confirmed)

| # | Decision |
|---|---|
| D-a | `origin/bob/m13-mutation-harness` **dropped** — unpruned dead work (GiGi, 2 commits); the mutation harness is not part of the current architecture. Branch deleted at Phase 0. GiGi → Role 4 |
| D-b | **ExposureCard hidden for the demo** — frontend-only. Backend `/api/metrics` stub + `exposure.schema.json` + validator pair **stay** (route-table test + 6/6 coverage depend on them) |
| D-c | **R4 thin slice as scoped** — deterministic extract/adjudicate/emit per §1.7; parse/verify stay stub-shaped with mock-backed findings (Convention 4) |
| D-d | **Bob invokes the gate only** — one agent command-tool call; the run's `exit_code` is the merge signal. No live code authoring mid-demo |
| D-e | `M4-ingest` **merged**, 45-min timebox; fallback = cherry-pick `b1689c3` (`select_client`) + `6c69c04` (D1 ratification), then stub-passthrough ingest |
| D-f | Live watsonx **out** (model id unprovisioned); no new dependencies (rule 9); contracts **frozen** |

## 2. Doc updates made at Session 24 `/end` (verbatim)

### 2.1 `docs/architecture.md` — appended session entry

> ### 2026-09-27 — Session 24: Bob-IDE refactor plan (planning only, no code change)
> - **Trigger:** LabLab Admin ruled (Discord, this session) that the **Bob IDE must be showcased as a core component** of the solution to be eligible for judging — ~5h before the 15:00 UTC submission cutoff — and all other developers were paused pending this plan. The hackathon grants **$40 Bob credits** on join (~80 Bobcoins at the documented $0.50), which removes the coin-exhaustion blocker that initially threatened a live Bob segment.
> - **Implemented:** nothing — plan-mode session: zero code, contract, fixture, dependency, or endpoint changes. Delivered the plan *"Close the loop, put Bob on the critical path"*: R1 loop wiring (M10 ACs) · R2 serve runs + `_dist` fix (M15 ACs) · R3 `select_client` landing · R4 deterministic chain slice against §1.7 · R5 §11.15 · R6 HTTP-mode Bob CLI (`scripts/attest.py`) · R7 dashboard · R8 prove/rehearse; 5-phase timeline (**3h build + 2h rehearsal**); branch disposition; risk fallbacks; out-of-scope list.
> - **Verified from source this session (re-confirming §11 as live, not stale):** `enqueue_run` still mints an id only; `jobs.worker` never started; `runs.py` hard-coded stubs; `main.py` `_dist` three-level climb unchanged; `ExposureCard` fed solely by `fetchMetrics()` (the stub). Branch state re-mapped: `main` == `origin/main` @ `bf52608`, clean; **all remote branches merged except** `M4-ingest` (7 commits by Aixxn — merge dry-run: **5 conflicts** = `schemas.py`, `test_models_parity.py`, 3 doc logs) and `bob/m13-mutation-harness` (2 commits by GiGi — dry-run: 3 doc-log conflicts only). Bob's integration surface confirmed from official docs: command/shell tools + MCP — the plan uses the command tool, no new dependency.
> - **User decisions affecting this record:** (a) **the mutation harness is not part of the current architecture** — `origin/bob/m13-mutation-harness` is unpruned dead work and will be deleted; note **§9, `exposure.schema.json`, and the `/api/metrics` stub are unaffected and remain as-coded** (the harness was never on `main`); (b) **ExposureCard hidden for the demo** — frontend-only; backend endpoint, contract, validator pair stay (route-table test + 6/6 coverage depend on them); (c) R4 thin slice as scoped; (d) Bob demo = **invoke the gate only** (one command-tool call; the run's `exit_code` is the merge signal); (e) `M4-ingest` merges with a **45-min timebox** and pre-agreed cherry-pick fallback (`b1689c3`, `6c69c04`).
> - **API endpoints:** none defined, changed, or removed. **Dependencies added:** none.
> - **Open at archive:** plan awaiting "go" (Phase 0 = delete dead branch, start M4 merge, `npm install`, Bob + credits health check, baseline suite); §11.15 still the only known red; **Figure 6 still do-not-show** (§11.11 unchanged); admin's answer on whether a pre-recorded Bob session counts is still pending; submission packaging unowned until Phase 5; the Aixxn/GiGi work sessions have no AGENTS.md entries of their own (branch state recorded here instead).

### 2.2 `docs/modules.md` — appended session entry

> ### 2026-09-27 — Session 24: refactor plan — module decisions (no code change)
> - **Plan-mode session, zero code/contract/fixture/dependency changes.** Trigger: LabLab Admin made the **Bob IDE a showcase requirement for judging eligibility** ~5h before submission; all developers paused; $40 Bob credits on join remove the coin blocker. The decisions below change module scope or ownership — owners fold them into their briefs when they land (rule 10 records findings in `architecture.md`; these are *decisions*, logged at their source).
> - **M13 — the mutation harness is OUT of the current architecture (user decision).** `origin/bob/m13-mutation-harness` (GiGi, 2 commits) is unpruned dead work and will be **deleted**; the harness acceptance criteria in §M13 are superseded for this build. **What stays as-coded:** `metrics/false_certified.py` + its tests, `exposure.schema.json` + validator pair, and the honest `measured: false` stub on `/api/metrics` (never remove a shape tests and the coverage check depend on — presentation is the cheap fix, removal is not). Consequence: the false-certified rate **cannot be measured in this build**; the demo shows no number at all rather than a synthetic one.
> - **M16 — scope change:** **hide `<ExposureCard>` for the demo** (frontend-only; this supersedes M2's request #2 to feed it `demo_exposure.json` for now). Rest of M16 unchanged: `npm install`/`npm run build` at Phase 0, the `VerdictBadge` lowercase-`status` defect, triple-fixture cleanup, and proof that the matrix renders **live** (no fixture-mode banner).
> - **M18 — scope change:** the runbook gains the **Bob integration**: new `scripts/attest.py`, **HTTP mode** (POST `/webhooks/github` → poll `GET /api/runs/{id}` → print verdict + traceability → exit with the run's `exit_code`; `--direct` in-process fallback), plus `fixtures/demo_payload.json` holding the §1.7 body. HTTP mode is deliberate — it dodges §6's CWD-relative SQLite trap. Bob's demo moment is **invoke only** (one command-tool call, no live code authoring).
> - **Ownership / build assignments (one writer per file, §0.4 honored):**
>   - **Role 1 → Cody:** M10 + M15 (R1 loop wiring, R2 serve + `main.py` `_dist` fix; the stub-test flips are in scope and must land in the same commits — rule 7).
>   - **Role 2 → Aixxn:** merge their own **`M4-ingest`** (45-min timebox; fallback = cherry-pick `b1689c3` `select_client` + `6c69c04` D1 ratification, then stub-passthrough ingest), **§11.15** fix inside that merge, M3-file conflicts resolved (main's Finding mirror wins; docs keep both — Session 20 pattern).
>   - **Role 3 → baron:** R4 thin slice on **M5/M8/M9** — real extract parsing, real adjudicate ladder per §1.4 (D1), derived `exit_code` per §1.5; parse/verify stay stub-shaped with mock-backed §1.7 findings (Convention 4). Plus integration merges of every green lane.
>   - **Role 4 → GiGi:** M18 deliverables above (freed by the harness drop).
>   - **Role 5 → FE dev:** M16 scope as changed.
> - **§1.7 is the demo contract** for R4's target outputs. Budget: **3h build / 2h rehearsal** (authorized deviation from Convention 6's nominal final-4h). D1 rides the `M4-ingest` merge; no contract changes are planned, so the validator stays 6/6 throughout.

## 3. Per-module refactor (what each module must do this build)

Conventions that bind every lane: **shape stability** (add keys, never rename/drop — rule 3) · **fail-closed** (rule 6) · **guards flip with stubs in the same commit** (rule 7) · **no new dependencies** (rule 9) · **attestor never weakened** (rule 5 / Conv 8) · **dual-mode survives** (rule 4).

### M1 — Contracts + validator — FROZEN, no active owner
- No schema changes this build. If a lane needs a boundary-crossing field: schema + fixture + pair in the **same** change (rule 1) — escalate to baron, since no M1 owner is assigned.

### M2 — Fixtures — GiGi (acting, one addition only)
- Add `fixtures/demo_payload.json` = the §1.7 injected body (`action: opened`, `pr: 142`, `requirement` with AC-1/AC-2, `diff_paths: ["src/refund.py"]`). One writer (§0.4) — nobody else touches `fixtures/`.
- §11.15 note: the traceability fixture's `E4`/`E2` is **correct** (PR #43 + §1.7); the stale side is the test.

### M3 — Pydantic mirrors — Aixxn (inside the M4 merge)
- Main's Finding mirror (`3f8fa25`) **wins** over the branch's `0cac970`; re-apply the branch's guard rework only where additive.
- Fix `test_demo_traceability_fixture_loads_into_model`: `E0` → `E4`/`E2`, with the commit stating why (closes §11.15 — the only known red).
- §11.12's three unguarded enum fields: out of scope unless green early (pattern exists — one line per field).

### M4 — Stage 1 Ingest — Aixxn (merge)
- Land `gates/ingest.py` + `test_ingest.py` as written (real bundle: `requirement` passthrough, measured `files[{path, sha256}]`, traversal/symlink/FIFO refusals). M5 depends on `requirement` flowing through — verify that key survives the merge.

### M5 — Stage 2 Extract — baron (R4)
- Real deterministic parsing: split `requirement` on `AC-\d+:` → `criteria[{criterion_id, text, testable: true}]`; untestable criterion dropped **with a reason**. No LLM in this stage, by spec.
- Flip `test_gates.py`'s extract exact-equality stubs in the same commit.

### M6 — Stage 3 Parse — baron (pass-through)
- Stay stub-shaped. Map criteria to criterion-anchored `ast[]` (`criterion_id`, `kind`, `node`); no model in this loop, per spec. Add keys only.

### M7 — Stage 4 Verify — stub-shaped, mock-backed
- No real probes (XL — out of scope). Emit the §1.7 demo findings (`AC-2 / ERROR_PATH / refuted / src/refund.py:88 / no retry path`) under **mock mode with provenance stated in the runbook** (Convention 4). Never claim live analysis in a rationale string.

### M8 — Stage 5 Adjudicate — baron (R4)
- Real ladder aggregation per §1.4 as ratified by D1 (rides the M4 merge): `CERTIFIED` requires ≥E4; `CONDITIONAL` for E2–E5 with ledger remainder; `REJECTED` on any refutation (any tier); else `PENDING`. Target: AC-1 `CERTIFIED`@E4 + location, AC-2 `REJECTED`@E2 + location. Flip adjudicate guards in the same commit.

### M9 — Stage 6 Emit + gate — baron (R4)
- Derive `exit_code` (**0 iff overall CERTIFIED, else 1**, §1.5) — replaces the current always-1 as a *derived* value; undecided paths keep the fail-closed default. Emit the run envelope (§1.2) + traceability matrix + artifact pointer; exposure stays `{null, false}` (harness dropped).

### M10 — Orchestrator — Cody (R1)
- `enqueue_run` persists a `queued` row **and** `submit()`s; `worker()` starts from the app lifespan (Cody holds `main.py` this session — M15's file, per spec); `run_pipeline` writes the run row + `write_artifact` + flips `status`; a stage raise stores a **blocking** failure (rule 6); keep `_queue` clean between tests. **Flip the two unwired-queue characterization tests in the same change** (rule 7).

### M11 — LLM layer — Aixxn (inside the merge)
- Land `select_client()` (`llm/__init__.py` — conflict-free vs `main`); `.env` sets `MOCK_LLM=true` for demo/CI; default stays **live/fail-closed** (branch design); live client keeps raising past the key check (no half-implemented client); no third client (pinned test).

### M12 — Attestor — no changes
- Read-only policy already enforced at worker startup on `main`. Nobody touches `policy.py` this build (rule 5).

### M13 — Metric + harness — DROPPED (D-a)
- Delete the branch at Phase 0. Harness ACs superseded. `false_certified.py`, its tests, the exposure contract, the validator pair, and the `/api/metrics` stub all stay as-coded.

### M14 — Persistence — no changes
- Callers arrive from Cody's R1/R2. Nobody edits `db.py` or `store/` this build. CWD relativity stays as the recorded limitation — GiGi's HTTP-mode CLI is designed around it.

### M15 — API surface — Cody (R2)
- `GET /api/runs` = real rows, newest-first; `GET /api/runs/{id}` = envelope + artifact pointers with **404** on unknown (today it echoes any id); `/api/metrics` stub conformance only; **`_dist` two-level fix + a mount test**; flip the three stub-response tests; route-table test stays green. HMAC (D7) and GitHub write-back (D13) deferred.

### M16 — Dashboard — FE dev (R7)
- Phase-0 first: `npm install && npm run build` (never run before — longest unknown, surface it early). Fix the **`VerdictBadge` lowercase-`status` defect** (renders orange = undecided — demo-breaking). **Remove `<ExposureCard>`** (D-b; leave `ExposureCard.jsx` on disk). Delete `frontend/src/fixtures.js`, read `public/` (M2's request, kills the triple-copy). Prove **live** render: AC-1@E4 green, AC-2@E2 red, **no fixture-mode banner** (rehearsal exit criterion).

### M17 — Test suite + CI — every lane, continuous
- Rule 7 everywhere (listed per module above). Zero live LLM calls (`live_llm` stays unselected). `tmp_path` discipline. No suite-wide work planned; full run (3.11.9 + 3.12.14) + validator at Phase 3.

### M18 — Runbook + Bob integration — GiGi
- `scripts/attest.py` (stdlib/`httpx` only): HTTP mode — POST payload → poll run → print verdict + traceability → **exit with the run's `exit_code`**; `--direct` in-process fallback. `fixtures/demo_payload.json` (§1.7 body). **Phase-0 first:** Bob installs, credits active, one agent command executes.
- Append the runbook to `modules.md` §M18 **after the M4 merge lands** (contended file — sequenced in Phase 2). Runbook must be executed by FE dev (didn't write it — M18 AC); demo moment = **invoke only**.

## 4. Sequence (clock starts at "go")

| Phase | Min | Parallel first actions |
|---|---|---|
| **0 — Health** | 0–15 | baron: delete harness branch · Aixxn: start M4 merge · FE: `npm install` · GiGi: **Bob check** · Cody: baseline suite |
| **1 — Build** | 15–60 | five lanes per §3 ownership; Aixxn's merge lands by 60 or the cherry-pick fallback fires |
| **2 — Integrate** | 60–120 | baron merges each lane as it goes green; conflicts surface early |
| **3 — Prove** | 120–160 | cold end-to-end (server → Bob CLI → dashboard) + full suite/validator both legs; fix fallout |
| **4 — Freeze** | 160–180 | code freeze; runbook dry-run by FE dev |
| **5 — Ship** | 180–300 | 3 rehearsals · fallback video (Conv 6) · submission artifacts · `/end` doc pass (session logs + record the harness pruning) |

**Explicitly out of scope:** mutation harness & any measured exposure · live watsonx (model id unprovisioned) · M7 real probes · GitHub write-back (D13) · HMAC (D7) · SSE/auth · **Figure 6 — do not show** (§11.11: three false claims, no committed generator) · receipt-renderer PR #26.
