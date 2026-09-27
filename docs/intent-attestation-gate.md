# docs/intent-attestation-gate.md — Intent Attestation Gate (module record)

Append-only module record for the new hackathon idea. Design doc status: **none** — the
single source is `IBM BOB.pdf`, Adrian's proposal (pp. 14–25). This file holds only the
distilled facts needed to plan without re-reading the PDF, plus the session log.

## Source

- `IBM BOB.pdf` → "ADRIAN IDEA" section, pages 14–25 (§1 Problem → §4 Workflow + Figures 1–2)
- Full text extracted for analysis at `/tmp/opencode/ibm-bob.txt` (session temp — never committed to docs/)
- Tagline: *"Anyone can check that the code is well-made. Nobody is checking that it's the right code."*
- Positioning: an independent, model-agnostic verification layer for AI-generated software, plus a spec-mutation benchmark nobody else can publish. **Not** an AI code-review bot (§1.4 rules that out — crowded market, no independent exit, Bob already ships Review).

## Problem (§1)

The market only asks "is this diff internally correct?"; nobody asks "does this change do what the ticket asked for?" — a measurement blind spot, not a feature gap. Three compounding failures:

1. **Supply/demand inverted** — CircleCI Feb 2026 (28M workflows): feature-branch throughput +15%, main-branch −7%, main-branch success 70.8% (5-yr low).
2. **Review is evicted, not delayed** — 52.8% of bot-reviewed PRs get zero human activity; 84% have no human reviewer besides the author; +31% PRs merging with zero review (2025→2026); Anthropic's own substantive-review coverage was 16%.
3. **Verification is structurally blind to intent** — no tool exceeds 63% recall (30% on 1k+ line PRs); the only independent benchmark's ground truth is built from human review comments and post-review changes — neither ever asks if the PR matches the ticket.

Do-not-claim list (§2.5): METR 19% (retracted), "AI is a thief of time" (not DORA's phrase — it's "verification tax"), 1.5T lines of COBOL (misreading), "mainframes are dying" (Forrester contradicts).

## Solution (§3) — a gate that emits evidence, not a reviewer

Six stages:

| # | Stage | Notes |
|---|---|---|
| 1 | Ingest | issue / spec / PRD / test matrix / diff — watsonx.ai (the integrated LLM) reads PDF/DOCX/XLSX/images natively — bob.ai fully replaced |
| 2 | Extract criteria | atomic acceptance criteria, quality-gated against ISO/IEC/IEEE 29148; unverifiable criteria rejected outright |
| 3 | Parse deterministically | cucumber/gherkin → AST; **no model in the extraction loop** |
| 4 | Verify in parallel | N independent workers (one per criterion group), each calling watsonx.ai for LLM reasoning — fan-out is N OS processes, not model-invoked subagents |
| 5 | Adjudicate | E0–E6 evidence ladder → CERTIFIED / CONDITIONAL / REJECTED |
| 6 | Emit and gate | traceability matrix, signed verdict record, review-debt ledger, risk-weighted exposure; non-zero exit blocks merge |

**Probe model (§3.2):** 5 static probes per criterion — `CODE_SEARCH`, `LOGIC_TRACE`, `STATE_CHECK`, `ERROR_PATH`, `ABSENCE_CHECK` — plus an adversarial pass across 7 failure classes (boundary · omission · contradiction · implicit · negative · concurrency). Taxonomy extracted from the MIT-licensed `attest` skill.

**Governance by construction (§3.3) — the differentiator:** verifier runs under a read-only `attestor` policy granting read/subagent/skill/workflow and **withholding edit and execute entirely** — structurally incapable of modifying what it verifies — with all LLM reasoning via **watsonx.ai**. bob.ai is fully replaced: not the model, not the harness — no `bob run`, no Bob custom-mode syntax, no Bobcoins. Answers the Delve-style "fabricated evidence" failure mode with architecture, not policy. Direct IBM read-only-custom-mode governance angle.

**Emitted artefacts (§3.4):** per-criterion verdict record · bidirectional traceability matrix · review-debt ledger · risk-weighted exposure (per repo/capability, decay curve) · signed hash-chained evidence record.

**Publishable metric (§3.5):** `FALSE CERTIFIED RATE = P(CERTIFIED | spec violation present)` — measured by injecting known defect operators into real acceptance criteria, reported per operator class across 7 spec-mutation classes (boundary drop, comparison inversion, threshold weakening, error-path deletion, normative demotion, negative-constraint removal, untestability). Corroborating ground truth: Stryker "Survived" mutants. The claim: publish a metric the existing leaderboard structurally cannot contain.

**Defensibility:** primitives are free/MIT (`attest`, Stryker, cucumber/gherkin, Martian harness), but the moat = vertical corpus of regulator-grade acceptance criteria + an evidence format an auditor accepts.

## Session log (append-only)

### 2026-09-26 — Session 6: migration from AI Quality Gates
- Pivot confirmed by user to Adrian's Intent Attestation Gate (evaluated 🥇 in Session 5).
- **Removed** all old-idea artifacts: `hackathon-idea.md`, `README.md`, `planing-transcript.md`, pipeline + architecture diagrams & generators, `contracts/`, `fixtures/`, `scripts/`, `docs/architecture.md`, `docs/contracts.md`. Safety backup: `/tmp/opencode/old-idea-backup-2026-09-26.tar.gz` (31 files).
- **Kept:** `AGENTS.md`, `IBM BOB.pdf`.
- Adrian's proposal extracted (`pdftotext`) to `/tmp/opencode/ibm-bob.txt` and distilled into this record.
- No design doc recreated (per user); this module record + the PDF are the sources until re-planning happens.
- **Next:** re-plan scope/workstreams/conventions for the new idea (contracts, fixtures, architecture, demo repo all need rebuilding from scratch).

### 2026-09-26 — Session 7: Figure 6 verification + patch
- Verified `docs/Figure-6-System-Architecture.png` against this record via subagent (`subagent/coder`): all 6 stages covered (Ingest → Extract → Deterministic parse → Parallel verify → Adjudicate E0–E6 → Emit+gate), `attestor` mode correct (read/subagent/skill/workflow, edit+execute absent), Budget Governor metering, traceability/signer/ledger/exposure/receipt surfaces present.
- **Gaps kept as-is (match original):** FALSE CERTIFIED RATE + 7 spec-mutation classes appear nowhere in the figure; fleet flags string says `--disable-subagents` while the attestor box grants `subagent` (footer note explains: N OS processes, not subagents).
- **Patched via new generator** `gen_fig6_architecture.py` (repo root, stdlib + matplotlib only, fails loudly on overflow; output 1920×1400 RGBA): `THE CONSTRAINT` → padded pill callout above Budget Governor; meter note → dark-on-white 2 full lines above fleet box; `THE NUMBER` → padded pill callout above Review-Debt Ledger; layer-3 arrow moved into gaps; fleet flags right-aligned with padding. Original backed up at `/tmp/opencode/fig6-backup/Figure-6-System-Architecture-orig-2026-09-26.png`.
- **Open:** user finds the diagram unclear — no per-module connecting lines (only left-gutter layer arrows; decomposition map, not data-flow). Proposed spine + numbered S1–S9 edge badges; pending user go (`add lines`).

### 2026-09-26 — Session 9: watsonx.ai correction — edits landed (resolves Session 8 pending)
- Admin correction applied per `/start` instruction: **bob.ai is NOT the integrated LLM — use watsonx.ai instead** (resolves the Session 8 "edits pending" entry below, kept for audit trail).
- Updated Stage 1 (Ingest via watsonx.ai), Stage 4 (N workers calling watsonx.ai, not `bob run`), and §3.3 (read-only `attestor` policy + watsonx.ai for all LLM reasoning; Bob harness-only if retained, never the model).
- `AGENTS.md` Bob-as-LLM references updated in the same session; Figure 6 generator (`gen_fig6_architecture.py`) + PNG flagged for the same correction, not yet regenerated.

### 2026-09-26 — Session 8: LLM correction bob.ai → watsonx.ai (Start + End, edits pending)
- `/start` executed with admin correction: **bob.ai is NOT the LLM to integrate — use watsonx.ai instead**. Target module confirmed as this record + `AGENTS.md` Bob-as-LLM references.
- Flagged correction targets (no edits landed this session): Stage 1 "Bob reads PDF/DOCX...", Stage 4 "N independent `bob run` processes", §3.3 "Bob custom mode (`attestor`)", Session 7 log attestor/Budget Governor lines; `AGENTS.md` AI-runtime line, Conventions 7–8, `attestor` syntax-spike open decision.
- Working interpretation for next session: **watsonx.ai = LLM backend for all verification reasoning; Bob (if retained) = agent shell/harness only, not the model**. Open question carried forward: is Bob still the harness or fully replaced by watsonx.ai?
- Next: apply the approved rewrite (watsonx.ai as LLM backend, clarify Bob's remaining role if any) to this record + `AGENTS.md`, then continue re-planning.

### 2026-09-26 — Session 10: fully replace bob.ai (not the model, not the harness)
- User instruction: fully replace bob.ai. Supersedes the Session 9 "harness-only if retained" wording.
- Body updated: Stage 1 (bob.ai fully replaced), §3.3 (no `bob run`, no Bob custom-mode syntax, no Bobcoins; all LLM reasoning via watsonx.ai). Stage 4 already clean (N workers calling watsonx.ai).
- `AGENTS.md` runtime line, Convention 7, and open decisions stripped of Bob-harness/Bobcoins fallbacks; spend/burn plan is watsonx.ai only.
- `gen_fig6_architecture.py` de-Bobbed (spend cap subtitle, N workers, attestor-policy flags, WATSONX_API_KEY, attestor-policy config) and Figure 6 PNG regenerated; prior PNG backed up to `/tmp/opencode/fig6-backup/`.
- Untouched on purpose: historical session-log lines naming Bob (audit trail) and market-research dossiers describing the IBM Bob product as a competitor/channel.

### 2026-09-27 — Session 11: frontend + backend file scaffold (branch `baron`, commit `617a134`)
- `/start` goal: setup the file scaffold for frontend and backend. Zero code existed; scaffold-only, no gate logic implemented.
- **Backend (`backend/`, FastAPI modular monolith, 33 files):** `app/main.py` (serves API + built Vite `dist/` when present), `config.py`, `db.py` (SQLite WAL), `routers/` (`webhooks.py` POST /webhooks/github with injected-payload fallback, `runs.py` GET /api/runs + /{id}, `metrics.py` GET /api/metrics), `orchestrator/` (`pipeline.py` 6-stage chain, `jobs.py` asyncio queue), `gates/` (6 fixture-shaped stubs: ingest/extract/parse/verify/adjudicate/emit), `models/schemas.py` (Pydantic mirrors `contracts/`), `store/artifacts.py` (hash-chained JSON), `llm/` (`watsonx_client.py` spike target + `mock_client.py` zero-spend fallback), `attestor/policy.py` + `attestor/sandbox.py` (5 grants = 4 harness groups + `llm_egress`, DENIES edit/execute, `resolve_worker_caps`/`assert_read_only`/`policy_record`, and the workspace write-probe that distinguishes a read-only mount from a missing write bit), `metrics/false_certified.py` (7 operators + rate fn), `tests/test_scaffold.py`, `requirements.txt`, `.env.example`.
- **Frontend (`frontend/`, React+Vite, 12 files):** `package.json` (react 18, vite 6 — not yet `npm install`ed), `vite.config.js` (API proxy → :8000), `App.jsx` (live-API first, fixture fallback + fixture-mode badge), `api.js`, `fixtures.js`, 4 components (VerdictBadge, TraceabilityMatrix, EvidenceLadder, ExposureCard), `public/fixtures/demo_run.json`.
- **Contracts/fixtures/scripts:** 6 schemas (`contracts/`: run, verdict, criterion, traceability, exposure, findings), 4 examples (`contracts/examples/`: verdict, criterion, exposure, findings) + 2 fixtures (`demo_run`, `demo_traceability`), `scripts/validate_contracts.py` (stdlib + jsonschema only).
- **Verified green:** `pytest backend/tests` 3 passed; validator OK ×2; pipeline stub returns `exit_code: 1` (gate blocks by default); FastAPI import OK.
- Committed to new branch `baron` as `617a134` (53 files, +584); pre-existing Sessions 9–10 working-tree changes deliberately left unstaged (landed separately as `56c2911` by another session). Branch not pushed to `origin`.
- **Next:** implement gates depth-first (adjudicate + metric), watsonx.ai auth/call-pattern spike, `npm install` + wire dashboard live.

### 2026-09-27 — Session 12: Figure 6 generator repair + `56c2911` commit to `baron`
- Found `gen_fig6_architecture.py` unrunnable after the Session 10 de-Bobbing (5 trailing-`,,` SyntaxErrors); fixed all five, finished attestor-box terms (`attestor policy`, `allows:`, `DENIED`), regenerated the PNG with the generator's own overflow check green (new md5 `aeb47178`).
- Removed a mislabeled self-made backup (md5-identical to the new PNG, not pre-change); genuine Bob-era PNG still at `/tmp/opencode/fig6-backup/Figure-6-System-Architecture-orig-2026-09-26.png`. Generator verified with zero `bob` matches.
- Secret scan clean; committed 14 files as `56c2911` on the pre-existing `baron` branch (not pushed to `origin`).
- Live parallel work deliberately untouched: uncommitted `docs/architecture.md`, working-tree `D gen_fig6_architecture.py` (preserved in `56c2911` history regardless), `__pycache__/` dirs.
