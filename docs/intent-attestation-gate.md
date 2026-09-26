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
| 1 | Ingest | issue / spec / PRD / test matrix / diff — Bob reads PDF/DOCX/XLSX/images natively |
| 2 | Extract criteria | atomic acceptance criteria, quality-gated against ISO/IEC/IEEE 29148; unverifiable criteria rejected outright |
| 3 | Parse deterministically | cucumber/gherkin → AST; **no model in the extraction loop** |
| 4 | Verify in parallel | N independent `bob run` processes (one per criterion group) — Bob Shell has no native subagent fan-out |
| 5 | Adjudicate | E0–E6 evidence ladder → CERTIFIED / CONDITIONAL / REJECTED |
| 6 | Emit and gate | traceability matrix, signed verdict record, review-debt ledger, risk-weighted exposure; non-zero exit blocks merge |

**Probe model (§3.2):** 5 static probes per criterion — `CODE_SEARCH`, `LOGIC_TRACE`, `STATE_CHECK`, `ERROR_PATH`, `ABSENCE_CHECK` — plus an adversarial pass across 7 failure classes (boundary · omission · contradiction · implicit · negative · concurrency). Taxonomy extracted from the MIT-licensed `attest` skill.

**Governance by construction (§3.3) — the differentiator:** verifier runs under a Bob custom mode (`attestor`) granting read/subagent/skill/workflow and **withholding edit and execute entirely** — structurally incapable of modifying what it verifies. Answers the Delve-style "fabricated evidence" failure mode with architecture, not policy. Direct IBM read-only-custom-mode governance angle.

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
