# AI-Assisted Developer Workflow Tooling: Code Review, Validation, Release Readiness

**Competitive & venture dossier — compiled 26 September 2026**

All claims carry a source tag:
- **[F]** = primary source (vendor docs, company announcement, official blog, filing, benchmark repo)
- **[S]** = secondary source (trade press, aggregator, analyst note) — treat as unconfirmed unless two sources agree
- **[SPEC]** = my inference. No source. Explicitly labelled.

Anything pre-2025 is tagged **[BASELINE]** per the AI-wave framing.

---

## TL;DR / Bottom Line

1. **The generic "AI code review" category is closed and consolidating.** $1.5B (CodeRabbit), $120M raised (Qodo), $231M raised (CodeRabbit total), Graphite acquired by Cursor, Gemini CLI killed, Continue.dev killed, Charlie Labs shutting down. A well-funded independent entrant that sells "AI reviews your PRs" is not viable in 2026.
2. **The measurable technical gap is not "find bugs in a diff."** No tool exceeds 63% recall on human-verified issues; on 1k+ line PRs aggregate recall drops to 30%. But *diff-scoped bug-finding is what everyone already does* — the scored differentiator is retrieval, and retrieval is being commoditized (Augment shipped its context index as a free MCP server in Feb 2026).
3. **The two genuinely unserved things are (a) verifying a change against the original requirement/acceptance criteria, and (b) quantifying "review debt" — the accumulating mass of AI-generated code merged with no human verification.** Neither is scored by any benchmark. Neither is a funded category. 52.8% of bot-reviewed open-source PRs get zero human response after the bot comments. **[F]**
4. **IBM is simultaneously the best channel and the biggest competitor in this space.** watsonx Orchestrate's Agentic Control Plane + Agent Connect is a real, open, documented distribution surface (MCP/A2A, published partner catalog, IBM-led GTM). But IBM Bob Premium Package for Z shipped GA on 9 July 2026 and already owns COBOL/PL-I modernization, business-rule extraction, and deterministic equivalence testing. **[F]**
5. **Verdict on viability:** viable *only* as an adjacent wedge with a compliance or data moat. Not viable as a horizontal AI code review product. Not scalable on per-seat pricing — the two largest players in the category both abandoned per-seat in 2026.

---

# 1. The Direct Competitive Set — AI Code Review / PR Review

## 1.1 The three that matter

| Company | What it actually does | Funding (date) | Valuation | Customers / scale | Pricing | Segment |
|---|---|---|---|---|---|---|
| **CodeRabbit** | PR review bot; pivoted Aug 2026 to "**Agentic Change Management**" = Triage (PR risk/value routing) + Change Stack (decompose large agent diffs for humans) + Security (post-ship scanning) | **$143M Series C, 12 Aug 2026** (Atomico + Smash Capital co-lead; BMW i Ventures, Datadog, Hirtle Callaghan new). Preceded by $60M Series B (16 Sep 2025, Scale Venture Partners + NVentures) and $16M Series A (Aug 2024, CRV). **Total ~$231M** | **$1.5B** post (Series C); ~$550M at Series B **[S]** | **17,000+ customers**; **>2M reviews/week**; 8,000+ *paying* (Sep 2025); 150,000+ OSS projects. NVIDIA, BMW, Adyen, Indeed, JFrog, trivago, NVIDIA, Adyen, Campfire | ~$12–24/dev/mo **[S]**; **$10M+ committed to keep OSS free for 12 months** | Enterprise + PLG funnel. SOC 2 Type 2, GDPR |
| **Qodo** (Codium Ltd, founded 2018) | "Code review and governance layer." Multi-agent (bug detection / compliance checks / architectural validation) + coordinating layer that filters and prioritizes. Qodo 2.2 draws on full-repo signals **including codebase history and prior PR decisions** | **$70M Series B, 30 Mar 2026** (Qumra Capital; angels incl. Peter Welender/OpenAI, Clara Shih/Meta). Preceded by $40M Series A (30 Sep 2024, Susa + Square Peg). **Total $120M** | Not disclosed **[S: PitchBook masks it]** | Walmart, NVIDIA, Red Hat, Box, Intuit, Ford, Monday.com, TUI Group (named testimonial). **Enterprise footprint 11x YoY** | **Credit-based, $0.012/credit**; packs ≈ 18/36/144 reviews-mo. Enterprise (30+ users): SSO/SAML, BYOK, single-tenant or on-prem, CSM | Enterprise-first. Claims #1 on Martian offline Code Review Bench (F1 50.3%) and #1 Gartner Critical Capabilities for AI Assistants **[S: vendor claim]** |
| **Greptile** | Agentic reviewer with full-codebase graph context; v3 = full architecture rewrite, claims 3x more critical bugs than v2. v4 (Mar 2026) + **TREX**, a runtime validation agent that writes and runs its own tests against a PR | **$25M Series A, 23 Sep 2025** (Benchmark; Eric Vishria to board). $4.1M seed 2024 (Initialized). **Total ~$29–30M** | **~$180M** reported **[S: TechCrunch, Jul 2025]** | **2,000+ teams**; 1B+ LOC reviewed. Brex, Substack, Retool, Klaviyo, **NVIDIA**, Scale, PostHog, Zapier, WorkOS, Mintlify, YC internal | **$30/dev/mo incl. 50 reviews**, then **$1/review overage** (introduced Mar 2026) | Enterprise + YC/SMB. **Self-hosting is the commercial unlock** — air-gapped, customer's own AWS + own LLM, SOC 2 |

Sources: [CodeRabbit Series C](https://www.coderabbit.ai/newsroom/coderabbit-series-c-agentic-change-management) · [Reuters](https://www.reuters.com/technology/ai-code-review-platform-coderabbit-valued-15-billion-latest-funding-round-2026-08-12/) · [CodeRabbit Series B](https://www.businesswire.com/news/home/20250916401011/en/) · [Qodo Series B](https://siliconangle.com/2026/03/30/ai-generated-code-verification-startup-qodo-raises-70m/) · [Qodo PR](https://financialpost.com/globe-newswire/qodo-raises-70m-to-accelerate-fight-against-software-slop-from-openclaw-and-claude-code) · [Greptile Series A](https://www.greptile.com/blog/series-a) · [Greptile on Martian bench](https://www.greptile.com/content-library/greptile-martian-code-review-benchmark) · [Qodo pricing](https://www.qodo.ai/pricing/)

**Revenue reality check:** CodeRabbit ARR tracked at $15M (Sep 2025) → $40M (late Jun 2026) → "nearing $100M with 50% growth in Q2" (Aug 2026) by ARR Club **[S — an ARR tracker, not audited; CodeRabbit itself only said "revenue grew more than 5x year-over-year" without a base]**. At $1.5B on ~$100M ARR that is ~15x forward, against a cited total code review services market of $3.04B in 2026 **[S: 360iResearch via TFN]**. Two independent critics made the same point: *TNW* and *TFN* both note the valuation is roughly half the entire market CodeRabbit sells into.

## 1.2 The hyperscaler / IDE incumbents

| Product | Owner | Status | Scale | Pricing | Note |
|---|---|---|---|---|---|
| **GitHub Copilot code review** | Microsoft/GitHub | **GA 4 Apr 2025**; moved to **agentic tool-calling architecture on GitHub Actions, 5 Mar 2026** | **12,000+ orgs** auto-review every PR; **60M+ reviews**; **>1 in 5 of all code reviews on GitHub**; 1M+ devs in first month | Bundled into Pro $10 / Pro+ / Business $19 / Enterprise $39. **Moved to usage-based "AI credits" 1 Jun 2026** (1 credit = $0.01, per token). Lite vs Balanced effort tiers | Effectively the category's floor. Free-to-paid tier of a suite people already buy. Also ships **usage metrics API** for Copilot-reviewed PRs (Apr 2026) — GitHub is building the measurement layer too |
| **Cursor Bugbot** | Cursor (Anysphere) | Launched Jul 2025; **fully agentic architecture autumn 2025**; **moved off per-seat 11 May 2026** | **2M+ PRs/month**. Rippling, Discord, Samsara, Airtable, Sierra. PlanetScale: 2,000+ PRs/mo, 80% resolution rate, "2 FTE of review effort saved" | **Was $40/seat/mo. Now usage-based, $1.00–$1.50 average per run.** Existing customers migrated at first renewal after 8 Jun 2026 | The most important pricing datapoint in the dossier — see §4. Effort levels (Default/High/Custom) are a **Teams-only** feature gated on usage billing |
| **Gemini Code Assist / Antigravity** | Google | Gemini CLI **closed to individual accounts 18 Jun 2026**, replaced by Antigravity CLI (**no public repo**, 107k-star project orphaned). Enterprise licences retained | — | — | Direct evidence that even a hyperscaler will kill a dev tool |
| **OpenAI Codex** | OpenAI | Review connector; **reviewed 220,000 PRs in two months** | Top-2 on Martian online bench (F1 59.4%) | Credits/usage | Also **losing Cursor as a customer** — OpenAI cut Cursor's model access effective **12 Nov 2026** following SpaceX's $60B acquisition of Anysphere **[S: Renascence]** |

Sources: [GitHub Blog 60M reviews](https://github.blog/ai-and-ml/github-copilot/60-million-copilot-code-reviews-and-counting/) · [Copilot agentic GA](https://github.blog/changelog/2026-03-05-copilot-code-review-now-runs-on-an-agentic-architecture/) · [Copilot GA Apr 2025](https://github.blog/changelog/2025-04-04-copilot-code-review-now-generally-available/) · [Bugbot billing](https://cursor.com/help/account-and-billing/bugbot-usage-based-billing) · [Bugbot changelog Jun 2026](https://cursor.com/changelog/bugbot-updates-june-2026) · [Gemini CLI shutdown analysis](https://www.uniflow.kr/en/gemini-cli-shutdown-what-it-taught-us/)

## 1.3 The rest of the field

| Company | Status | Funding | Pricing | Segment | Verdict |
|---|---|---|---|---|---|
| **Graphite / Diamond** | **ACQUIRED by Cursor, announced 19 Dec 2025.** Operated independently through 2026; AI Reviewer being merged with Bugbot | $52M Series B Mar 2025 (Accel + Anthropic Anthology Fund + Menlo + a16z). Last private valuation **~$290M**; Axios reported Cursor paid "way over" that | ~$15–20/active committer **[S]** | Enterprise (Shopify, Snowflake, Figma, Ramp, Perplexity, 500+ cos) | **Exit signal.** The #2 well-funded independent review platform got bought for the agent that already had a reviewer |
| **Augment Code** | Context Engine (400k+ files, sub-200ms, real-time index) + code review agent. **Shipped Context Engine as a standalone MCP server 6 Feb 2026** | $252M raised, **$977M valuation** **[S: Ry Walker]** | Credit-based from $20/mo | Enterprise, SOC 2 Type 2 + ISO/IEC 42001 | **The commoditization canary.** A ~$1B company gave away its index so any agent could use it. Claims #1–2 on Martian offline; 70% win rate vs Copilot (self-reported) |
| **Baz** | Review that starts at the *planning* stage, not the diff. **#1 on precision-weighted Code Review Bench.** Enterprise self-host offered | **$17M total** ($9M extension 29 Jun 2026; Battery Ventures + Boldstart co-lead, AFG, Disruptive) | Custom | Enterprise/regulated | Interesting: attacks the earliest possible interception point |
| **Gitar** | Exited stealth Apr 2026. AI agents for code validation/quality; custom security & maintenance agents. Founded by **Ali-Reza Adl-Tabatabai** (ex-Fabric, Sift) | **$9M** (Venrock lead, Sierra Ventures) | n/d | Enterprise | Well-credibled early entrant in the validation layer |
| **Kodus** | Open-source (AGPLv3) self-hosted reviewer, BYO key, **zero markup on tokens**, no source storage. Explicit CodeRabbit comparison table | ~$60K seed **[S]** | Self-host free; cloud BYOK | **Sovereign/regulated, OSS** | Small, but the clearest expression of the "sovereignty wedge" thesis (§4.3) |
| **Cubic** (YC S2025) | Reviewer + human-review UI (logical file ordering, architecture diagrams) | YC | Freemium | SMB/mid | cal.com, n8n, Linux Foundation. **#3 on Martian online, F1 58.7%** |
| **Ellipsis** | Review + fix; **executes the code it generates** (a reviewer that tries its own fix) | $2M seed Jun 2024 (YC W24) | n/d | SMB/mid | 90+ cos, 9,300+ devs, 29K codebases (2024) |
| **CodeSheriff** | AI code safety scanner for AI-generated code, self-improving via autotune | None found | n/d | n/d | F1 64.6% on Martian offline (Opus 4.5 judge) — **highest published offline F1 in the repo**, submitted Apr 2026 |
| **StarSling** (Bessemer + YC) | **Review runners inside GitHub Actions**; per-area reviewers (security/API/tests/DB); customer brings model key | **$3M pre-seed, 22 Sep 2026** | **$0.004/min** 2-vCPU runner + customer pays model provider directly | SMB / dev infra | Early access. Notable because it sells *infrastructure*, not AI — sidesteps the seat problem entirely |
| **Sourcegraph** | Enterprise code intelligence, Cody, **Deep Search** (agentic code search, Lua sandbox, no network) | Late-stage | Enterprise/BYOK | Enterprise | Deep Search is Enterprise-only, **not available to BYOK customers** — BYOK is a downgrade |
| **SonarQube / SonarCloud** | **[BASELINE: static analysis since 2008]**, now AI CodeFix (GA 31 Jul 2025), "Ask Gitar" agent, **Sonar Vortex** (constrain agents in the inner loop), MCP server + agent plugins for Claude Code/Gemini/Kiro | Late-stage | SonarQube from $34/mo (LOC-based). **Sonar Agent $20–25/user/mo, $40/user/mo premium**, Enterprise custom (BYOK, self-hosted) | Enterprise | 40+ languages incl. **ABAP, COBOL, JCL, RPG, PL/I**. The most credible *incumbent* answer, and it has the mainframe language coverage |
| **Codacy** | Cloud code quality + AI Reviewer + merge gates + **AI Inventory / AI Risk Hub** | — | **$18–21/dev/mth** | SMB/mid | AWS Marketplace. Explicit quote on site: "SonarQube's pricing changed, so we needed an alternative" |
| **DeepWiki** | Free AI-generated docs/architecture diagrams for any public repo (Cognition) | — | Free | OSS/dev | Documentation, not review |
| **DeepCode (Snyk)** | **[BASELINE]** acquired by Snyk; DeepCode AI folded into Snyk's product. Snyk also has an agent named "Gitar" surfaced inside Sonar — name collision worth noting | — | Bundled | Enterprise | |
| **Bito / Pieces / CodeSee / Trunk** | **[BASELINE]**. Bito still sells AI reviews. Pieces is local-first. CodeSee effectively dormant. Trunk is a merge queue | — | — | SMB | Pre-AI-wave. CodeRabbit/Sonar/Codacy have largely eaten this tier |
| **Ellipsis AI** (the distinct company from `ellipsis.dev`) | Note: there are **two** "Ellipsis" — `ellipsis.dev` (YC W24 code review) and Ellipsis AI. Search results conflate them. I could not find current Ellipsis AI code-review funding | — | — | — | **Flag: unresolved. Treat as low-signal.** |

Sources: [Graphite→Cursor](https://cursor.com/blog/graphite) · [Graphite blog](https://graphite.com/blog/graphite-joins-cursor) · [Axios](https://www.axios.com/pro/enterprise-software-deals/2025/12/19/cursor-buys-code-review-platform-graphite) · [Augment Context MCP](https://www.augmentcode.com/blog/context-engine-mcp-now-live) · [Augment review agent](https://www.augmentcode.com/blog/how-we-built-high-quality-ai-code-review-agent) · [Baz](https://siliconangle.com/2026/06/29/exclusive-agentic-coding-startup-baz-brings-code-reviews-planning-stage-extends-seed-funding-17m/) · [Gitar](https://theaiinsider.tech/2026/04/17/gitar-raises-9m-to-deploy-ai-agents-for-code-validation-and-software-quality-control/) · [Kodus self-host](https://kodus.io/self-hosted-ai-code-review/) · [Cubic YC](https://www.ycombinator.com/companies/cubic) · [StarSling](https://runtimewire.com/article/starsling-raises-3m-review-runners-code-review-agents) · [Sonar pricing](https://www.sonarsource.com/plans-and-pricing/) · [Codacy pricing](https://www.codacy.com/pricing) · [CodeSheriff bench PR](https://github.com/withmartian/code-review-benchmark/pull/24)

## 1.4 The independent benchmark — this is the most important artifact in the dossier

**Martian Code Review Bench** ([codereview.withmartian.com](https://codereview.withmartian.com/), [github.com/withmartian/code-review-benchmark](https://github.com/withmartian/code-review-benchmark)) — MIT-licensed, fully open (PRs, golden comments, judge prompts, pipeline). Self-describes as a "well-funded research lab that doesn't train models or sell coding tools."

- **Offline:** 50 PRs from 5 major OSS repos, human-curated golden comments with severity labels. 20+ tools evaluated. Judge models: Claude Opus 4.5, Sonnet 4.5, GPT-5.2. Scoring profiles Strict/Core/All, F-beta 0.5–3.0.
- **Online:** continuous sampling of **200,000+ fresh PRs/day** where review bots left comments. Ground truth = **what the developer actually fixed in post-review commits.** Updates daily, no training-data leakage.
- Design rationale (Feb 26 2026): SWE-bench was killed by OpenAI because frontier models reproduce gold patches from memory (they hired 93 engineers to audit; 59.4% of remaining hard problems had flawed tests). Code Review Bench's answer is an offline/online pair that cross-check each other.

**Current standings (online, 30 Jul 2026):** Greptile 60.8% F1 (P 76.2% / R 50.6%) · Codex 59.4% · Cubic 58.7% · Devin 58.6% · CodeRabbit 57.5%. Qodo cited #1 on offline at F1 50.3%; CodeSheriff submitted F1 64.6% offline (Opus 4.5).

**Five findings from this benchmark that should drive your strategy:**

1. **Nobody is close to solved.** *"no tool found more than 63% of the known issues. The best tool still missed a third of the bugs. The verifier is far from solved."* **[F]**
2. **Every tool collapses on large PRs.** Aggregate F1 drops 26.7% small→large. On 1k+ line PRs **aggregate recall falls to 30% — tools miss 70% of key issues.** Fullstack PRs score lowest for every tool. **[F]**
3. **Half of bot-reviewed PRs get no human response.** *"Over half of open source bot-reviewed PRs (52.8%) see zero human activity after the bot posts its review, and 84% have no human reviewer besides the PR author."* Codex: 220,000 PRs in two months, **only 4.6% had a human reviewer besides the author**. Solo-developer pattern: 96% of Codex repos, 92% Copilot, 91% Cursor. **[F]**
4. **Two distinct usage patterns, not one market.** Review-centric (CodeRabbit 60.5% engagement, 39% follow-up commits) vs. automated/agentic (Codex 33.2% engagement, 6.6% follow-up). Tool rankings **invert** depending on whether you filter for human engagement — Codex gains +17.2pp on engaged PRs, Claude *drops* -8.7pp. "Baseline scores are nearly meaningless to you." **[F]**
5. **The gold set is wrong, and that matters.** Real issues were being scored as false positives because the gold set omitted them — meaning **every tool's precision is understated and recall overstated**, and the magnitude "is large enough to change rankings." **[F]**

Sources: [Code Review Bench v0](https://withmartian.com/post/code-review-bench-v0) · [The Software Factory's Inspection Problem](https://withmartian.com/post/measuring-the-software-factorys-inspection-line)

---

# 2. Adjacent Categories — Saturation Verdicts

## 2.1 AI Testing / QA — **CROWDED. Do not enter.**

| Player | Status |
|---|---|
| **Momentic** | **$15M Series A, 24 Nov 2025** (Standard Capital lead, Dropbox Ventures; total $19.2M). Notion, Quora, Webflow, Xero, Bilt, SPS Commerce. 2B+ steps, 80,000+ PRs verified. **23 Jun 2026 launched an "agentic quality platform":** shared product knowledge base ingesting Jira/GitHub/Support/Slack, Explore Agent, Failure Classification Agent (real bug vs. intended change vs. flaky), **intent-based test format** |
| **mabl** | "AI native testing agent" (AI-native since 2017 **[BASELINE]**). Agentic authoring + managed QA workflows. G2 Leader in AI Testing |
| **KaneAI / TestMu** (LambdaTest) | Repositioned to "AI-agentic testing cloud" under TestMu branding. Multimodal agents reading diffs, tickets, docs |
| **Applitools, Autify, Testim, testRigor, TestSprite, BrowserStack AI, CueTest** | Fragmented middle. BrowserStack adds self-healing to existing Playwright/Selenium |

**Verdict: saturated and converging on the same primitives as code review (diff context, intent, self-healing).** Momentic's knowledge-base + failure-classification design overlaps directly with the "review debt" thesis in §5e — meaning the testing layer is already adjacent to it. Note Momentic's own framing: *"The constraint on shipping velocity used to be how fast developers could write code; but AI has changed that to be about how fast teams can verify it."* **[F]**

Sources: [Momentic Series A](https://techcrunch.com/2025/11/24/momentic-raises-15m-to-automate-software-testing/) · [Momentic platform launch](https://momentic.reportablenews.com/pr/momentic-launches-the-first-agentic-quality-platform-as-ai-continues-to-scale-code-output) · [mabl](https://www.mabl.com/) · [agentic testing comparison 2026](https://cuetest.dev/resources/best-agentic-testing-tools)

## 2.2 Legacy Modernization / Migration — **CROWDED, and now platform-owned.**

| Player | Position |
|---|---|
| **Amazon Q Developer: Transform** | GA for .NET, mainframe (COBOL→Java), VMware. Claims 4x faster .NET→Linux, up to 40% licensing savings. "Wave plans," hyper-graph decomposition, maintains functional equivalence. Customer: Novacomp (60% tech-debt decrease), Signaturit, DXC (80+ microservices) |
| **IBM Bob Premium Package for Z** | **GA 9 July 2026. Supersedes IBM watsonx Code Assistant for Z.** Built on **Z Understand** (static analysis across COBOL/PL-I/assembler/JCL → queryable repo, 10,000+ programs). Z Architect Mode (impact analysis, dependency assessment, business-context discovery), Z Code Mode, business-rule extraction + data dictionaries, **deterministic COBOL→Java with test cases generated from source behavior "to prove equivalence"**, repository-level `agents.md` enforcement, DBB on z/OS, Z Code Scan, IBM Debug. **Entitlement is sales-led; no self-serve.** Bob claims 20–40% faster delivery, 50–80% effort cut on structured workflows |
| **IBM Bob PP for i** | Announced 21 May 2026, released 24 Jun 2026. RPG/CL/SQL/COBOL, QSYS source members, fixed→free format conversion, business rule extraction |
| **IBM Bob PP for Java Modernization** | Same wave |
| **Moderne** | **$30M Series B, 11 Feb 2025** (Acrew Capital; Morgan Stanley, Amex Ventures, TIAA Ventures, Allstate, Intel Capital, True). **~$50M total.** OpenRewrite (Netflix-origin, Apache 2.0) Lossless Semantic Tree. **OpenRewrite is embedded in Amazon Q, GitHub Copilot, and Broadcom App Advisor** — i.e. the hyperscalers *use* Moderne's engine rather than compete with it |
| CAST Highlight, CodeScene, MethodJet | [BASELINE] + AI overlays |

Sources: [Bob PP for Z announcement](https://www.ibm.com/new/announcements/announcing-the-ibm-bob-premium-package-for-z) · [Bob architecture announcement](https://www.ibm.com/new/announcements/ibm-bob-expands-with-premium-packages-new-architecture-and-greater-enterprise-control) · [Bob for Z blog](https://bob.ibm.com/blog/bob-for-z-announcement/) · [IBM newsroom](https://newsroom.ibm.com/2026-07-09-ibm-advances-enterprise-ai-software-development-with-multi-agent-capabilities-and-specialized-modernization-workflows) · [Amazon Q Transform](https://aws.amazon.com/q/developer/transform/) · [Moderne Series B](https://www.globenewswire.com/news-release/2025/02/11/3024163/0/en/)

**Verdict: saturated, and the interesting competitive fact is structural — OpenRewrite is the shared substrate under Amazon Q, Copilot and Broadcom. You cannot win by being a better rewriter.** The only defensible position in this category is *verification of the rewrite*, which is exactly where Bob PP4Z is already investing.

## 2.3 SCA / Dependency Risk — **MATURED, not the frontier.**

Snyk, Mend, Black Duck, Sonatype, osv.dev, Dependabot are **[BASELINE]** and consolidating. The 2025-26 AI-native entrants (Endor Labs, Cybeats, Aikido) are **dependency-graph / SBOM-native**, not review-native. The genuinely new adjacent surface is **ML/model BOM and AI-component provenance** — but see §5d: the tooling for that is already free and open source (prompt-bom, ForgeProof, licit, squash, AIBoMGen). Sonar now bundles SBOM visibility and Cyber Resilience Act compliance at Enterprise tier. **[F]**

*Search gap flagged: I got a 429 from the search provider on Endor Labs/Cybeats/Aikido specifically. I did not confirm 2025-26 round sizes for these three. Treat as unresearched.*

## 2.4 Engineering Intelligence / DORA Analytics — **CROWDED but consolidating into one leader.**

- **LinearB** — **Leader, 2026 Gartner MQ for Developer Productivity Insight Platforms** **[F, per own site]**. Published the single most decision-useful dataset I found: **2.7M PRs, 83,000 developers, 253 organizations, Feb–May 2026** **[F]**
- **Swarmia** — **$11M Series A, 18 Jun 2025** (Karma Ventures + DIG Ventures; angels incl. Cal Henderson/Slack CTO, Romain Huët/OpenAI Head of DevEx). Positioning: "nobody really knows how much these tools are actually helping" → AI ROI measurement
- Jellyfish, Code Climate, Haystack, Pluralsight Flow, GitLab Value Stream, Chronosphere — established **[BASELINE]**

**The LinearB 2026 numbers are the core evidence for §4 and §5 — reproduce them yourself before acting:**

| Metric | Elite (top 10%) | Good (top 30%) | Fair (top 60%) |
|---|---|---|---|
| PRs with AI coding assistance | 54% | 35% | 20% |
| **PRs with AI code review** | **57%** | **26%** | **8%** |
| PRs written by autonomous agents | 4.7% | 1.1% | 0.1% |
| Merged code lines written by AI | 45% | 25% | 12% |
| PR yield rate, all PRs | 90% | 86% | 81% |
| **PR yield rate, agentic PRs** | **79%** | 58% | 37% |
| Token cost per dev per month | $481 | $152 | $50 |

- **AI PRs wait 4.6x longer before review, but are reviewed 2x faster once picked up.**
- **Acceptance rate: AI-generated PRs 32.7% vs 84.4% manual.**
- **AI code review is the single fastest available gain — +5pp PR yield vs all-PR baseline, +7pp vs human-only.**
- Top AI-usage devs at 2.3x their June 2025 merge rate by May 2026; zero-AI devs **declined 3.6%**.
- Token cost at p90 = $481/dev/mo, "still under 4% of a fully loaded developer's cost."

Sources: [LinearB 2026 Benchmarks](https://linearb.io/resources/software-engineering-benchmarks-report) · [LinearB AI productivity gap](https://linearb.io/resources/ai-engineering-productivity-gap) · [Swarmia Series A](https://www.swarmia.com/blog/series-a-funding/)

## 2.5 AI SRE / Incident — **CROWDED.**

Gartner's first **Magic Quadrant for Enterprise AI Coding Agents (published 20 May 2026)**: **Leaders = Anthropic, Cursor, GitHub, OpenAI. Challengers = AWS, Google Cloud, Alibaba Cloud, Cognition.** AWS and Google were Leaders in the 2024 and 2025 *AI Code Assistants* quadrants and were **demoted**. Read: the category was redefined from completion to autonomous plan-act-verify governance, and the cloud-IDE incumbents failed the new bar. **[S — the MQ itself is paywalled; this is a secondary summary]**

SRE/incident: Dynatrace, Shoreline, Traversal (agent-as-SRE), Resolve AI ($40M Series A 2026 **[S: aggregator]**), mabl, Gatling. a16z's Jan 2026 note: *"instead of engineers staring at Grafana dashboards, AI SREs can interpret telemetry and post insights in Slack."* **[F]**

**Verdict: saturated and consolidating around observability incumbents. Adjacent to code review only via the "did the agent's change cause an incident?" loop — which nobody has closed.**

## 2.6 Saturation summary

| Category | Verdict | Who wins | Why |
|---|---|---|---|
| AI code review (horizontal) | **CROWDED / CLOSED** | CodeRabbit ($1.5B), GitHub Copilot, Qodo | Two well-capitalized independents + a free-ish bundled incumbent. Independent #2 got acquired. Benchmark scores are bunched in a 3-point F1 band |
| AI code review (sovereign/regulated) | **OPEN** | Nobody yet | Incumbents are cloud-only or make you ask. Kodus/Sovri/Baz are too small or uncertified |
| Intent/spec verification | **OPEN** | Nobody | Zero benchmark coverage. Solo/OSS swarm only |
| Review debt / verification debt | **OPEN — nobody selling it** | Nobody | Measured, large, and unmonetised |
| AI testing/QA | **CROWDED** | Momentic, mabl, TestMu | Converging on same primitives |
| Legacy modernization | **CROWDED / platform-owned** | AWS Q, IBM Bob PP, Moderne-as-substrate | Hyperscalers use OpenRewrite; IBM owns Z/i metadata |
| SCA / dependency | **MATURED** | Snyk, Mend, Sonar, osv.dev | [BASELINE] category now |
| Engineering intelligence | **CROWDED, one leader** | LinearB | Gartner MQ Leader; owns the AI ROI dataset |
| AI SRE | **CROWDED** | Dynatrace + Gartner MQ leaders | Category just got redefined |
| AI code provenance / attestation | **COMMODITY** | OSS | prompt-bom, ForgeProof, licit, squash all free. Sell the *audit*, not the ledger |

---

# 3. Venture Signal

## 3.1 2026 dev-tooling funding volume

**[S — aggregator, not audited]** FundedStartupsDaily tracked 51 Developer Tools companies raising **$910.9M** in 2026 across pre-seed/seed/Series A. **Median round $6M.** 63% of activity at pre-seed/seed; 27% at pre-seed alone. Largest: **Blitzy $200M Series A**. Also visible: Blitzy ($200M A), 8090 Labs ($135M A), Noon ($44M seed), Resolve AI ($40M A), Coval ($28M A), Naive ($28.5M A), Parasail ($32M A), Kestra ($25M A), CopilotKit ($20M A), Mastra ($22M A), Conductor ($22M A), GitButler ($17M A), OpsMill ($14M A).

**Read: capital has NOT flooded into code review specifically. The 2026 dev-tooling dollars went to agent infrastructure (MCP, agent builders, workflow engines), not to review.** The code-review-adjacent rounds in 2026 were small: Gitar $9M, Baz $9M, StarSling $3M, CodeAnt AI $2M.

## 3.2 Thesis statements

**Sequoia, "Services: The New Software" (5 Mar 2026)** — the single most relevant thesis for a pricing decision:
> *"A copilot sells the tool. An autopilot sells the work."*
> *"For every dollar spent on software, six are spent on services."*
> *"Software engineering accounts for over half of all AI tool usage across professions. Every other category is still in single digits."*
> Playbook: **start where the task is already outsourced** — the budget line exists, the company has accepted external delivery, and the buyer already purchases an outcome. Replacing an outsourcing contract is a vendor swap. Replacing headcount is a reorg.

**Sequoia, "2026: This is AGI" (14 Jan 2026)**: long-horizon agents are functionally AGI. METR data: long-horizon task completion **doubling every ~7 months**; a full human expert day by 2028. *"Soon you'll be able to hire an agent."*

**a16z, "Notes on AI Apps in 2026" (8 Jan 2026)**, Anish Acharya:
> *"There are still fundamental tooling problems to solve — like the fact that all our tools are for making, not for thinking."*
> *"As coding agents work with increasing accuracy and longer time horizons, the hard problem moves from how do I build it to what do we build."*
> Also: a thriving startup ecosystem in coding generated **>$1B of new revenue in 2025 alone**, contradicting the "apps get subsumed by models" thesis.

**a16z, Big Ideas 2026 (9 Dec 2025)**: "agent-native infrastructure becomes table stakes" (thundering-herd patterns as default state); "creating for agents, not humans" (machine legibility over visual hierarchy); data entropy as the bottleneck; **"the collaboration layer becomes the moat"** as multi-party vertical AI raises switching costs.

**Menlo Ventures, "There Are No AI Markets, Only Proto-Markets" (15 Jan 2026)**, Derek Xiao — directly about the failure of category thinking in AI:
> *"Capabilities blur market boundaries… Products are never 'done'… Adoption is bottoms-up."*
> What has **failed** to be a durable moat at the AI app layer: proprietary foundation models, domain-specific fine-tuning, sophisticated search architectures like MCTS. What is rewarded instead: **product plasticity and learning velocity.**

## 3.3 Menlo Ventures: State of Generative AI in the Enterprise

**2025 edition published 9 Dec 2025** (survey of ~500 US enterprise decision-makers). **I could not find a 2026 edition in Menlo's report index — the latest indexed is the Dec 2025 report.** Treat any "Menlo 2026" figure as unverified. **[F for the 2025 report; GAP: no 2026 edition found as of 26 Sep 2026]**

| Metric | Value |
|---|---|
| Total enterprise AI spend 2025 | **$37B, 3x YoY** |
| Applications layer | $19B+ (AI apps now 6% of the entire software market) |
| Coding & developer tools | **$7.3B** |
| Industry-specific AI | $3.5B (healthcare-led) |
| General-purpose copilots | $8.4B (86% share) |
| **Build vs. buy** | **76% purchased vs. built** (was 53/47 in 2024) |
| **Deal conversion to production** | **47% for AI vs. 25% for traditional SaaS** |
| PLG share of AI app spend | **27% (vs. 7% traditional)**; ~40% incl. shadow AI |
| Startups' share of code generation | **71%** |
| Devs using AI coding tools daily | **50%** (65% in top-quartile orgs) |
| **True agent deployments (enterprise)** | **16%** (27% in startups) |
| Products at $1B+ ARR | 10; 50+ crossed $100M |
| Cursor | **$200M revenue before hiring a single enterprise sales rep** |

Menlo's own 2025 mechanism: *"the code review services market"* is not called out, but the adjacent named winners are: **PRs → Graphite** (now acquired by Cursor), **SRE → Resolve**, **QA → Meticulous**, **refactoring → Open Hands**, **deployment → Harness**. *(Note: this list was written before the Cursor/Graphite close. Menlo pointed at the exact asset that got bought.)*

## 3.4 Enterprise agent adoption — the numbers disagree wildly

This matters, so here are all of them with methodology:

| Source | Date | Headline | Methodology |
|---|---|---|---|
| **Databricks / Thoughtworks** | Feb 2026 | **Only 19% of orgs have deployed AI agents**; 67% use AI tools | Telemetry from 20,000+ orgs incl. 60%+ of Fortune 500. Nov 2024–Oct 2025 window. *Self-reported "deployed" is a weak signal* |
| **Halkwinds** | 6 Jun 2026 | **45% of enterprise AI teams have ≥1 agent in production**, up from **<3% in 2024**. Single agent 3–4 mo to prod; multi-agent 6–9 mo. **41% reported ≥1 prompt injection attempt in 2025** | 634 orgs, 500+ employees or $250M+ revenue, Q4 2025–Q2 2026. Self-reported; explicitly flagged for optimism bias |
| **Anthropic + Material** | 2026 | **57% deploy agents for multi-stage workflows**; 16% cross-functional. **~90% use AI for coding**; **86% deploy coding agents to production code**; 42% trust agents to lead dev work; 80% report measurable ROI | 500+ US technical leaders, fielded late 2025. Self-reported |
| **Salesforce** | 27 Aug 2026 | **30% deployed** (47% piloting, 23% evaluating). ROI ~8 months, 53% employee adoption, +29% CSAT. **Only 31% unified data first** — but doing so → ROI at 7.3 vs 8.8 months | 2,025 decision-makers, 20 countries, May 2026. Self-reported |
| **McKinsey** | 25 Aug 2026 | **88% regular AI use; only 23% scaling agents anywhere; 39% experimenting. Only 39% report any enterprise-level EBIT impact** | 1,993 respondents, fielded Jun–Jul 2025 |
| **KXN Technologies** | Mar 2026 | **67% past pilot** (from 31% in 2024). Median $2.4M yr-1 net savings; 8.3 mo to ROI; Financial Services 74% | 312 enterprise AI decision-makers in FS/healthcare/manufacturing. Self-reported |

**Read this honestly: the spread is 19% → 67% for essentially the same question.** The dividing variable is the definition of "deployed." This is a genuinely contested number and I would not build a deck on any single one. The two figures I would actually defend:
- **Only 16% of enterprise deployments are true agents** (Menlo, technical definition: LLM plans, executes, observes feedback, adapts) — vs. mostly fixed-sequence workflows.
- **The value lands where model capability is strong and regulatory friction is low** (Anthropic): *"Tasks requiring regulatory approval, dispersed tacit knowledge, or capabilities AI can't handle see minimal adoption."* That is a direct argument **for** regulated-industry tooling and **against** regulated-industry *agents*.

**Where value is landing (evidence, not vibes):** coding first (>$4B of $7.3B departmental AI spend, 55%), then IT ops ($700M), marketing ($660M), customer success ($630M). Sequoia: software engineering is >50% of all AI tool usage across professions; every other category is single digits.

## 3.5 What failed, got consolidated, or shut down — **the most important section**

| Event | Date | Detail | Signal |
|---|---|---|---|
| **Graphite acquired by Cursor** | 19 Dec 2025 | $52M Series B Mar 2025, ~$290M valuation, 500+ companies, Shopify/Snowflake/Figma/Ramp. Paid "way over" valuation. AI Reviewer + Bugbot to be combined | The #2 independent review platform exited. **No independent exit exists in this category** |
| **Continue.dev acquired and killed** | 16 Jun 2026 | Cursor acqui-hire. No press release. All user data permanently deleted 15 Jul 2026. **Two founding engineers (Romney, Erichsen) went to OpenClaw instead of the acquirer** | Acquirers take teams, not products. 107k-star open source projects are not protected |
| **Gemini CLI closed** | 18 Jun 2026 | Announced 19 May, cut off in 30 days. 107,000 stars, 14,000 forks. Replaced by Antigravity CLI (Go binary, **no public repo**). GitHub thread: **301 thumbs-down, 6 thumbs-up** | 30-day notice. Open-source → closed in one release. Enterprise licences kept |
| **Charlie Labs shutting down** | Announced pre-5 Oct 2026 | Coding agent doing end-to-end PRs. Shutting down 5 Oct 2026, refunds issued. Customers incl. Coforma | Vendor failure in the agent-PR space |
| **Flowise wound down** | 29 Jul – 31 Aug 2026 | Wind-down announced 29 Jul 2026, code frozen same day, repo archived Aug, EOL 31 Aug 2026. **Acquired by Workday Aug 2025 — 11 months later the public product is dead.** A CVSS 10.0 (CVE-2025-59528) was found in 2025; the team **no longer accepts security reports** | Acquisition ≠ product continuity. Archived code with an unpatched RCE |
| **LlamaPReview killed its paid tier** | 1 May 2026 | 535 GitHub App installs, 4,000+ repos, **61% signal-to-noise** (good metrics!), Stripe ready, then shut the paid tier. Founder's words: *"the traditional standalone AI code review bot is rapidly becoming a relic… a standalone GitHub App for code review is rapidly becoming a native IDE feature, not a standalone business."* Pivoted to a local knowledge-base tool | **The clearest single-founder verdict on this market, written by someone who had traction** |
| **OpenAI cuts Cursor's model access** | Effective 12 Nov 2026 | After SpaceX's $60B acquisition of Anysphere. Cites "pattern of contract violations by Musk-linked entities" | Model access is contractual, not permanent. A dependency risk every buyer now prices |
| **SpaceX acquires Cursor ($60B), merges with xAI (Feb 2026)** | Dec 2025 / Feb 2026 | Cursor had hit $1B ARR and a $29.3B valuation one month before | The centre of gravity moved from startups to a mega-cap with no incentive to leave a market open |
| **Windsurf acquired** | 2026 | 350 enterprise accounts, $82M ARR, absorbed | Another dev-tool exit |
| **Qodo originally "Codium"** | — | Repositioned twice (test-gen → code integrity → governance). Founded 2018, still searching for the wedge after $120M | Even a $120M company hasn't settled its own category |

**The negative signal, stated plainly: there is no successful independent exit in AI code review. Every one of the notable outcomes is an acquisition, a shutdown, or a repositioning. The only two that grew into real independence (CodeRabbit, Qodo) both had to move *up-stack* into "governance" to escape the review feature — and CodeRabbit needed a $143M Series C and a $1.5B valuation to do it.**

---

# 4. Enterprise Buyer & Pricing Reality

## 4.1 Willingness to pay

**DevTools is the cheapest vertical to sell into. This is a structural problem, not a positioning problem.**

| Vertical (mid-market median ACV) | Enterprise ACV | Pricing model |
|---|---|---|
| **Cybersecurity** | **$85K** | **$280K** | Per-seat + per-endpoint |
| Fintech | $65K | $220K | Transaction volume + base |
| Healthcare | $58K | $185K | Per-seat + module |
| **DevTools / API-first** | **$35K (LOWEST of all verticals)** | **$95K (still lowest)** | Usage + per-seat |

Sources: GrowthSpree ACV benchmarks 2026 **[S — an agency publishing its own benchmark; treat directionally]**. Cross-check: SaaStr puts enterprise at ~$220K / mid-market ~$40K / SMB ~$4,800, median private-SaaS ACV $26,265 **[S]**.

The benchmark's own explanation is the one that matters:
> *"DevTools runs lower because buyers (engineers) are price-sensitive and self-serve options exist."*

**Implication: you cannot build a $500K ACV business selling horizontal developer tooling to engineers. You have to change the buyer.** Compliance officers, risk officers, and audit functions do not have self-serve options and are not price-elastic on the same curve — Kastra sells to them at GSA-schedule/Net-60 terms; Archiet sells on FedRAMP/HIPAA/SOC 2 posture; mabl sells "compliance-ready evidence continuously — SOC 2 Type II, audit trails, RBAC."

**Pricing model is the single largest ACV lever: 2–4x difference between usage-based and flat-seat for the same product category** **[S]**. 87% of enterprise customers choose annual billing; median enterprise discount 16.7%; 74.5% of contracts run 13–24 months; AI-native tools average a 22.4-month term vs 18.7 for SaaS.

## 4.2 The seat-pricing collapse — this already happened

**In a single 12-month window, every major player moved off per-seat:**

| Date | Company | Change |
|---|---|---|
| ~Mar 2026 | **Greptile** | $30/seat retains only 50 reviews/mo; **$1 per additional review** |
| 11 May 2026 | **Cursor Bugbot** | **Removed the $40/seat fee entirely.** Pure usage-based, **$1.00–$1.50 per run**. Migrated at first renewal after 8 Jun 2026. Seat pricing is now documented as *legacy* |
| 1 Jun 2026 | **GitHub Copilot** | Usage-based **AI credits** (1 credit = $0.01, per token); Lite vs Balanced effort tiers |
| Ongoing | **Qodo** | Credit-based, $0.012/credit |
| Ongoing | **IBM Bob** | **Bobcoins**, 1 coin = $0.50. Pro $20/40 coins, Pro+ $60/160, Ultra $200/500; Enterprise 1,000-coin packs at $500 (10% premium on overage) |

**The consequences, documented by users, not vendors:**
- Cursor forum (May 2026): a 20-PR/month workflow with ~7 runs per PR goes from ~$40/mo flat to **$150–200+/mo**. *"This pricing model actively penalizes continuous AI review and forces developers to use Bugbot merely as a final, static linter right before merging… This pricing effectively kills the ability to use Bugbot alongside automated agentic workflows."*
- Another: *"you can't even see what usage is tied to which PRs… Price seems to double daily and you have no idea why."*
- Cursor shipped effort levels as a mitigation — **Teams-only, and gated on usage billing.** Copilot shipped Lite/Balanced tiers. Both are cost-control features for a model that stopped being predictable.

**Where the money actually is (H1 2026 pricing survey) [S: Cerver, June 2026]** — treat as directional:

| Tool | ARR / run-rate | Note |
|---|---|---|
| Cursor | **$2B** (→ $6B forecast) | >1M paying; **$29.3B valuation** Dec 2025 |
| Claude Code | ~$2.5B | |
| Devin (Cognition) | ~$1B est. | |
| GitHub Copilot | ~20M users, **4.7M paid** | |
| Windsurf | $82M | acquired |
| OpenAI Codex | 5M weekly users | |
| **Token cost, p90** | **$481/dev/month** | LinearB, 253 orgs |

> *"Flat seat prices now understate real cost — at scale, per-developer spend commonly runs $100–200+/mo, and reported heavy-user figures reach $500–$2,000/dev/mo."* **[S]**

**The 2026 default architecture is hybrid, not per-seat** (Causo H1 2026, citing Lenny Rachitsky's three-pillar playbook): usage-gated entry tier + outcome-priced layer for measurable ROI (Intercom Fin = $0.99/confirmed resolution) + heavy-compute gate. **But:** *"CIOs explicitly distrust pure outcome pricing as unpredictable"* and *"Pure per-seat pricing only survives where the buyer is non-technical and the product replaces a license, not a workflow."*

## 4.3 Procurement friction — and the one thing that actually unblocks it

**The sales motion has changed.** For ACV >$25K, the dominant motion is now a **proof-of-value cycle of 30–90 days** anchored to a hard ROI metric agreed before the trial starts. Procurement typically lands **week 10–12**. PLG is only correct when all three hold: genuinely self-serve, technical buyer with spending authority, **ACV ≤$10K**. AI deal conversion: **47% vs 25% for SaaS.** **[S: Causo H1 2026]**

**The unblocker is not a nicer UI or a lower price. It is deployment sovereignty.** The evidence is unusually clean:

| Vendor | Cloud-only? | Self-host | BYO LLM | Air-gap feasible |
|---|---|---|---|---|
| **CodeRabbit** | **Cloud only** | No | No (bundled) | **No** |
| **Greptile** | Yes | **Yes** — customer's own AWS or air-gapped, own LLM provider, SOC 2 | Yes | **Yes** |
| **Qodo** | Yes | **Yes** — single-tenant or on-prem | Yes (BYOK) | Yes |
| **Baz** | Yes | **Yes** | Yes | Yes |
| **Kodus** | Yes | **AGPLv3, fully self-hosted** | Any, incl. internal vLLM/Ollama; **zero markup** | **Yes** (no packaged installer — plan the glue) |
| **Snyk** | Mixed | Agent-based | Snyk only | No |
| **SonarQube** | Yes | **Yes** (Server) | Yes (Enterprise BYOK) | **No AI at air-gap** |
| **Sourcegraph** | Yes | **Yes** | Yes — but **Deep Search is not available to BYOK customers** | Yes |

Kodus's comparison table exists specifically to make one argument: *"CodeRabbit is cloud-only with a bundled LLM… The choice is data sovereignty and cost control versus managed convenience."* And Sovri's README makes the EU version of the same case: *"The dominant AI code-review tools — CodeRabbit, Qodo, CodeAnt — are US-centric SaaS products. For regulated EU customers, that model fails three tests at once: data residency, auditability, and vendor lock-in on the model."*

**And here is the precedent for selling to that buyer** — Kastra (AI authorization for government): air-gapped, NIST 800-53 Rev 5 + **FedRAMP Moderate** control mapping, SCAP-hardened images, CIS benchmarks, signed SBOMs, **ATO-ready tamper-evident hash-chained evidence export**, continuous monitoring, POA&M support, annual third-party pen tests, GSA schedule in progress, **Net-60 terms**. That is a company that solved enterprise procurement and is not a developer tool.

**Compliance regimes that create the mandate** (all primary sources):
- **EU AI Act**: Art. 9 risk management, **Art. 12 record-keeping / traceability**, Art. 13 transparency, Art. 14 human oversight, Art. 26 deployer obligations, Art. 27 FRIA, Annex IV technical documentation. **Art. 50 transparency obligations: 2 Dec 2026.** Annex III high-risk: **postponed to 2 Dec 2027** by the May 2026 Omnibus political agreement. Penalties: up to €35M or 7% of global turnover. Annex IV documentation alone "takes 3–6 months manually" **[S: vendor claim]**
- **DORA** (EU financial entities), **HDS** (French health), **NIS2**, **SecNumCloud** (French sovereign cloud)
- **US**: FedRAMP Moderate/High, CMMC L2 (DoD), NIST AI RMF 1.0 (42 controls), NIST 800-53 Rev 5
- **ISO/IEC 42001** (AI management), **ISO/IEC/IEEE 29148** (requirements quality — the 8-attribute gate: necessary, verifiable, unambiguous, consistent, singular, complete, feasible, traceable, implementation-free)
- **SOC 2 / HIPAA / PCI-DSS / CRA** — Sonar Enterprise now explicitly ships **Cyber Resilience Act (CRA)** compliance and **MISRA C++:2023**

**Sales-cycle data:** I found no reliable published average for AI code review specifically. The best available proxies: POV cycle 30–90 days with procurement landing week 10–12; contract term 13–24 months; Archiet's own stated procurement path is a 30-minute founder call, CAIQ/SIG Lite responses in 5 business days, DPA/BAA redlines in 5–10 business days. **[F for Archiet's claims; the POV cycle is [S]]**

## 4.4 IBM's position and whether watsonx Orchestrate is a real channel

**It is a real channel, and it is unusually well-documented for a partner program.**

**watsonx Orchestrate — Agentic Control Plane (announced 5 May 2026; on IBM Cloud Jun 2026; expanded 2 Jul 2026):**
- Centralised operational layer to observe, govern, and optimise agents "no matter where they were built or where they run." Explicitly **open** — works with IBM native agents, Langflow, LangGraph, and A2A-protocol agents.
- Now supports agents **beyond its native environment**: IBM native, Langflow, LangGraph, A2A. "With broader interoperability coming soon."
- Capabilities: **policy management enforced at runtime** (output limits, secrets detection, rate limiting, content filtering), **credential health monitoring**, **content guardrails** (6 types, IBM Granite Guardian models), **Agent Access overview** (which agent can reach which integration/data source), certification & publishing workflows, lifecycle management, task scheduling, observability with context-variable tracing.
- **Runs on AWS and IBM Cloud**, plus on-premises and AWS GovCloud. **GovCloud IP restrictions** documented. Hybrid.
- **IBM has been recognised as a Leader in the 2025 Gartner MQ for AI Application Development Platforms.**

**Agent Connect — the actual distribution surface:** *"Publish and monetize your agents through a governed ecosystem, with built-in go-to-market support."* Partners build specialised agents, list them in the catalog, reach IBM's customer base. The catalog **already contains third-party partner agents and MCP servers**: D&B Direct+, Fullstory, PagerDuty, Visier, Workable, Netsmartz, Vistergy, AS Peoria. Protocols supported: **MCP and A2A**. This is a live, populated, low-friction integration point — not a "reach out and we'll figure it out" programme.

**So: yes, watsonx Orchestrate is pluggable.** The realistic shape is *a governed verification/attestation agent or tool in the catalog*, invoked by Orchestrate for policy enforcement and audit logging — not a competing IDE.

**But read the threat before the opportunity.** **IBM Bob Premium Package for Z went GA 9 July 2026** and already ships: Z Architect Mode with impact analysis and **business-context discovery**; **business-rule extraction and documentation from metadata and data dictionaries**; **deterministic COBOL→Java with "test cases generated from source behavior to prove equivalence"**; repository-level `agents.md` enforcement of coding standards; dependency-based build on z/OS; Z Code Scan; IBM Debug. Bob's five modes folded into three (Agent, Plan, Ask) with **native tool calling, parallel execution, subagents, background task orchestration**. Plus PP for i (RPG/CL/SQL) and PP for Java. **If your wedge is IBM Z/i, you are competing with your own platform's vendor, who owns Z Understand, the i metadata, watsonx, Granite, and the sales relationship.** Atomico put the counter-argument better than IBM will:

> *"As AI becomes critical infrastructure for the global economy, organisations will increasingly need **independent governance layers that can validate software regardless of which model produced it.** That kind of trusted, model-agnostic infrastructure strengthens the resilience of the software that businesses depend on."* — Luca Eisenstecken, Atomico, on the CodeRabbit Series C **[F]**

That is the strategic opening: **IBM has a conflict of interest it cannot resolve.** It cannot credibly grade code produced by Bob, and it cannot endorse a competitor's validator. A model-agnostic, IBM-ecosystem-compatible, independently-hosted verification layer is a product IBM can *list in its own catalog* without endorsing its own homework.

---

# 5. Gap Analysis — adversarial, with evidence

## (a) Reviewing a change in the context of system history, architecture, and invariants — **NOT A GAP. Being commoditized right now.**

**Verdict: dead as a wedge.**

Evidence it is being worked, aggressively:
- **CodeRabbit** context engineering: function dependencies, **past PR history**, MCP servers, 40+ linters/SAST, custom review instructions, code agent guidelines **[F]**
- **Qodo 2.2**: *"draws on full-repository signals (including codebase history and prior PR decisions)"*; *"While most AI review tools evaluate what changed, Qodo evaluates what that change impacts, across repositories, against codebase history, and measured against the engineering standards an organization has defined"* **[F, vendor claim]**
- **Augment Context Engine**: 400,000+ files, sub-200ms, real-time index, semantic retrieval of auth middleware / token-validation logic / historical permission-check patterns. **Shipped as a free MCP server 6 Feb 2026** so Claude Code, Cursor, and Codex can all use it **[F]**
- **Greptile** graph-based codebase context; **Sourcegraph Deep Search** (agentic, Lua sandbox, no network)
- **IBM PP4Z** took the strongest form: instead of asking a model to reconstruct the estate, it gives it a **deterministic queryable representation** (Z Understand) and teaches Bob to write and run its own queries. *"The point is to make answers traceable to the IBM Z system, not to a training distribution."* **[F]**
- **Moderne's LST** is the same idea for Java: a compiler-accurate model of every repo, pre-computed.

Augment's own engineering writeup concedes the baseline gap — *"most AI code review tools operate almost entirely on the PR diff"* — and then explains they closed it with retrieval. That is the whole story: **the diff-context gap was real, it was identified, and it is being closed by shipping the index over MCP.** The durable primitive is the index, and the index is being given away.

## (b) Verifying AI code satisfies the ORIGINAL requirement / acceptance criteria — **GENUINELY OPEN. The least-served real gap in the category.**

**This is the strongest finding in the dossier, and the evidence is structural rather than anecdotal: the entire evaluation layer is blind to it.**

Every major AI code review benchmark scores *"did the tool find the issues a human reviewer found in the diff."* Martian's offline gold set is **human-curated PR comments**; its online ground truth is **what the developer actually fixed in post-review commits.** Neither asks whether the PR does what the ticket asked for. A tool that flags 10 real bugs in a PR that implements the wrong requirement scores well on both. **A whole category can be excellent at its stated job and 0% at intent verification, and no leaderboard will ever show it.** That is a measurement blind spot, not a product gap — and it means there is no competitive pressure to close it.

Supporting evidence that the capability is not yet delivered even by the leaders:
- Augment's reviewer pulls **Linear, Jira, Notion via MCP for context** — context, not verification. No published claim of acceptance-criteria conformance.
- **LinearB** now markets "AI Code Reviews — catch security risks, bugs, and **spec mismatches**" **[F]** — i.e. a major analytics incumbent just claimed the wedge in Aug/Sep 2026. That is a warning, not a moat.
- **Momentic** (23 Jun 2026) built a "shared product knowledge base" ingesting Jira/GitHub/support/Slack that decides whether a failure is "a real bug or from an intended change" **[F]** — the testing layer is already doing adjacent work.
- **Qodo's founding thesis was literally this**: the $40M Series A announcement says the funding enables *"integrating advanced algorithms into every aspect of software development, **from spec and intent establishment**, through code inception, testing and review"* **[F]**. It then spent two years building tests and reviews and only now claims "governance." The intent piece is still on the roadmap.

**Who's already trying — and how far along they are** (all found via search; all small):

| Player | What it does | Stage |
|---|---|---|
| **Spectrace** | PRDs/transcripts/Slack → structured specs with acceptance criteria → **continuous trace from spec to merged PR**, per-criterion evidence + verdict posted to GitHub/GitLab, **hosted MCP server** so Claude Code/Cursor read the spec live | Live product, no funding found, no pricing found |
| **VasperaPM** | Reverse-engineers a spec from existing code, validates it as canonical, then **continuously verifies the code never drifts**. Flags missing error handling, edge cases, GDPR gaps. 230 requirements verified / 1 drifted demo | Early product |
| **driftless** | PRD ↔ tech-spec **1:1 bidirectional traceability**, spec gates that **block** on contradiction before code, "$3.60 per Acceptance Criteria, all-in" | Early product |
| **OpenAgile.AI** | Epic → story → task decomposition, 342 domain checks across 15 perspectives, bidirectional AC↔code↔test traceability, EU AI Act / ISO 27001 / SOC 2 framing | **Alpha. "Don't expect generated code yet."** |
| **Specwright** | AGENTS.md skill framework; 6 quality gates; **wiring verification** (orphaned files, unused exports, layer violations); AC→code+test evidence matrix; "AI agents optimise for done. Specwright optimises for works" | OSS, v0.31.0 Apr 2026 |
| **attest** (skill) | Full spec-compliance pipeline: extract ACs → ISO/IEC/IEEE 29148 quality gate → generate BDD per AC → verify with CODE_SEARCH/LOGIC_TRACE/STATE_CHECK/ERROR_PATH/ABSENCE_CHECK → **CERTIFIED / CONDITIONAL / REJECTED** verdict + traceability matrix + remediation handoff. Adversarial probing across 6 categories | OSS skill |
| **Trex / Momentic** | Runtime validation agent that writes and runs its own tests against a PR | Funded, live |

**The honest read: the primitives are all free and OSS, the solo/small-player layer is swarming, and the incumbents are circling.** The defensible asset is **not** the AC-extraction algorithm. It is (i) a **vertical corpus of real acceptance criteria** for a regulated domain, and (ii) an **evidence format an auditor accepts**. Both take longer than an algorithm and neither is bought.

## (c) Detecting when a change silently breaks an invariant, contract, or assumption not expressed in code — **GENUINELY OPEN, AND THE BEST-SUPPORTED WEDGE.**

**Evidence the problem is real and unsolved at scale:**
- **No tool exceeds 63% recall on human-verified issues**; the best misses a third **[F]**
- **On 1k+ line PRs, aggregate recall is 30% — tools miss 70% of key issues.** Every tool degrades. Fullstack PRs score worst across the board **[F]**
- Note what large-PR degradation *is*: it is exactly the regime where a change's blast radius exceeds the diff. This is the invariant problem, measured.
- The **precision understatement** finding cuts the same way: tools find real issues the gold set omits, i.e. their notion of "issue" is diff-local and misses systemic/business-rule violations entirely.
- **DORA's verification tax** is the organisational version: time saved writing is re-spent auditing, and 30% of developers report **little to no trust** in AI-generated code **[F]**
- **DORA 2024:** +25% AI adoption → −1.5% throughput, **+7.2% delivery instability**. **DORA 2025:** throughput relationship flipped positive, **instability relationship did not.** As of the April 2026 update DORA's framing is still that *"AI currently hurts software delivery performance."* **[F]**

**Why it stays open technically:** an invariant violated by a change is, by definition, not visible in the change. It lives in a business rule in someone's head, a compliance clause, a data-retention policy, a rounding convention, an implicit ordering assumption, or a decade of production behaviour. No amount of retrieval finds it, because it was never written down. IBM's PP4Z faces this head-on and its answer is instructive: it does static analysis to extract business rules and data dictionaries, generates tests from **source behaviour** to prove equivalence, and adds **runtime tracing** — *"static analysis tells you what can happen; runtime data tells you what did"* **[F]**. That is three expensive mechanisms, and IBM only does it for COBOL on z/OS.

**Who's trying:**
- **Codacy AI Risk Hub** + AI Inventory (risk-oriented framing)
- **Sovri**: CWE→regulation mapping attaching **GDPR, DORA, NIS2 references** to every finding, with a provenance trail (model, prompt digest, hosting region) on each finding. Pre-alpha, no certifications
- **Momentic** Failure Classification Agent: real bug vs. intended change vs. flaky vs. transient
- **IBM PP4Z**: business-rule extraction, data dictionaries, equivalence testing
- **Specwright**: wiring verification (orphaned code, unused exports, layer violations) — closest OSS analogue
- **OpenAgile.AI / attest**: the `attest` probe taxonomy is literally built for this — Boundary (BND), Omission (OMS), **Contradiction (CTR)**, **Implicit (IMP)**, Negative (NEG), Concurrency (CNC)

**Verdict: open, expensive, and mapped to a budget that engineering does not own.** The buyer is risk/compliance/audit, not the VP Eng. That is the whole reason it is defensible.

## (d) Measuring/attributing which agent or prompt produced risky code — **THE CAPABILITY IS A COMMODITY. THE DATA IS NOT.**

**Be precise here, because it is easy to mistake an OSS pile for a market.**

What already exists, free and open source:
- **prompt-bom** — Rust CLI, walks a repo, attributes each AI-generated hunk to model/session/prompt hash, emits **signed SPDX 2.3 + SPDX-AI extension JSON**. Joins Claude Code session JSONL records to file content via substring match + git blame. Designed for EU AI Act / CRA. v0.0.1 pre-release
- **ForgeProof** — Ed25519-signed, SHA-256 hash-chained append-only ledger. Multi-model attribution, **provider-separation enforcement** (audits must come from a different provider than the origin), geographic/jurisdiction compliance policy, public verification, analytics by provider/model/country
- **licit** — two-method provenance: `git-infer` (6-heuristic, **60–95% confidence**) + `session-log` (parse agent session files, **95%**). HMAC-SHA256 per-record, Merkle-tree batches. Covers EU AI Act Art. 9/12/13/14/26/27 + Annex IV + FRIA + OWASP Agentic Top 10. CI gate
- **squash** — SPDX 2.3 SBOM + CycloneDX 1.7 ML-BOM + Annex IV in 10s + NIST AI RMF 42/42 + SLSA L1–3 + Sigstore Rekor, $299/mo
- **AIBoMGen** (arXiv 2601.05703, 9 Jan 2026) — signed CycloneDX AIBOM + in-toto attestations, neutral third-party root of trust
- Standards are moving: **SPDX 3.0 and CycloneDX 1.7 now carry AI-specific fields**

**Critical distinction nobody has solved:** all of the above is **model BOM / training provenance**. ForgeProof's own comparison table is honest about it:

| Tool | Proves | Does NOT prove |
|---|---|---|
| SLSA/Sigstore/cosign | Binary built from source in trusted CI/CD | Which AI wrote the source |
| SBOM (SPDX/CycloneDX) | What components are in the software | How components were created |
| C2PA | Media file provenance | Code provenance (code is trivially refactored) |
| **ForgeProof** | **Which model wrote the code, where it ran, whether independently audited** | **That the output is correct or secure** |

**And no one does per-agent, per-prompt, per-PR *risk* attribution.** The demand signal exists and is measured — LinearB gives the *aggregate*: 54% of PRs with AI assistance, 45% of merged lines AI-written at top-decile orgs, **but "fewer than 5% of PRs come from autonomous agents,"** and their agentic PR yield (79% elite / 37% fair) has no attribution to *which agent*. Nobody correlates *which agent + which prompt version* → *defect escape → rollback → Sev-1*.

**Verdict: do not sell provenance infrastructure; it is free and it is a spec race you will lose to SPDX/CycloneDX.** The defensible asset is the **correlation model** — the accumulated dataset linking agent/prompt identity to downstream defect and incident outcomes. That is a data moat you build by running, and it gets better with every reviewed PR. It is also the natural input to (b), (c), and (e). A free hobbyst can emit a signed BOM; almost nobody can tell you which agent is producing your production incidents.

## (e) Review debt — accumulating unreviewed / under-reviewed AI output — **REAL, MEASURED, AND UNOWNED AS A CATEGORY. This is the single most under-monetised finding in this dossier.**

**Every vendor in this category sells reviews *performed*. Nobody sells the backlog of reviews *not* done*, risk-weighted, with a decay curve and an auditor-readable burn-down.**

The measurements:

| Finding | Value | Source |
|---|---|---|
| Bot-reviewed OSS PRs with **zero human activity after the bot comments** | **52.8%** | Martian, Apr 2026 **[F]** |
| Bot-reviewed PRs with **no human reviewer besides the author** | **84%** | Martian **[F]** |
| Codex: PRs with a human reviewer besides the author | **4.6%** (of ~48,000 analysed) | Martian **[F]** |
| Solo-developer repos: Codex / Copilot / Cursor | **96% / 92% / 91%** | Martian **[F]** |
| CodeRabbit engagement / follow-up commit | 60.5% / 39% | Martian **[F]** |
| Codex engagement / follow-up commit | 33.2% / 6.6% | Martian **[F]** |
| **Acceptance rate: AI-generated PRs vs manual** | **32.7% vs 84.4%** | LinearB, 2.7M PRs, 253 orgs **[F]** |
| AI PRs wait for review | **4.6x longer** (but reviewed 2x faster once picked up) | LinearB **[F]** |
| **PR yield, agentic vs all** | **79% vs 90%** (elite); **37% vs 81%** (fair) | LinearB **[F]** |
| Developers reporting **little to no trust** in AI-generated code | **30%** | DORA 2025, n≈5,000 **[F]** |
| AI adoption effect on delivery instability | **+7.2%** per +25% adoption (2024); **still negative in 2025** | DORA **[F]** |
| Verification tax | *"time saved during initial code generation is often re-allocated to verification overhead"* | DORA 2025 **[F]** |

**Corroborating structural evidence:** the two largest PR-review datasets in the world are *measuring this and nobody has built a product on it.* Martian built a research lab to quantify it. LinearB built a benchmark section for it. Both are dashboards, not controls.

**And the phrase already exists as marketing, not as a product category:** mabl advertises *"No coverage debt"* and *"No maintenance sprints."* The problem is named by sellers; it is not yet instrumented by anyone.

**Why it stays open:** it is a *negative* metric. Nobody's budget line is "review debt reduction," which means nobody is defending it — but it maps directly onto change-failure rate, which *does* have a budget line, and onto DORA/audit/regulator attention.

**Speculation, flagged as such [SPEC]:** a risk-weighted inventory of under-reviewed AI-generated code, recomputed continuously and reported as an exposure number with a burn-down, is likely a *feature* inside a broader platform within 24 months (Codacy AI Risk Hub, LinearB, or CodeRabbit Triage are the obvious homes). It is unlikely to remain a standalone product for long. **Therefore: ship it as an input to a wedge you own, not as the wedge itself.**

---

# 6. Five Defensible Wedges

Ranked by defensibility × time-to-first-revenue. Each states the moat, the 48h version, the 12-month version, the buyer, the pricing model, and the honest risk.

---

## Wedge 1 — **IBM-ecosystem verification control plane: the independent validator Bob cannot be**

**The insight, quoted by a $1.5B competitor:** organisations *"will increasingly need independent governance layers that can validate software regardless of which model produced it."* IBM has a conflict of interest it structurally cannot resolve — it cannot credibly grade code produced by Bob, and it cannot endorse a rival's validator. It *can* list one in its own catalog.

**What exists already on the IBM side (so you are not starting from zero):** Z Architect Mode (impact analysis, dependency assessment, business-context discovery), business-rule extraction from metadata + data dictionaries, deterministic COBOL→Java with **tests generated from source behaviour to prove equivalence**, repository-level `agents.md` standards enforcement, Z Code Scan, DBB on z/OS, IBM Debug, PP for i (RPG/CL/SQL, QSYS source members) and PP for Java.

**What is missing — the wedge:** an **independent, model-agnostic attestation layer** that (1) consumes Z Understand / i metadata / Bob's `agents.md` standards as *inputs*, (2) verifies the *output* against the stated business rule and the original requirement, (3) emits a signed, auditor-readable record, and (4) runs **inside the customer's enclave**, not in your VPC.

- **48h version:** an `agents.md`-consuming validator that runs in GitHub Actions against Bob PP4Z output and posts a per-business-rule verdict to the PR. Publish the control mapping. Get 3 design-partner conversations, not revenue.
- **12-month version:** MCP/A2A tool in the watsonx Orchestrate **Agent Connect catalog** (the surface already carries third-party partner MCP servers — D&B, Fullstory, PagerDuty, Visier, Workable). Equivalence-test generation from COBOL source behaviour. Ed25519 evidence chain. FedRAMP/DORA-ready pack.
- **Buyer:** mainframe modernisation programme leads and second-line risk/compliance. **Not** individual developers — IBM Bob sells Pro at $20/user to individuals and you cannot win that.
- **Pricing:** per attested application or per modernisation wave. Both are countable, both have a budget line, and neither scales with headcount — which is the point.
- **Moat:** IBM won't build it (conflict), hyperscalers can't (no Z/i metadata), and OpenRewrite-based tools don't touch COBOL/PL-I/RPG.
- **Honest risk [SPEC]:** IBM can build it, will build it eventually, and can bundle it into Bob Premium Packages at zero incremental price. Your window is the 12–24 months before PP5Z. **[SPEC — no source for IBM's internal roadmap.]** Mitigate by being genuinely model-agnostic and genuinely outside the Bob IDE — that way you are more useful to IBM as a *catalog partner* than as a competitor.

---

## Wedge 2 — **Intent attestation: did the code do what the ticket asked?**

**The gap is a measurement blind spot, not a feature gap.** Every benchmark scores bug-finding in the diff. Nothing scores requirement satisfaction. There is therefore no competitive pressure to solve it, and no leaderboard credit for solving it.

**What exists to build on:** the OSS primitives are complete and free — AC extraction, ISO/IEC/IEEE 29148 quality gating, BDD generation, static verification methods (CODE_SEARCH / LOGIC_TRACE / STATE_CHECK / ERROR_PATH / ABSENCE_CHECK), bidirectional traceability matrices, CERTIFIED/CONDITIONAL/REJECTED verdicts, adversarial probing across Boundary/Omission/Contradiction/Implicit/Negative/Concurrency. The `attest` skill is a working reference implementation of the whole pipeline.

- **48h version:** a GitHub App + action that reads the linked issue's acceptance criteria, generates a BDD check per criterion, statically verifies the diff against it, and posts a per-criterion verdict + traceability matrix on the PR. Blocks merge on any CRITICAL FAIL. This is a weekend, not a quarter.
- **12-month version:** the vertical corpus. This is the actual moat — **a few thousand real, regulator-grade acceptance criteria for one domain** (e.g. EU retail payments, or US 834 EDI, or insurance claim adjudication) with the mapping to the tests that prove them. That corpus cannot be scraped and it is what an auditor actually asks for. Add runtime verification (generate and run the test) to close the loop from static conformance to behavioural proof.
- **Buyer:** engineering leadership *plus* the audit/compliance function. The audit function is the one with the budget and no self-serve option.
- **Pricing:** **per attested release** or per audited application. Countable, and it sidesteps the CIO's distrust of variance-based outcome pricing because the unit ("a release") is discrete and forecastable. This is the cleanest fit to Sequoia's "sell the work, not the tool" without taking open-ended outcome risk.
- **Moat:** the corpus, plus the evidence format. Both compound and neither is bought.
- **Honest risk:** LinearB already markets "spec mismatches"; Momentic's knowledge base already ingests Jira and decides "real bug vs. intended change"; CodeRabbit's Triage is one product release away. **[SPEC: none of these has shipped AC-level per-criterion verification as of 26 Sep 2026 — that is my read of the public pages, not a vendor confirmation.]** The OSS swarm is the bigger near-term risk, but none of them have a regulated corpus.

---

## Wedge 3 — **The review-debt ledger: a risk-weighted inventory of under-reviewed AI code**

**Cheapest to build of the five, and the most alarming number in the dossier.** Every vendor sells reviews performed. This sells the reviews *not* done.

**Your problem statement, all measured:** 52.8% of bot-reviewed PRs get zero human response · 84% have no human reviewer besides the author · AI PRs merge at 32.7% acceptance vs 84.4% for human PRs · agentic PR yield 37–79% vs 81–90% overall · 30% of developers distrust AI-generated code · AI adoption still degrades delivery stability.

**- 48h version:** a scheduled job that reads git history + agent session logs + PR review graph + CI results and reports, per repo and per business capability: % of merged lines agent-authored, % with no human reviewer, % with no automated review, weighted by change-failure rate and incident history. Output: a single number and a chart. This is data engineering, not AI.
- **12-month version:** a **decay curve** and burn-down — exposure as a function of time-since-merge, with remediation prioritised by realised (not modelled) defect rate. Add the attribution model from Wedge 5 as the risk input. Sell the burn-down to the audit committee quarterly.
- **Buyer:** VP Eng (as a productivity/release-velocity instrument) and the risk function (as an exposure number). Report both framings; they buy for different reasons.
- **Pricing:** this is the wedge where outcome pricing actually works, because the outcome is a *measured reduction in a number the client already reports*. "Your review debt went from 41% to 9% of agent-authored changes touching the payments ledger" is a countable, auditable, non-vague outcome — the exact property Intercom Fin's $0.99/resolution has and that pure-outcome SaaS usually lacks.
- **Moat:** weak on its own — this is precisely the kind of thing Codacy's AI Risk Hub or LinearB's benchmark section becomes next year. **[SPEC]**
- **Therefore: do not build this as a standalone company. Build it as the data engine inside Wedge 2 or Wedge 4,** where the same inventory becomes evidence rather than a dashboard. Its standalone value is that it is how you *sell* the other two.

---

## Wedge 4 — **Sovereign / attested deployment for regulated enterprise**

**The incumbents are structurally disqualified, and they have said so themselves.** CodeRabbit is cloud-only with a bundled LLM — Kodus's own comparison table, and Kodus's own page, say it plainly. Sourcegraph disables its best agentic feature for BYOK customers. SonarQube's AI has no air-gap story. Sovri's README names the three failures for EU regulated buyers: **data residency, auditability, and vendor lock-in on the model.** And Sovri — the company built specifically for that gap — is **pre-alpha with no ISO 27001, no SOC 2, no HDS, no SecNumCloud, and explicitly says "this product does not claim to be certified."** The gap is real and unfilled.

**The precedent to copy is not a dev tool — it's Kastra:** air-gapped, NIST 800-53 Rev 5 + FedRAMP Moderate control mapping, SCAP-hardened images, CIS benchmarks, signed SBOMs, **ATO-ready hash-chained tamper-evident evidence export**, continuous monitoring, POA&M support, annual third-party pen tests, GSA schedule, Net-60. That is how you survive a security review. Archiet shows the same shape for HIPAA/FedRAMP/PCI-DSS.

- **48h version:** three things, none of which require a certification. (a) Publish the **NIST 800-53 / SOC 2 / DORA / ISO 42001 control-mapping page** — which control your product satisfies and how, with evidence artefacts named. (b) Publish a **real air-gap deployment guide** with a local-vLLM/Ollama endpoint, a private container registry, and telemetry disabled — Kodus and StarSling have already proven the pattern works. (c) Ship a **self-hosted review runner priced on compute** (StarSling: $0.004/min for a 2-vCPU runner, customer's model key) so you are selling infrastructure with near-zero COGS and no seat problem. This gets you in the door while you build certs.
- **12-month version:** SOC 2 Type II (CodeRabbit and Augment already have it — it is table stakes, not a differentiator). Then **one** of: FedRAMP Moderate (18–24 months, or acquire), DORA operational-resilience pack, or ISO/IEC 42001 (fastest, and increasingly the AI-specific one). Add signed, exportable audit evidence.
- **Buyer:** a compliance officer or a bank/insurer CISO — **not an engineer.** This is the entire point: you stop competing on the axis engineers optimise.
- **Pricing:** platform fee + per-deployment, or per attested-environment. Does not scale with seats. Premium multiple over the $35K DevTools median ACV is achievable because the buyer is different — compare Kastra's GSA/Net-60 posture and Archiet's "enterprise deals scoped on a 30-minute call with the founder."
- **Moat:** certifications and an air-gapped build are 12–18 months of work you cannot buy, and the incumbents' cloud-only architecture is a decision they cannot cheaply reverse. High ACV, low churn, small market.
- **Honest risk:** the certification path is slow, sales cycles are long, and the market is smaller than the horizontal one. **[SPEC: I found no reliable average sales-cycle length for AI code review in regulated industries. Do not plan against a number I cannot source.]**

---

## Wedge 5 — **Agent-risk attribution — sell the correlation model, never the ledger**

**This is the honest version of gap (d), and it requires giving up the easy story.** Provenance *infrastructure* is a commodity: prompt-bom, ForgeProof, licit, and squash are free, open, MIT/Apache, and cover Ed25519 signing, SPDX 2.3/3.0, CycloneDX 1.7 ML-BOM, in-toto attestations, EU AI Act Annex IV, FRIA, NIST AI RMF, and OWASP Agentic Top 10. SPDX and CycloneDX are actively adding AI fields. **You will lose a spec race and you should not enter it.** ForgeProof's own table concedes the boundary: it proves *which model wrote the code*, not *that the code is correct or secure*.

**What nobody has is the risk model:** **which agent, at which prompt version, on which task class, produces code that correlates with defect escapes, rollbacks, and Sev-1s — for this codebase, under this team's workflow.** LinearB gives the aggregate (54% of PRs AI-assisted, 45% of merged lines, agentic yield 37–79%) and explicitly cannot attribute. No published benchmark scores it. No tool computes it.

- **48h version:** a script that joins Claude Code / Codex / Cursor session logs to git blame to PR review outcomes to incident data, and reports a per-agent defect-escape rate. The plumbing already exists in four OSS projects — you assemble it. The first report is genuinely interesting and almost nobody has it.
- **12-month version:** the accumulated correlation model, and three products out of it: (i) **per-agent risk scores** that gate which agents run on which paths (High-risk model on `payments/`, cheap model on `docs/`); (ii) **model/prompt regression detection** — "PRs generated with prompt v3.2 have a 2.4x rollback rate"; (iii) the **regulator-facing exposure statement** — which is really Wedge 3 in a compliance costume. (ii) is the most novel and the least crowded **[SPEC]**.
- **Buyer:** platform engineering / developer productivity (Wedge 3 framing) and the AI governance function (Wedge 4 framing). Same engine, two products.
- **Pricing:** fold into Wedge 3 or 4. Do not sell standalone — the standalone buyer has to be told the ledger exists first, and if they know the ledger exists they'll use a free tool.
- **Moat:** a dataset that improves with every reviewed PR and cannot be reconstructed from public data. Real, but it is a *data* moat, not a *technology* moat, and it only pays after 6–12 months of volume.
- **Honest risk:** Codacy already ships an AI Inventory + AI Risk Hub, and LinearB has the PR/incident data to build this internally at any time. **[SPEC]** Counter: they have the *aggregate* telemetry and no incentive to build a per-agent causal model, because it would require them to opine on model quality — which is a vendor-conflict they will avoid for the same reason IBM will avoid grading Bob's output.

---

## Sequencing recommendation

| Horizon | Do | Why |
|---|---|---|
| **Weeks 1–4** | Build **Wedge 3's 48h version**. One scheduled job, one number: *% of merged lines that are agent-authored with no human and no automated review, weighted by realised defect rate.* Simultaneously write the **Wedge 4 control-mapping page** and the **air-gap deployment guide** — both are content, not product, and they are the door-opener. | Wedge 3 is days of work and gives you the number that sells Wedges 2 and 4. The control-mapping page costs a week and is the thing a security reviewer asks for first. |
| **Months 2–6** | Ship **Wedge 2's 48h version** (per-criterion AC verification on the PR) and land 3–5 design partners **inside IBM Z/i accounts specifically** — where the incumbent review tools are weakest, the code is highest-stakes, and the buyer has budget. Submit an MCP tool to watsonx Orchestrate Agent Connect. | The per-criterion verifier is a weekend build on top of free OSS primitives. The IBM design partners are the fastest route to a reference customer with a reference logo. |
| **Months 6–12** | Assemble **Wedge 5's correlation model** on top of your own review volume. Publish the corpus and the first real risk findings. Start SOC 2 Type II. | The data moat needs volume you won't have until Wedge 2 is shipping. SOC 2 is table stakes for Wedge 4 and takes months to start. |
| **Do not** | Build a signing/BOM tool. Enter horizontal AI code review. Sell per-seat. Sell to individual developers. Compete with CodeRabbit or Qodo on a general-purpose reviewer. | §1 and §3.5. There is no independent exit in this category and every peer that tried got acquired or shut down. |

---

# Appendix A — Sources

**Primary (vendor/official/benchmark):**
- CodeRabbit Series C — https://www.coderabbit.ai/newsroom/coderabbit-series-c-agentic-change-management
- CodeRabbit Series B — https://www.businesswire.com/news/home/20250916401011/en/
- Qodo Series B — https://financialpost.com/globe-newswire/qodo-raises-70m-to-accelerate-fight-against-software-slop-from-openclaw-and-claude-code · https://www.qodo.ai/blog/qodo-50m-to-accelerate-quality-of-software-development-with-ai/ · https://www.qodo.ai/pricing/
- Greptile Series A — https://www.greptile.com/blog/series-a · https://www.greptile.com/content-library/greptile-martian-code-review-benchmark
- GitHub Copilot code review — https://github.blog/ai-and-ml/github-copilot/60-million-copilot-code-reviews-and-counting/ · https://github.blog/changelog/2026-03-05-copilot-code-review-now-runs-on-an-agentic-architecture/ · https://github.blog/changelog/2025-04-04-copilot-code-review-now-generally-available/ · https://github.blog/changelog/2026-04-08-copilot-reviewed-pull-request-merge-metrics-now-in-the-usage-metrics-api/
- Cursor — https://cursor.com/blog/graphite · https://cursor.com/help/account-and-billing/bugbot-usage-based-billing · https://cursor.com/changelog/bugbot-updates-june-2026 · https://cursor.com/bugbot
- **Martian Code Review Bench** — https://codereview.withmartian.com/ · https://github.com/withmartian/code-review-benchmark · https://withmartian.com/post/code-review-bench-v0 · https://withmartian.com/post/measuring-the-software-factorys-inspection-line · offline README · CodeSheriff PR #24
- IBM Bob — https://www.ibm.com/new/announcements/announcing-the-ibm-bob-premium-package-for-z · https://www.ibm.com/new/announcements/ibm-bob-expands-with-premium-packages-new-architecture-and-greater-enterprise-control · https://bob.ibm.com/blog/bob-for-z-announcement/ · https://bob.ibm.com/docs/ide/premium-packages/bob-for-z/bob-for-z-index · https://bob.ibm.com/pricing · https://bob.ibm.com/docs/ide/account/bobcoins · https://newsroom.ibm.com/2026-07-09-ibm-advances-enterprise-ai-software-development-with-multi-agent-capabilities-and-specialized-modernization-workflows
- watsonx Orchestrate — https://www.ibm.com/products/watsonx-orchestrate/agent-control-plane · https://www.ibm.com/new/announcements/introducing-the-agentic-control-plane · https://www.ibm.com/products/watsonx-orchestrate/agent-catalog · https://www.ibm.com/docs/en/watsonx/watson-orchestrate/base?topic=releases-release-notes-june-2026
- AWS — https://aws.amazon.com/q/developer/transform/ · https://aws.amazon.com/blogs/migration-and-modernization/simplify-mainframe-modernization-using-amazon-q-developer-generative-ai-agents/
- DORA — https://dora.dev/research/2025/dora-report/ · https://dora.dev/ai/gen-ai-report/ · https://dora.dev/insights/balancing-ai-tensions/
- Menlo Ventures — https://menlovc.com/reports/ · 2025 PDF · https://menlovc.com/perspective/there-are-no-ai-markets-only-proto-markets-why-the-saas-playbook-fails-in-ai/
- Sequoia — https://sequoiacap.com/article/services-the-new-software/ · https://sequoiacap.com/article/2026-this-is-agi/
- a16z — https://a16z.com/notes-on-ai-apps-in-2026/ · https://a16z.com/newsletter/big-ideas-2026-part-1/
- Anthropic 2026 State of AI Agents — https://resources.anthropic.com/hubfs/The%202026%20State%20of%20AI%20Agents%20Report.pdf
- Databricks/Thoughtworks 2026 State of AI Agents — https://www.thoughtworks.com/content/dam/thoughtworks/documents/e-book/State-of-AI-Agents-2026-020426.pdf
- McKinsey — https://www.mckinsey.com/capabilities/quantumblack/our-insights/the-state-of-ai
- Salesforce — https://www.salesforce.com/news/stories/agentic-ai-leaders-survey-on-roi/
- LinearB — https://linearb.io/resources/software-engineering-benchmarks-report · https://linearb.io/resources/ai-engineering-productivity-gap · https://linearb.io/blog/dora-ai-capabilities-model-engineering-efficiency-apex-framework
- Augment — https://www.augmentcode.com/blog/context-engine-mcp-now-live · https://www.augmentcode.com/context-engine · https://www.augmentcode.com/blog/how-we-built-high-quality-ai-code-review-agent
- Kodus — https://kodus.io/ · https://kodus.io/self-hosted-ai-code-review/
- Sonar — https://www.sonarsource.com/plans-and-pricing/ · https://www.sonarsource.com/blog/ai-codefix-is-now-generally-available/
- Codacy — https://www.codacy.com/pricing
- Momentic — https://momentic.ai/blog/series-a · https://momentic.reportablenews.com/pr/momentic-launches-the-first-agentic-quality-platform-as-ai-continues-to-scale-code-output
- Moderne — https://www.globenewswire.com/news-release/2025/02/11/3024163/0/en/ · https://moderne.ai/openrewrite
- Provenance OSS — https://github.com/verepdev/prompt-bom · https://github.com/bxrist/forgeproof · https://github.com/mpiton/sovri · https://github.com/Diego303/licit-cli · https://squash.works/ · https://arxiv.org/html/2601.05703v1
- Intent/spec entrants — https://spectrace.io/ · https://openagile.ai/ · https://vasperapm.com/ · https://godriftless.ai/ · https://github.com/Obsidian-Owl/specwright
- Kastra (gov precedent) — https://kastra.ai/industries/government
- Archiet (compliance posture precedent) — https://archiet.com/enterprise
- Gartner MQ for Enterprise AI Coding Agents (20 May 2026) — covered via https://www.beri.net/article/gartner-magic-quadrant-enterprise-ai-coding-agents-cloud-giants-dethroned-2026 **[S]**
- Gartner Peer Insights code review — https://www.gartner.com/reviews/market/code-review-tools

**Secondary (trade press / aggregators / analysts):**
- Reuters on CodeRabbit — https://www.reuters.com/technology/ai-code-review-platform-coderabbit-valued-15-billion-latest-funding-round-2026-08-12/
- TNW — https://thenextweb.com/news/coderabbit-raised-143m-to-read-the-code-ai-wrote
- Tech Funding News — https://techfundingnews.com/coderabbit-lands-143m-at-1-5b-valuation-as-ai-generated-code-surges/ · https://techfundingnews.com/qodo-70m-series-b-qumra-capital-ai-code-review/
- SiliconANGLE — https://siliconangle.com/2026/03/30/ai-generated-code-verification-startup-qodo-raises-70m/ · https://siliconangle.com/2026/06/29/exclusive-agentic-coding-startup-baz-brings-code-reviews-planning-stage-extends-seed-funding-17m/ · https://siliconangle.com/2026/08/12/coderabbit-bags-143m-help-companies-get-grip-explosion-ai-generated-code/
- TechCrunch — https://techcrunch.com/2025/07/18/benchmark-in-talks-to-lead-series-a-for-greptile-valuing-ai-code-reviewer-at-180m-sources-say/ · https://techcrunch.com/2025/12/19/cursor-continues-acquisition-spree-with-graphite-deal/ · https://techcrunch.com/2025/11/24/momentic-raises-15m-to-automate-software-testing/
- Axios Pro — https://www.axios.com/pro/enterprise-software-deals/2025/12/19/cursor-buys-code-review-platform-graphite
- Fortune — https://fortune.com/2025/12/19/cursor-ai-coding-startup-graphite-competition-heats-up/
- ARR Club (CodeRabbit ARR tracker) — https://www.arr.club/coderabbit/coderabbit-arr-nearing-100m-with-50-growth-in-q2-alone
- Sacra (Greptile/CodeRabbit pricing) — https://sacra.com/c/greptile/
- **Shutdowns** — Continue.dev: https://byteiota.com/continue-dev-shuts-down-export-your-data-before-july-15/ · Gemini CLI: https://www.uniflow.kr/en/gemini-cli-shutdown-what-it-taught-us/ · Charlie Labs: https://charlielabs.ai/blog/charlie-is-shutting-down/ · Flowise: https://vibecoding.app/blog/flowise-review · LlamaPReview: https://jetxu-llm.github.io/posts/why-i-killed-my-ai-code-review-saas/ · OpenAI/Cursor model access: https://www.renascence.io/news/77027/
- Adoption surveys — Halkwinds: https://www.halkwinds.com/research/ai-agent-adoption-report-2026 · KXN: https://kxntech.com/global/en/research/state-of-agentic-ai-2026/
- Pricing/ACV — GrowthSpree: https://www.growthspreeofficial.com/blogs/b2b-saas-average-deal-size-acv-benchmarks-2026-by-vertical-segment-arr-stage-gtm-motion · vendorbenchmark: https://vendorbenchmark.com/blog/saas-pricing-benchmarks-enterprise-2026 · Mystery Demo: https://www.mysterydemo.com/blog/saas-enterprise-pricing-statistics · Causo H1 2026 GTM: https://hub.causo.ai/guides/h1-2026-ai-product-gtm-report · Cerver: https://cerver.ai/report
- FundedStartupsDaily 2026 dev tools — https://www.fundedstartupsdaily.com/raises/developer-tools/
- Code intelligence landscape — Ry Walker: https://rywalker.com/research/code-intelligence-tools
- Gitar — https://theaiinsider.tech/2026/04/17/gitar-raises-9m-to-deploy-ai-agents-for-code-validation-and-software-quality-control/
- StarSling — https://runtimewire.com/article/starsling-raises-3m-review-runners-code-review-agents
- Swarmia — https://www.swarmia.com/blog/series-a-funding/

---

# Appendix B — Confidence and gaps

**High confidence, primary-sourced:** CodeRabbit/Qodo/Greptile funding and terms; GitHub Copilot adoption numbers and GA dates; Bugbot pricing change and usage; the Martian benchmark findings and all five conclusions drawn from it; DORA 2024/2025 numbers; IBM Bob PP4Z capabilities and Bobcoin pricing; watsonx Orchestrate Agentic Control Plane + Agent Connect; Amazon Q Transform; Moderne funding and OpenRewrite's position as shared substrate; EU AI Act article/deadline references; LinearB's 2026 benchmark table; every shutdown in §3.5.

**Medium confidence, secondary-sourced:** all ARR figures (CodeRabbit's especially — no audited figure exists, only an ARR tracker and a "5x YoY" claim with no base); Greptile's ~$180M valuation; all per-seat price points for CodeRabbit/Cubic/Graphite/Ellipsis; ACV benchmarks; the Gartner MQ leaderboard; the 2026 dev-tooling funding aggregate; Cerver's ARR figures; the POV sales-cycle numbers.

**Explicit research gaps — do not assume these are settled:**
1. **No Menlo Ventures 2026 State of GenAI report found.** Latest indexed is Dec 2025. If a 2026 edition exists, it likely supersedes several figures here.
2. **Endor Labs, Cybeats, Aikido: 2025–26 round sizes not researched** (search provider rate-limited). SCA category verdict is based on the mature incumbents only.
3. **No reliable published sales-cycle length for AI code review**, especially in regulated industries. The 30–90 day POV cycle is the best available proxy and is secondary-sourced.
4. **"Ellipsis AI" vs `ellipsis.dev`** — two distinct companies appear under one name in search results. I could not establish current status or funding for Ellipsis AI's code-review line.
5. **Bito, Pieces, CodeSee, Trunk 2025–26 status** is asserted from their absence from current coverage and search results, not from their own announcements. Treat as inferred.
6. **Qodo's valuation is undisclosed** (PitchBook masks it). No number should be quoted.
7. **Customer counts for Baz, Gitar, StarSling, Kodus, Cubic** are unavailable or pre-2025.
8. **I did not verify whether any incumbent has shipped per-criterion acceptance-criteria verification.** The §5b verdict is based on public product pages and benchmark methodologies as of 26 Sep 2026. A private beta would not be visible.
9. **CodeRabbit's "Agentic Change Management" was announced 12 Aug 2026 and the newsroom page delegates detail to Business Wire.** Triage/Change Stack/Security capabilities are described from the press release and TFN's coverage, not from product documentation I could read in full.

**Speculation, isolated and labelled:** all `[SPEC]` tags in §5e and §6 — specifically the 12–24 month window before an IBM PP5Z, the claim that review-debt gets absorbed as a platform feature, the claim that no incumbent has shipped AC-level verification, the novelty assessment of prompt-version regression detection, and the build-vs-buy judgement on Wedge 5. None of these rest on a source.
