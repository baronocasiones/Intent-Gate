# Evidence Dossier: "AI shifted the bottleneck from code writing to code review"

Compiled for a hackathon product decision. Target claim: *as AI writes more code, the constraint in
software delivery has moved to code review and validation.*

Evidence tiers used throughout:
- **STRONG** = primary-source behavioral telemetry or peer-reviewed/RCT data at scale
- **MODERATE** = credible vendor research with methodology disclosed, or survey data with conflicts of interest
- **WEAK** = single small study, recycled decade-old figures, or unattributable
- **CONTESTED** = credible sources disagree, or the source has since retracted/updated

---

## 1. THE CORE STAT: the "85%" IBM cited

### What IBM actually said
IBM's press release (July 9, 2026) states: *"85% of DevSecOps professionals surveyed agreeing that AI
has shifted the bottleneck from writing code to reviewing and validating it"* with footnote [1].
- Source: https://newsroom.ibm.com/2026-07-09-ibm-advances-enterprise-ai-software-development-with-multi-agent-capabilities-and-specialized-modernization-workflows
- Date: July 9, 2026
- **IBM did not conduct this survey.** It is a citation of someone else's research.

### The actual underlying source — FOUND
**GitLab 2026 AI Accountability Report**
- Fieldwork by **The Harris Poll**
- **n = 1,528 developers and technology buyers**, six countries
- Published **June 23, 2026** (16 days before IBM's press release)
- GitLab's own key-findings bullet, verbatim: *"85% agree AI has shifted the bottleneck from writing code to reviewing and validating it"*
- Press release: https://about.gitlab.com/press/releases/2026-06-23-gitlab-research-reveals-organizations-are-generating-ai-code-faster-than-they-can-control-it/
- IR version: https://ir.gitlab.com/news/news-details/2026/GitLab-Research-Reveals-Organizations-Are-Generating-AI-Code-Faster-Than-They-Can-Control-It/default.aspx
- Report landing page: https://about.gitlab.com/resources/ai-accountability-survey-2026/
- Independently reported by InfoQ, June 29, 2026, with matching numbers: https://www.infoq.com/news/2026/06/ai-coding-outpaces-governance
- Direct quote from Manav Khurana, GitLab CPMO, to The New Stack: *"AI has shifted the bottleneck from writing code to reviewing it — 85% of our survey respondents confirmed this... Developers have an increased load of validating code they didn't write and may not fully understand. The gains from writing code faster are washed away by the lag in days-long review cycles."* https://thenewstack.io/gitlab-ai-code-governance

### Supporting stats from the same GitLab report (all n=1,528, June 23, 2026)
| Stat | Value |
|---|---|
| Write/commit code faster since adopting AI | 78% |
| Overall code quality improved | 73% |
| AI coding ROI exceeded expectations | 60% |
| Individual productivity improved BUT overall delivery not accelerated at same pace ("AI Paradox") | 79% |
| **Bottleneck shifted to reviewing/validating** | **85%** |
| Biggest challenge is governing AI code *after* creation | 84% |
| Cannot reliably distinguish AI-generated from human-written code in own codebase | 43% |
| Concerned about maintainability of AI-generated code | 73% |
| AI code risks new technical debt org not prepared to manage | 82% |
| AI code accumulation is a risk to manage now | 83% |
| Report it as a top-5 technology risk | 44% |
| Some form of governance challenge with AI code | 92% |
| Adopted AI faster than they built governance policies | 80% |
| Orgs w/ 2+ AI coding tools in active use | 91% (54% have 3+) |
| SDLC tools fully integrated w/ shared data/workflows | 28% |
| Traceability barriers: hard to distinguish AI vs human code | 43% |
| Fragmented toolchains | 40% |
| Systems that don't track code origin | 39% |
| Confident team could determine within 24h whether AI code caused an incident | 87% |
| ...but of orgs that HAD an incident in past year, could not make that determination | 34% |
| Plan to invest in AI code governance tools in next 12 months | 91% (98% have/expect budget) |

### ⚠️ How to characterize the 85%
**Tier: MODERATE, and vendor-conflicted.** Four reasons to be careful:

1. **IBM misattributed the population.** IBM said "DevSecOps professionals." GitLab's press release
   says "developers and technology buyers"; GitLab's own landing page says "1,528 DevSecOps
   professionals." GitLab describes the same sample two different ways, and IBM inherited the
   more flattering framing. Do not present n=1,528 as "DevSecOps professionals" without noting this.

2. **It is an attitudinal survey, not a behavioral measurement.** 85% *agree* with a leading
   statement. It is not a measurement of time-to-merge, review queue depth, or reviewer hours.
   Section 2 below contains actual behavioral data, and it is far better.

3. **Direct commercial conflict.** GitLab sells a DevSecOps platform. Khurana's framing in the same
   coverage: *"The GitLab mantra states that when governance is built into the platform, code reviews
   are automatic, based on the team and company's policies."* GitLab's Nov 2025 report used a
   *different* 85% — "85% agree agentic AI will be most successful when implemented in a platform
   engineering approach" — which is even more transparently self-serving.
   Source: https://about.gitlab.com/press/releases/2025-11-10-gitlab-survey-reveals-the-ai-paradox/

4. **GitLab's own data partially contradicts it.** 73% say overall code quality *improved*, and
   GitLab's own top-of-list problem is *governance* (84%), not review. A quality improvement and a
   review crisis are in tension.

**Honest framing for a pitch:** "A June 2026 Harris Poll survey of 1,528 developers and technology
buyers, published by GitLab, found 85% agree AI has shifted the bottleneck from writing code to
reviewing and validating it. Vendor-commissioned and attitudinal, so we treat it as directional —
but three independent telemetry datasets confirm the direction."

---

## 2. INDUSTRY DATA — the behavioral evidence (this is the real strength)

### 2.1 CircleCI State of Software Delivery 2026 — **STRONG**
Best evidence in the dossier. Telemetry, not survey. Sponsored by Thoughtworks (CircleCI sells CI,
so there is vendor interest — but this is their own instrumented pipeline data across 28M runs).

- **28 million CI/CD workflows, 22,000+ organizations, 149 countries.** Data collected in first 28 days of September 2025. Published **Feb 18, 2026**.
- Report: https://circleci.com/landing-pages/assets/2026-state-of-software-delivery-report.pdf
- Press release: https://www.prnewswire.com/news-releases/circleci-publishes-2026-state-of-software-delivery-302691131.html
- CTO Rob Zuber: *"success in the AI era is not determined by how quickly code can be written, but by the ability to validate, integrate, and ship code, and recover at scale."*

| Metric | Value |
|---|---|
| Average daily throughput (workflow runs) YoY | **+59%** — largest increase since report began in 2019 |
| Top 5% of teams, daily throughput | 6.8 → 13.4, **+97%** |
| Top 10% / top 25% | +47% / +25% |
| **Median team** daily throughput | **+4%** |
| Bottom 25% of teams | **no measurable increase** |
| **Median team: feature-branch throughput** | **+15%** |
| **Median team: MAIN-BRANCH throughput** | **−7%** ← code generated faster, shipped *slower* |
| Top 10%: feature branch / main branch | ~+50% / **+1%** |
| Top 5%: feature branch / main branch | +85% / +26% |
| **Main-branch success rate** | **70.8%** — lowest in 5+ years; CircleCI's own benchmark is 90% |
| Recovery time to green (median team) | 72 min, **+13% YoY** |
| Elite cohort size | fewer than 1 in 20 teams |

**Q2 2026 Pulse** (published July 7, 2026, 20M+ workflows, first 28 days of March 2026):
- Feature-branch throughput **+7.7%** YoY; main-branch throughput **entirely flat** YoY.
- Introduces **Merge Efficiency Ratio (MER)** = validation cycles needed to ship one change.
- Profiling: slow outer-loop feedback "could cost teams nearly **$1M a year**"; inner-loop validation cuts that by >75%.
- https://circleci.com/landing-pages/assets/2026-q2-state-of-software-delivery-report.pdf

> **This is the single best sentence for a pitch:** the median team's feature-branch throughput rose
> 15% while its main-branch throughput *fell* 7%. Code creation accelerated; delivery decelerated.

### 2.2 Faros AI — **STRONG** (telemetry, with correlation caveats)
Two annual reports from engineering-intelligence vendor Faros AI. Vendor sells analytics, not
engineering tools, so conflict is lower than GitLab's. Correlational, not causal.

**"The AI Productivity Paradox" (July 2025)** — 10,000 developers, 1,255 teams
- PDF: https://cdn.prod.website-files.com/66f2fa250759eeb1f2b1199a/68d6e93f3060b3c8a32e72bf_AI_Engineering_Impact_Report_July_2025_Faros_AI.pdf
- Blog: https://www.faros.ai/blog/ai-software-engineering

| Metric | Value (high-AI-adoption teams) |
|---|---|
| Tasks completed | **+21%** (ρ=0.21, p<0.01) |
| PRs merged | **+98%** (ρ=0.30, p<0.01) |
| **PR review time** | **+91%** (ρ=0.08, p<0.01) |
| Tasks touched per day | +9% (ρ=0.22) |
| PRs touched per day | +47% (ρ=0.15) |
| **Average PR size** | **+154%** |
| **Bugs per developer** | **+9%** |
| Work restarts | +13.8% |
| Stalled tasks | +26% |
| **Org-level (DORA metrics, throughput, quality KPIs)** | **no significant correlation with AI adoption** |

Faros's own summary of the mechanism: *"downstream bottlenecks are absorbing the value created by AI tools."*
Corroborated independently by Communications of the ACM, July 21, 2026: https://cacm.acm.org/news/how-to-cross-the-ai-code-productivity-divide

**"AI Engineering Report 2026: The Acceleration Whiplash"** — 22,000 developers, 4,000 teams
- https://faros.ai/research/ai-acceleration-whiplash
- Two-year comparison, published ~Sept 2026:

| Metric | 2025 | 2026 | Direction |
|---|---|---|---|
| **Median time in PR review** | +91% | **+441%** | **deepening** |
| **PRs merging with ZERO review** | — | **31% more** | **worsening** |
| PR size | +154% | +51.3% | still overloaded |
| **Bugs per developer** | +9% | **+54%** | accelerating |
| **Incidents per PR** | — | **+242.7%** | production risk |
| Monthly incidents | — | +57.9% | |
| Bugs per PR | — | +28.7% | |
| **Code churn** | — | **+861%** | |
| Epics completed/dev | — | +66.2% | positive |
| Tasks throughput | +21% | +33.7% | positive |
| PRs merged/dev | +98% | +16.2% | positive but decelerating |
| **Deployments per week** | — | **−11.7%** | **negative** |
| PR contexts handled daily | +67.4% | | cognitive load |
| Task contexts handled daily | +17.7% | | |
| AI adoption: devs using ≥1 tool weekly / teams >50% WAU / PRs reviewed by an AI agent | | 60% / 80% / 25% | |

> **"31% more PRs are merging with zero review" is a devastating and highly citable fact.** It is
> direct evidence that the market is not solving the review bottleneck — it is *evading* it.

### 2.3 LinearB 2026 Software Engineering Benchmarks — **STRONG**
8.1M+ PRs, 4,800 teams, 42 countries, 163,820 contributors.
- Report: https://linearb.io/resources/software-engineering-benchmarks-report
- Blog: https://linearb.io/blog/8-million-prs-engineering-productivity
- Podcast w/ Ben Lloyd Pearson: https://linearb.io/dev-interrupted/podcast/linearb-2026-benchmarks-ai-pr-merge-rate (Mar 24, 2026)
- Blog, Sept 9, 2026: https://linearb.io/blog/engineering-health

| Metric | Value |
|---|---|
| **AI PRs merge within 30 days** | **32.7%** |
| **Unassisted PRs merge within 30 days** | **84.4%** (also cited 84.5%) |
| Elite-tier acceptance threshold | >95% manual vs just over 71% AI |
| **AI PRs wait before a reviewer picks them up** | **4.6x longer** — 16+ hrs vs ~200 min (~3.3h) |
| Agentic PRs, 75th percentile wait | **17.6 hrs** vs 3.4 hrs unassisted (5.25x) |
| Once picked up | reviewed **2x faster** than manual |
| **AI-assisted PR size** | **2.5–2.6x larger**; 75th pct **400+ lines** vs 157 |
| Agentic PR size, 75th pct | ~290 lines |
| Devs using AI regularly | 88.3% (from 71.6% early 2024) |
| Orgs that don't formally measure AI's impact | 44.7% |
| Leaders reporting productivity gains based on adoption signals rather than delivery data | 76.1% |

Lloyd Pearson's stated mechanism: AI PRs are *"basically waiting idle for review."* PRs of 400+ lines
*"increases a lot of the mental tax on people who have to review the code."*

**The Sept 9, 2026 LinearB blog is the best single articulation of the context/bus-factor problem:**
> *"the same handful of engineers open every review that matters. AI raised the volume of code
> arriving, and the work of judging that code goes to whoever holds the most context about your
> systems... Review capacity is what the volume runs into, and the reviewing itself is toil that's
> being created for a small number of people."*

### 2.4 Anthropic's own engineering data — **STRONG (but self-interested)**
Anthropic launched Claude Code "Code Review" on **March 9, 2026**, and disclosed its internal numbers.
- https://claude.com/blog/code-review
- https://techcrunch.com/2026/03/09/anthropic-launches-code-review-tool-to-check-flood-of-ai-generated-code/

| Metric | Value |
|---|---|
| **Anthropic's own statement of the problem** | *"Code output per Anthropic engineer has grown 200% in the last year. Code review has become a bottleneck"* |
| On customer pain | *"developers are stretched thin, and many PRs get skims rather than deep reads"* |
| **Share of Anthropic PRs getting SUBSTANTIVE review comments, before tool** | **16%** |
| ...after deploying multi-agent Code Review | **54%** |
| Large PRs (>1,000 lines changed) getting findings | **84%**, avg 7.5 issues |
| Small PRs (<50 lines) getting findings | 31%, avg 0.5 issues |
| Findings marked incorrect by engineers | **<1%** |
| Average review time | ~20 min |
| Reported cost | $15–25 per PR (third-party analysis, not Anthropic's own figure) |

> **Before Anthropic deployed AI review tooling, 84% of its PRs received no substantive human review
> comment.** A frontier lab with unlimited budget and elite engineers. This is the strongest single
> data point for "review is already broken and getting worse," and it came from a company selling
> the fix — which makes it hard to dismiss as competitor marketing.

### 2.5 GitHub Octoverse 2025 — **MODERATE** (platform telemetry, self-selected population)
Data window Sept 1, 2024 – Aug 31, 2025. Published Nov 2025.
- https://octoverse.github.com/
- https://github.blog/news-insights/octoverse/what-986-million-code-pushes-say-about-the-developer-workflow-in-2025
- https://github.blog/news-insights/octoverse/what-the-fastest-growing-tools-reveal-about-how-software-is-being-built

| Metric | Value |
|---|---|
| Total developers on GitHub | 180M+ (+36M in 2025) |
| Commits pushed | **986M, +25% YoY** |
| PRs merged | **43.2M/month, +23% YoY** |
| PRs created | +20.4% |
| Code pushes | 82.19M/month vs 65M in 2024 |
| Total projects | 630M (+121M) |
| Repos created | 230+/minute |
| Contributions to public repos | 1.12B, +13% |
| AI-related repos | 4.3M+ |
| New devs using Copilot in first week | ~80% |
| TypeScript | became #1 language on GitHub Aug 2025, first time ever |
| **Mean time to fix critical security vulns** | **26 days, down 30% from 37 days** |
| Dependabot adoption | +137% to 846,000 projects |
| Copilot Autofix fixing broken access control | 6,000+ repos/month |
| **Broken access control overtook injection as #1 code security alert** | 151,000+ repos, **+172% YoY**, "often due to AI-generated scaffolds skipping authentication checks" |
| Top language growth | TypeScript +1M contributors; Python +850,579 (+48.78%) |

**Note two counterweights to the doom narrative:** (a) mean time to fix critical vulns *improved* 30%;
(b) GitHub explicitly says PRs are getting *smaller* — *"Pull requests simply aren't novels anymore.
We're seeing more short, readable pull requests with a single purpose."* That directly contradicts
Faros's +154% PR size finding. **Contested.**

### 2.6 GitHub Stacked PRs launch — **STRONG on mechanism** (vendor's own admission)
Announced **April 13–14, 2026** (private preview); public preview **July 30, 2026**.
- https://www.infoworld.com/article/4158575/github-adds-stacked-prs-to-speed-complex-code-reviews.html
- https://www.infoq.com/news/2026/04/github-stacked-prs

GitHub's own words:
> *"Large pull requests are hard to review, slow to merge, and prone to conflicts. **Reviewers lose
> context, feedback quality drops, and the whole team slows down**."*
> *"GitHub's traditional PR model created a bottleneck where developers either waited long cycles for
> reviews or bundled work into large, hard-to-review PRs that increased risk and slowed merges."*
> *"Feed any failures back into the next iteration until the relevant checks pass, then open the PR
> while the diff is still small enough to review, validate, and ship with confidence."*

Research cited in the launch announcement: analysis of **1.5 million pull requests** found PRs of
**200–400 lines had 40% fewer defects and were approved 3x faster** than larger ones.

Historical anchor quoted by InfoQ: Evan Priestley, co-creator of Phabricator Differential
(Facebook, 2007): *"I was spending a lot of time waiting for code review to happen, which was a major
motivator for building the tool."*

> A top-three platform shipping a feature whose entire purpose is fixing code review, and describing
> reviewer context loss as the core problem, is a strong signal of where the pain is.

### 2.7 Stack Overflow Developer Survey 2025 — **MODERATE** (n=49,000+, but self-selected)
Published **July 29, 2025**. 49,000+ responses, 177 countries, 62 questions, 314 technologies.
- https://survey.stackoverflow.co/2025/ai
- Press release: https://stackoverflow.co/company/press/archive/stack-overflow-2025-developer-survey

| Metric | Value |
|---|---|
| Use or plan to use AI tools | **84%** (up from 76% in 2024) |
| Professional devs using AI daily | 51% |
| **Trust accuracy of AI output** | **29%** (down from 40% in 2024) — headline: "Trust in AI at an All Time Low" |
| **Distrust** accuracy of AI output | **46%** (up from 31%) |
| Actively trust / actively distrust | 33% / 46%; only **3%** "highly trust" |
| Experienced devs | lowest "highly trust" (**2.6%**), highest "highly distrust" (**20%**) |
| Positive favorability toward AI | 60% (from 72%) |
| **#1 frustration: "AI solutions that are almost right, but not quite"** | **45%** (66% in the AI section) |
| **Spend MORE time fixing "almost-right" AI code** | **66%** |
| Would still ask a person when they don't trust AI | **75%** |
| Currently use AI agents | **31%** (17% planning, 38% no plans) |
| Devs who don't use agents or stick to simpler tools | 52% |
| Agent users reporting reduced time on tasks / increased productivity | 70% / 69% |
| **Agent users reporting improved team collaboration** | **17%** — lowest-rated impact "by a wide margin" |
| Agent users reporting improved code quality | 38% |
| Not vibe coding professionally | 72% (+5% emphatically not) |

**The "17% collaboration improvement" is important for this thesis.** AI's measured benefit is
individual; its measured *team-level* benefit is near zero. That is the signature of a shifted
bottleneck rather than a capability gain.

### 2.8 DORA / Google Cloud — **STRONG, and the direction REVERSED**
**2024 report** (published Oct 22, 2024) — the "AI hurts delivery" finding:
- https://cloud.google.com/blog/products/devops-sre/announcing-the-2024-dora-report
- https://dora.dev/research/2024/dora-report/
- n ≈ 3,000 respondents

Per **25% increase in AI adoption**:
| Outcome | Change |
|---|---|
| Documentation quality | +7.5% |
| Code quality | +3.4% |
| **Code review speed** | **+3.1%** |
| Approval speed | +1.3% |
| Code complexity | −1.8% (good) |
| **Delivery throughput** | **−1.5%** |
| **Delivery stability** | **−7.2%** |
| Reported little/no trust in AI-generated code | 39% |

**2025 report — "State of AI-assisted Software Development"** (published Sept 23–24, 2025), ~5,000 professionals:
- https://blog.google/technology/developers/dora-report-2025
- https://dora.dev/research/2025/dora-report/
- Analysis: https://itrevolution.com/articles/ais-mirror-effect-how-the-2025-dora-report-reveals-your-organizations-true-capabilities
- Analysis: https://www.techtarget.com/it-infrastructure/news/366631712/Google-DORA-Software-delivery-caught-up-to-AI-coding-tools (Sept 23, 2025)

| Metric | 2024 | 2025 |
|---|---|---|
| AI adoption | 76% | **90%** |
| Report productivity gains | >1/3 moderate–extreme | **>80%** |
| Report code quality improvement | 67% | 59% |
| **Throughput vs AI adoption** | **−1.5%** | **now POSITIVE (reversal)** |
| **Instability vs AI adoption** | −7.2% | **still negative — persists** |
| Little/no trust in AI code | 39% | 30% |
| Median AI user | — | 2 hrs/day alongside AI; reaches for it ~half of roadblocks |

**DORA's own March 10, 2026 analysis names the verification tax explicitly:**
> *"While AI successfully accelerates initial code generation and reduces the friction of starting new
> tasks, **the time saved in creation is frequently re-allocated to auditing and verification**... This
> dynamic is creating a shifting burden within engineering teams, **specifically during the code
> review process**."*
> *"AI's primary role in software development is that of an amplifier. It magnifies the strengths of
> high-performing organizations and the dysfunctions of struggling ones."*
- https://dora.dev/insights/balancing-ai-tensions (March 10, 2026)

Developer quote DORA collected:
> *"I feel somewhat more productive, but it's at a cost. While I end up spending less time writing
> code, I spend more time babysitting the AI and reviewing what it is trying to do."*

**DORA's crucial self-critique of the +3.1% review-speed figure:**
> *"Of course, faster code reviews and approvals do not equate to better and more thorough code review
> processes... It is possible that we're gaining speed through an **over-reliance on AI for assisting
> in the process or trusting code generated by AI a bit too much**."*
> — https://services.google.com/fh/files/misc/dora-impact-of-generative-ai-in-software-development.pdf

> **Handle the DORA reversal carefully.** DORA 2024 says AI reduces throughput; DORA 2025 says it
> increases it. If a judge knows DORA, citing only 2024 looks like you didn't read 2025. The honest
> 2026 framing: throughput recovered, **instability did not**, and DORA itself attributes the
> remaining cost to a "verification tax" landing on review.

### 2.9 Google RCT — **STRONG, and it CONTRADICTS the productivity-paradox thesis**
Paradis et al., *"How much does AI impact development speed? An enterprise-based randomized controlled trial"*, ICSE-SEIP 2025.
- https://arxiv.org/pdf/2410.12944v3 | https://dl.acm.org/doi/10.1109/ICSE-SEIP66354.2025.00060
- **n = 96 full-time Google engineers**, C++/Piper, recruited June–July 2024. Three AI features: AI Code Completion, Smart Paste, NL-to-Code.
- **Result: ~21% faster** (p<0.05). Effect size controlling for covariates ≈ 21%. Authors note the **confidence interval is large**.
- Interesting interaction: developers spending **more** hours on code-related activity per day were faster with AI.
- Authors' own caveat: *"we cannot assume that the effect size obtained in our lab study will
  necessarily apply more broadly, or that the effect of AI found using internal Google tooling in the
  summer of 2024 will translate across tools and over time."*

**Implication:** on a bounded, standardized task in a familiar codebase, Google's own RCT found a
solid speedup. The "review bottleneck" thesis is not a claim that AI makes individuals slower —
it's a claim about **team-level flow and validation capacity**. Keep those separate.

---

## 3. THE METR RCT — and why citing it in July 2026 is a mistake

### 3.1 The famous result (July 10, 2025) — **now explicitly superseded**
Becker, Rush, Barnes, Rein. *"Measuring the Impact of Early-2025 AI on Experienced Open-Source Developer Productivity."*
- Blog: https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study
- Paper: https://metr.org/Early_2025_AI_Experienced_OS_Devs_Study-paper.pdf | arXiv:2507.09089

| Detail | Value |
|---|---|
| Design | RCT, within-developer, issue-level randomization |
| n | **16** experienced developers |
| Repos | avg 22,000–23,000 stars, 1M+ LOC each |
| Developer experience on those repos | avg **5 years** prior |
| Tasks | **246**, avg 2.0 hrs each |
| Tools | primarily Cursor Pro + Claude 3.5/3.7 Sonnet |
| Window | February–June 2025 |
| **Result** | **19% SLOWER** (CI **+2% to +39%** for slowdown) |
| Developers' pre-task forecast | expected 24% faster |
| Developers' post-task estimate | believed 20% faster |
| Economics-expert forecast | 39% faster |
| ML-expert forecast | 38% faster |
| Developer compensation | $150/hr |
| Analysts investigated | 20 potential contributing factors |

**METR's own banner now reads:** *"⚠️ These results are out of date... We believe these historical
results no longer reflect the current impact of AI models on open-source developer productivity."*

### 3.2 The February 24, 2026 update — **this is what you should cite**
https://metr.org/blog/2026-02-24-uplift-update

| Cohort | Estimated speedup | 95% CI |
|---|---|---|
| **Early 2025 (original study)** | **−19% (slower)** | −39% to −2% |
| **Late 2025, returning panel devs (n=10)** | **−18% (i.e. 18% faster)** | −38% to +9% |
| **Late 2025, newly recruited devs (n=47)** | **−4%** | −15% to +9% |

Design: follow-on study from **August 2025**, 10 original + 47 new developers from more diverse
projects, **$50/hr** compensation.

METR's own conclusions, verbatim:
> *"**Late-2025 AI likely accelerated open-source developers**, but selection effects obscure the true
> speedup. However the true speedup could be much higher among the developers and tasks which are
> selected out of the experiment."*
> *"our data is only very weak evidence for the size of this increase."*
> *"An increased share of developers say they would not want to do 50% of their work without AI,
> even though our study pays them $50/hour."*

**Tier: CONTESTED, resolving toward "AI now helps individuals."**

**If you cite METR, cite the 2026 update, not the 19%.** Citing "19% slower" in September 2026 is
a factual error against the source's own retraction banner, and a judge who reads the METR blog
will catch it. The defensible METR framing is about **perception**: developers believed they were
20% faster when they were 19% slower — a 39-point perception gap. METR's May 2026 survey of 349
technical workers found self-reported value gains of 1.3x (retrospective March 2025) → 2x (March
2026) → 2.5x forecast (March 2027), and noted METR staff report the *lowest* gains of any subgroup.
https://evals.alignment.org/blog/2026-05-11-ai-usage-survey

### 3.3 Counter-evidence you should know about before arguing "AI is a thief of time"
- **arXiv:2509.19708** — "Intuition to Evidence," DeputyDev platform, **300 engineers, 1 year, production deployment**: **31.8% reduction in PR review cycle time** (128.8h → 90.5h; cycle time 150.5h → 99.6h), 28% increase in shipped code volume, 71% found PR reviews helpful, ~20 min/day saved. **But:** the low-adoption Cohort 2 saw a **−11.4% decline in shipped code volume** (p=0.08). Gains scale with adoption intensity; sporadic use produces nothing.
- **GitHub Copilot code review** (March 5, 2026): 60M+ reviews, 10x growth since April 2025 launch, now **>1 in 5 code reviews on GitHub**; 12,000+ orgs run it on every PR; **actionable feedback in 71% of reviews, silence in 29%**; agentic architecture that reads linked issues/PRs. https://github.blog/ai-and-ml/github-copilot/60-million-copilot-code-reviews-and-counting

---

## 4. FAILURE MODES OF AI CODE

### 4.1 Package hallucination / "slopsquatting" — **STRONG, peer-reviewed**
Spracklen, Wijewickrama, Sakib, Maiti, Viswanath, Jadliwala (UTSA / Univ. of Oklahoma / Virginia Tech).
*"We Have a Package for You! A Comprehensive Analysis of Package Hallucinations by Code Generating LLMs."*
**USENIX Security 2025** (Seattle, Aug 13–15, 2025). **Distinguished Paper Award winner.**
- https://www.usenix.org/conference/usenixsecurity25/presentation/spracklen
- PDF: https://www.usenix.org/system/files/usenixsecurity25-spracklen.pdf
- Blog: https://www.usenix.org/publications/loginonline/we-have-package-you-comprehensive-analysis-package-hallucinations-code

| Metric | Value |
|---|---|
| Design | 16 LLMs, 2 prompt datasets, **576,000 code samples** (paper abstract figure) |
| Also reported as | **2.23M code samples**, 440,445 (19.7%) with ≥1 hallucinated package (per CSA April 2026 research note) |
| **Hallucination rate, commercial models** | **≥5.2%** (GPT-4 Turbo lowest at **3.59%**) |
| **Hallucination rate, open-source models** | **21.7%** (CodeLlama family >33% in some configs) |
| Overall average across all 16 models | **19.6%** |
| **Unique hallucinated package names identified** | **205,474** |
| Breakdown: pure fabrications / conflations / typo variants | 51% / 38% / 13% |
| **Predictability: hallucinated names reappearing on all 10 identical re-runs** | **43%** — this is what makes slopsquatting viable |
| Hallucinated Python package names that actually exist in npm | **8.7%** (cross-registry confusion) |
| Documented live incident | `unused-imports` on npm (models hallucinate it instead of `eslint-plugin-unused-imports`); still live with ~233 weekly downloads as of early Feb 2026 |
| Related | Perry et al., *"Asleep at the Keyboard"*: Copilot generated vulnerable code **40% of the time** on MITRE Top-25 CWEs |

**IMPORTANT COUNTER-EVIDENCE (2026 replication):** arXiv:2605.17062, *"Re-evaluating LLM Package Hallucinations on the 2026 Model Cohort"* — replicated on 5 frontier models (Claude Sonnet 4.6, Claude Haiku 4.5, GPT-5.4-mini, Gemini 2.5 Pro, DeepSeek V3.2), Oct 2025–Mar 2026 releases, **199,845 code samples**:
- Range compressed from **5.2%–21.7% (16.5 pp spread) → 4.62%–6.10% (1.48 pp spread)** — an 11x narrowing.
- *"The range has shrunk; the threat has not. At 4–7%, slopsquatting remains adversary-[reachable]."*
- **Use the 4.6–6.1% figure, not 19.6% or 21.7%, if you want to be current and unimpeachable.** The 43%-predictability and 8.7%-cross-registry findings are the durable, interesting parts.

CSA research note (April 19, 2026): https://labs.cloudsecurityalliance.org/research/csa-research-note-slopsquatting-ai-supply-chain-20260419-csa

### 4.2 Code churn and duplication — GitClear — **MODERATE** (huge dataset, but a vendor selling code analytics; AI-attribution is inferred, not observed)
**"The Maintainability Gap: AI Code Quality in 2026"** (June 2026) and **"Write-Only Mode"** (2026)
- https://www.gitclear.com/the_ai_code_quality_maintainability_gap
- https://www.gitclear.com/write_only_mode_ai_research
- Live signal dashboard: https://www.gitclear.com/industry_stats/ai_code_quality_signal_graphs
- Coverage: https://thenewstack.io/ai-coding-duplication-rose/ (Sept 14, 2026) | https://pipelinemag.ai/posts/gitclear-maintainability-gap-ai-coding-debt/ (July 22, 2026)

**623 million analyzed code changes, 2023–2026.** Dashboard scope: 976.2M lines evaluated since
Dec 2024, 6.4M AI-attributed lines, 289,467 developers observed.

| Signal | Change | Detail |
|---|---|---|
| **Refactoring (moved code)** | **−70%** | 21% of changed lines (2022) → 13% (2023) → **3.8%** (2026 YTD) |
| **Legacy maintenance (long-term update %)** | **−74%** | 1.7% (2023) → **0.46%** (2026 YTD) — code untouched >12 months is essentially never revisited |
| **Code block duplication** | **+81%** | 40.3 (2023) → **73.0** duplicate lines per 1,000 changes (record high) |
| Within-commit copy/paste | +41% | 9.4% (2022) → **15.7%** (H1 2026) |
| Error-masking constructs | +47% | rescue/null-checks/mock-guards |
| Two-week code churn | +15% | |
| Cross-file function calls (reuse signal) | **−35%** | 343 → 223 method calls per 1,000 changed lines |
| Redundant-vs-refactor preference | ~**5x** toward redundant | was 2x toward refactor in 2022 |

GitClear's framing: *"a generation of repos stuck in 'write-only mode' — growing outward in new v1
features while their older strata calcify untouched."* The New Stack headline: *"Your AI coding spend
bought 25% more output. Duplication rose 81%."*

Prior GitClear study (2025), 211M lines 2021–2025: moved/refactored code fell **25% (2021) → <10% (2025)**;
copy/pasted code rose **8% → 18%** of changes.

**Why this matters for review:** duplication +81% and refactoring −70% are *precisely* the conditions
under which review load per unit of functionality rises and reviewer context must be reconstructed
from scratch. This is the mechanical link between code quality decay and review cost.

**Caveat to state if challenged:** GitClear infers AI authorship from commit metadata/API signals.
Only ~6.4M of 976.2M lines are AI-attributed. The trends are real measurements; the *causal
attribution to AI* is inferential.

### 4.3 Human review of AI PRs is already mostly absent — **STRONG, peer-reviewed**
Duma, Wróblewski, Bobińska, Winiarska, Przymus. *"These Aren't the Reviews You're Looking For: How Humans Review AI-Generated Pull Requests."* **EASE 2026** (Glasgow, June 9–12, 2026).
- https://arxiv.org/pdf/2605.02273

| Metric | Value |
|---|---|
| Corpus | agent-authored PRs from SSAIDev repos (≥100 stars) |
| n agent-authored PRs | **33,596** |
| **Received NO recorded review, or reviewed exclusively by agents** | **84.0%** (28,246) |
| Showed any human participation | **15.9%** (5,350) |
| Agentic share of comments on agent-authored PRs | **72.47%** |
| Human share of comments on human-authored PRs | **44.12%** |
| Significance | χ²(1) = 873.7, p < 10⁻³, V = 0.16 |

The paper notes even **human-authored** PRs frequently receive limited substantive feedback.

### 4.4 Agentic PR acceptance — **MODERATE**
arXiv:2509.14745, *"On the Use of Agentic Coding: An Empirical Study of Pull Requests on GitHub"* — 567 Claude Code–generated PRs across 157 OSS projects.
- Rejection reasons: **"too large / effective review impractical" 3.3%**, "obsolete" 3.3%, **"no confidence in AI-generated code" 1.1%**. 59 of 92 rejected APRs fell into the reported categories; 31 closed with no review comment at all.
- Real example: a solvespace PR closed with *"Closing in favor of smaller, more focused PRs to make reviews more manageable."*

### 4.5 Dev-reported failure modes
**Harness survey, ~May 14, 2026** — 700 developers/managers, US/UK/India/France/Germany.
- https://www.computerweekly.com/news/366643082/Software-developers-shift-to-AI-code-reviewers

| Stat | Value |
|---|---|
| Believe productivity metrics improved | 89% |
| **Spending MORE time reviewing AI-generated source code** | **81%** |
| **Share of a developer's day now consumed by unmeasured "AI-related invisible work"** | **31%** |
| Say reviewing AI-generated code causes the most friction | 53% |
| — of which: fixing subtle bugs in AI code | 52% |
| — of which: **explaining the AI-generated code to teammates** | **48%** |
| Worried about AI tools being used to measure their performance | 96% |
| Say tech debt, validation time, and burnout are missing from their current metrics | 94% |

> The 48% "explaining AI code to teammates" figure is a direct measurement of the **context/explainability
> problem** — and it is a *communication* tax, not a *reading* tax.

**Stack Overflow 2025**: 66% spend more time fixing "almost-right" AI code; 45–66% cite it as top frustration.

**GitLab Nov 2025 report** (Harris Poll, n=3,266): 73% have experienced problems with "vibe coding" code; only 37% would trust AI to handle daily work tasks without human review.
https://about.gitlab.com/press/releases/2025-11-10-gitlab-survey-reveals-the-ai-paradox/

---

## 5. WHY REVIEW IS STRUCTURALLY HARD — the context problem

### 5.1 Reviewer capacity concentrates on whoever holds context — **STRONG (directional)**
LinearB, Sept 9, 2026: *"the same handful of engineers open every review that matters... the work of
judging that code goes to whoever holds the most context about our systems."*
https://linearb.io/blog/engineering-health

Faros 2026: devs handle **67.4% more PR contexts** and **17.7% more task contexts** daily; work
restarts **+13.8%**; stalled tasks **+26%**.

### 5.2 Review quality degrades with diff size — **STRONG**
- GitHub launch research, **1.5M PRs**: PRs of **200–400 lines had 40% fewer defects and were approved 3x faster** than larger. https://www.infoq.com/news/2026/04/github-stacked-prs
- Anthropic's own data: findings rate scales with size — **84% of >1,000-line PRs** produce findings (avg 7.5) vs **31% of <50-line PRs** (avg 0.5). https://claude.com/blog/code-review
- Classic anchor, Cohen/Cisco/SmartBear 2006, 2,500 reviews / 3.2M LOC: optimal review pace **300–500 LOC/hr**; above 500 LOC/hr defect detection collapses; above 1,000 LOC/hr the reviewer is effectively not reading; hard fatigue ceiling at **60–90 minutes**; optimal review size **200–400 LOC**. (Old but still the most-cited empirical basis, and GitHub's 200–400 line finding matches it independently.)
- Bacchelli & Bird (Microsoft, ICSE 2013), 165 surveys + 17 interviews: reviewer familiarity multiplier **×0.60** — knowing the code roughly halves review time. https://dl.acm.org/doi/10.1145/2593791.2593808

### 5.3 Bus factor / knowledge concentration — **MODERATE (academic construct, thin 2026 data)**
- **"Bus factor in practice"**, ICSE-SEIP 2022, survey of **269 engineers**: bus factor is perceived as an important problem in collective development; proposes a multimodal estimator using code review + meeting + VCS data. https://dl.acm.org/doi/10.1145/3510457.3513082
- arXiv:2401.03303, *"Guiding Effort Allocation in Open-Source Software Projects Using Bus Factor Analysis"*: argues most bus-factor algorithms use commit counts, proposes LOCC and change-size-cosine. Finds high-knowledge developers declining through 2022. https://arxiv.org/html/2401.03303
- arXiv:2604.23257 (2026), *"Knowledge Lever Risk Management for Software Engineering"* — frames bus-factor risk as "the most acute and most neglected knowledge risk in software engineering," with LLM-based documentation/ADRs/agentic code review as mitigations. https://arxiv.org/html/2604.23257v1
- **I could not find a credible 2025/2026 quantified survey of enterprise bus factors or onboarding time.** The "onboarding-complexity" GitHub repo and similar tools are hobby projects, not research. Treat onboarding-time claims as WEAK.

### 5.4 Platform-level admission that traceability/context is missing — **STRONG**
GitLab 2026 report: only **28%** say their SDLC tools are fully integrated with shared data and
workflows; **43%** cannot reliably distinguish AI from human code; **39%** have systems that don't
track code origin. GitLab's own definition of "AI accountability" — the three questions almost nobody
can answer about any line of AI code: *where did it come from, what was it meant to do, and who is
responsible once it's in production.*

Anthropic's Code Review architecture explicitly reads linked issues and PRs to *"flag subtle gaps...
including cases where the code looks reasonable in isolation but doesn't match the project's
requirements."* That is a vendor confirming context, not the diff, is what review fails on.

---

## 6. QUANTIFIED COST

### 6.1 Developer cost — **MODERATE**
- **US BLS, SOC 15-1252, May 2025**: median software developer salary **$135,980/yr = $65.38/hr**; mean $148,100; 10th–90th pct $82,460–$214,670; 1,687,890 employed. https://www.bls.gov/oes/current/oes151252.htm (aggregated at https://salarybyjob.com/salary/software-developers)
- **Stack Overflow 2025**: global median developer salary **$71,488**; US Engineering Manager median **$200,000** vs Germany $118,000, India $52,000. https://survey.stackoverflow.co/2025/work
- **Fully-loaded multiplier: I did not find a single authoritative, citable 2025/2026 figure.** Multiple
  secondary sources assert **$75/hr fully-loaded ≈ $150K/yr**, and LinearB/Anthropic-adjacent commentary
  uses **$50–75/hr**. Treat $75–100/hr as a defensible planning assumption; **do not attribute a
  precise multiplier to a named source.**

### 6.2 Cost of defects escaping — **MODERATE, but the source is ancient**
- **IBM Systems Sciences Institute**: 1x design → 6.5x implementation → 15x testing → **60–100x post-release**. This is **1980s–90s research** (commonly attributed to Fiman, 1988) and has been laundered through a decade of SEO content. Use it only for *relative* escalation, never as an absolute dollar figure. Even Black Duck's 2026 blog cites it: https://www.blackduck.com/blog/cost-to-fix-bugs-during-each-sdlc-phase.html
- **NIST 2002**, *Economic Impacts of Inadequate Infrastructure for Software Testing* — the other root source. Both are pre-2020.
- **Modern, defensible anchors instead:**
  - **IBM/Ponemon Cost of a Data Breach 2025**: global average **$4.44M**; US average **$10.22M** (record US high). Shadow-AI incidents added **$200,000** to global average; average breach involving shadow AI cost **$4.63M**; MTTI 62 days, MTTC 185. Shadow-AI incidents took **~1 week longer** to detect/contain. Customer PII most expensive at **$166/record**; company IP most costly at **$178/record**. **#1 factor that reduced breach cost: taking a DevSecOps approach.** https://www.ibm.com/reports/data-breach (PDF: https://na.ingrammicro.com/Ingram/media/North-America-US/EN-US/I/ibm/docs/IBM-cost-of-a-data-breach-2025-full-report.pdf)
  - **Gartner**: ~$5,600/min average downtime cost; ~$100,000/min peak e-commerce. Widely cited but **Gartner is paywalled and I could not verify the primary source.** Do not cite as hard.
  - **CISQ 2022**: cost of poor software quality in the US ≥ **$2.41 trillion**. Real but dated and definitionally loose.

### 6.3 Cost of slow review, per CircleCI
- Slow outer-loop feedback *"could cost teams nearly **$1M a year**"*; inner-loop validation cuts it by >75%. (Q2 2026 Pulse, https://circleci.com/resources/2026-state-of-software-delivery-q2-pulse)
- Median team 12 minutes above CircleCI's 60-min recovery benchmark ≈ **250 hours/year** lost to debugging and blocked deployments. (2026 annual report)
- One report page references *"lose the equivalent of 12 full-time engineers"* — **I could not locate the metric or denominator this refers to in the report body. Do not cite.**

### 6.4 Attrition cost — **NOT VERIFIED**
I did not find a credible, current, citable figure for engineering attrition replacement cost in this
research pass. Widely-quoted Gartner/"50-200% of salary" figures circulate but I could not verify a
primary source. **Flagged as a gap.**

---

## 7. ADJACENT BOTTLENECKS

### 7.1 Security / SCA alert fatigue — **MODERATE**
**Sonatype 2026 State of the Software Supply Chain** (published Jan 28, 2026). Backed by Maven Central telemetry; analyzed 1.233M malicious packages, 1,700+ CVE records, 37,000 AI-driven upgrade recommendations.
- https://www.sonatype.com/press-releases/sonatype-research-reveals-open-malware-grows-75-percent
- https://www.sonatype.com/state-of-the-software-supply-chain/2026/vulnerability-management

| Metric | Value |
|---|---|
| **False positives** (packages incorrectly marked vulnerable) | **20,362** |
| **False negatives** (exploitable components unflagged) | **167,286** — 8.2x worse than false positives |
| Log4Shell downloads in 2025 despite fixes available for 4+ years | **42 million** |
| Avoidable vulnerable downloads across 4 component versions | **~1.8 billion** |
| — commons-lang 2.6, % of avoidable downloads | 99.88% |
| — snappy 0.5 | 99.58% |
| — commons-compress 1.26 | 46.32% |
| — jdom2 2.0.6.1 | 57.73% |
| Open-source malware growth | +75% |
| **IDC (quoted by Sonatype): devs accept ~39% of AI-generated code without revision** | |
| Sonatype Hybrid vs Latest Version upgrade cost | **2.1x lower** |
| Sonatype Hybrid vs LLM/GPT-5 recommendations | **2.7x lower** |

**The false-negative number is the striking one and is under-used: for every false positive that wastes
a developer's time, ~8 exploitable components slip through silently.** That reframes the problem —
the failure mode isn't noisy scanners, it's *miscalibrated* ones.

Veracode on cascade mapping: CVE-2025-66478 was **rejected by NVD as a duplicate of CVE-2025-55182**
because the flaw was in the RSC runtime, not Next.js. Alerting on every downstream wrapper "degrades
security data quality." https://www.veracode.com/blog/decoding-cve-2025-66478-signal-vs-noise-in-sca (Dec 10, 2025)
Veracode 2026 State of Software Security (July 9, 2026) thesis: *"the pace of flaw creation is now
outpacing the capacity to fix them."* https://www.veracode.com/resources/analyst-reports/state-of-software-security-2026
SOC alert false-positive rate: **46–83%** range across sources; 76% of orgs cite alert fatigue as a top
SOC concern. (Range is wide → treat as WEAK.) https://www.secure.com/blog/soc/soc-alerts

**I did NOT find a credible "N SCA alerts per PR" number.** Many sources assert one; none cite a
methodology. Do not use.

### 7.2 Flaky tests — **STRONG (peer-reviewed)**
- **"Cost of Flaky Tests in Continuous Integration: An Industrial Case Study," ICST 2024** — large commercial project, ~30 developers, ~1M SLoC, **five years** of CI logs + VCS + tickets + tracked work time.
  - **≥2.5% of productive developer time** spent on flaky tests
  - Breakdown: investigation 1.1%, repair 1.3%, tooling 0.1%
  - Rerun compute cost: **0.63% of total run time, 347 hours over 6 months — "negligible and inexpensive"** (a direct correction to the common "flaky tests burn CI dollars" claim)
  - https://mediatum.ub.tum.de/doc/1730194/gbm0plj5hiwtahxthafyg16bl.cost-of-flaky-tests-in-ci.pdf
- **Microsoft and Google report 4–16% of tests involve flakiness; 1.5% of CI test runs are flaky.**
- Parry et al., *"A Survey of Flaky Tests,"* ACM TOSEM 31(1), Oct 26, 2021, 76 papers: **59% of developers** report dealing with flaky tests monthly/weekly/daily. **78% of flaky tests are flaky the first time they are written** (Lam et al., FSE 2014). https://dl.acm.org/doi/10.1145/3476105
- EASE 2026: 606 of 810 flaky tests (75%) belong to co-occurring clusters, mean cluster size 13.5.
- Kleore (Mar 28, 2026), 10,000 GitHub Actions runs: 30% of reruns caused by flaky tests; 15–25% of CI compute wasted. **Vendor analysis, no peer review → MODERATE at best.**

### 7.3 Legacy modernization — **MODERATE to WEAK, mostly vendor-sourced**
- **IBM**: COBOL endures in an estimated **250 billion lines** in production. https://www.ibm.com/think/topics/cobol-modernization (Nov 27, 2025, updated Apr 6, 2026)
- **Kyndryl 2025 State of Mainframe Modernization** (Aug 1, 2025): modernization ROI **288–362%**; AI expected to drive **$12.7B cost savings + $19.5B increased revenue** over 3 years; average cost of modernize-on-mainframe fell **$9.1M (2024) → $7.2M (2025)**; 56% *increased* platform usage while mainframe importance dropped 11%; 47% cite restrictive security protocols, 37% regulatory/compliance as AI hurdles; only 23% cite legacy-language skills gaps. https://www.kyndryl.com/content/dam/kyndrylprogram/doc/en/2025/mainframe-modernization-report.pdf
- **Gartner Market Guide** (paywalled): *"Technical debt, lack of business fit and high costs are driving enterprise systems customers to modernize."* https://www.gartner.com/en/documents/5769515
- **UK DWP**: 25M lines of COBOL, ~20M claimants/yr; **four prior modernization attempts failed**, including a full COBOL→Java rewrite; succeeded 2021 with like-to-better automated conversion. https://www.infoworld.com/article/2265785/how-companies-are-moving-on-from-cobol.html
- **Australia, APRA CPS 230** in full effect **July 1, 2026** — operational-resilience deadline that makes unsupported COBOL a compliance problem. (via GEM Corp, Aug 25, 2026 — secondary)
- **"$3 trillion in daily COBOL financial transactions" and "~95% of ATM transactions touch COBOL"** — I could **NOT** verify these against a primary source. They are ubiquitous in vendor content and almost certainly originate from a 2010s Deloitte/NCR estimate. **Do not cite as current fact.**
- **"Technical debt ≈ 40% of average enterprise IT budget"** and **"US orgs spend over $1 trillion/year on IT maintenance"** (Pega) — vendor/consultancy figures with no disclosed methodology. **WEAK.**
- **">$1 trillion" / **Java version debt**: I found **no** credible quantified estimate of Java version-debt remediation effort. **GAP.**

---

## 8. THE 3 STRONGEST, MOST DEFENSIBLE FACTS

### 1. Code generation accelerated; delivery did not — and main-branch throughput actually declined.
**CircleCI 2026 State of Software Delivery** (Feb 18, 2026), 28M CI/CD workflows, 22,000+ orgs, 149 countries.
Median team: feature-branch throughput **+15% YoY**, main-branch throughput **−7% YoY**. Main-branch
success rate **70.8%**, a five-year low, against CircleCI's own 90% benchmark. Average throughput
+59% is real but concentrated: top 5% **+97%**, median **+4%**, bottom quartile **flat**. Q2 2026
pulse: main-branch throughput still **entirely flat** while feature branches +7.7%.
*Why it's the strongest:* it is instrumented behavioral telemetry at enormous scale, not opinions, and
the vendor's own product is the measurement instrument. It also cannot be dismissed as AI
doomerism — the same report shows throughput rising. Corroborated independently by Faros AI (22,000
developers, 4,000 teams: deployments/week **−11.7%**) and by GitHub's own decision to ship Stacked PRs.
**The one-line version:** the bottleneck moved, and it is measurable in the merge path.

### 2. At AI-native organizations, the large majority of PRs get no substantive human review.
Three independent sources, three different methods:
- **Anthropic** (March 9, 2026): before deploying AI review tooling, only **16%** of Anthropic's own PRs
  received substantive review comments. (https://claude.com/blog/code-review)
- **EASE 2026 peer-reviewed study**, 33,596 agent-authored PRs: **84.0%** received no recorded review or
  agent-only review; only **15.9%** showed any human participation. (arXiv:2605.02273)
- **Faros AI 2026**, 4,000 teams: **31% more PRs merging with zero review** than a year earlier.
  (https://faros.ai/research/ai-acceleration-whiplash)

*Why it's the strongest:* it survives vendor-bias attack because the two loudest vendors (Anthropic
selling review tooling, Faros selling analytics) both *incite* the problem, and the peer-reviewed
number comes from neither. It is also the most actionable fact in the dossier — it says the failure
mode is **evasion of review**, not overload of it, which implies the product opportunity is
*increasing* effective review coverage rather than *speeding up* review.

### 3. The context problem is real, documented, and unaddressed.
- **GitHub**, launching Stacked PRs (April 2026): *"Reviewers lose context, feedback quality drops, and
  the whole team slows down."* Cited research on 1.5M PRs: 200–400-line PRs have **40% fewer defects**
  and are approved **3x faster**.
- **Anthropic**: findings rate scales with diff size — **84%** of >1,000-line PRs produce findings
  (avg 7.5) vs **31%** of <50-line PRs (avg 0.5).
- **Microsoft/ICSE 2013** (Bacchelli & Bird, 165 surveys + 17 interviews): reviewer familiarity is
  worth a **×0.60** time multiplier — knowing the code roughly halves the work.
- **LinearB**, Sept 2026: *"the same handful of engineers open every review that matters... the work of
  judging that code goes to whoever holds the most context about your systems."*
- **Harness 2026**: **48%** of devs say their biggest AI friction is **explaining AI-generated code to
  teammates** — a communication tax, not a reading tax.
- **GitLab 2026**: only **28%** of orgs have fully integrated SDLC tooling; **43%** cannot distinguish
  AI from human code in their own repo.

*Why it's the strongest:* it's the one claim where vendors with mutually incompatible businesses
(GitHub, Anthropic, LinearB, Harness, GitLab) all independently point the same direction, and it's
supported by the oldest and most robust finding in software engineering (reviewer familiarity and diff
size). If you build for context, you are not betting on one vendor's narrative.

**Runner-up, if you want a fourth:** LinearB's 8.1M-PR dataset — AI PRs merge within 30 days only
**32.7%** of the time vs **84.4%** for unassisted PRs, and wait **4.6x longer** for pickup (16+ hrs vs
~200 min). This is the cleanest single "AI code is systematically rejected downstream" number available.

---

## 9. GAPS — WHAT I COULD NOT VERIFY

| Claim I was asked about | Status |
|---|---|
| **"AI is a thief of time" as a DORA finding/phrase** | **Could not find any DORA report using this phrase.** DORA's actual 2025 language is the "verification tax" and "amplifier" framing (https://dora.dev/insights/balancing-ai-tensions). Do not attribute this phrase to DORA. |
| **IBM's original survey** | Fully resolved — it is GitLab's 2026 AI Accountability Report, Harris Poll, n=1,528, June 23, 2026. IBM is a secondary citer. |
| **Authoritative fully-loaded developer cost multiplier** ($/hr) | Not found. BLS base median is $65.38/hr (May 2025); $75–100/hr fully loaded is a reasonable assumption but I could not attribute a multiplier to a credible named source. |
| **Engineering attrition / replacement cost** | Not found in this pass. Do not use a "50–200% of salary" figure without a primary source. |
| **"N SCA alerts per PR"** | No credible figure with disclosed methodology exists that I could find. Do not use. |
| **% of SCA alerts that are false positives** | Only a very wide range (46–83%, mostly SOC not SCA) and vendor-specific counts (Sonatype: 20,362 FP / 167,286 FN). Not a generalizable rate. |
| **GitClear's "lose the equivalent of 12 full-time engineers"** | Quoted in a CircleCI report page but the metric/denominator is not located in the report body. Do not cite. |
| **CodeRabbit "AI code introduces 15–18% more security vulnerabilities, 1.7x more issues"** | Appears only in a forum post (tianpan.co). Could not verify at CodeRabbit. Do not use. |
| **"Salesforce internal findings: PRs regularly exceed 1,000 lines, reviewers stop engaging"** | Sourced to a Medium article. Could not verify at Salesforce. Do not use. |
| **"Opsera: 250,000+ developers across 60+ enterprises, AI PRs wait 4.6x longer"** | The 4.6x figure is real but belongs to **LinearB**, not Opsera. Content farms conflated them. Do not attribute to Opsera. |
| **"Anthropic: substantive review comments rose 16% → 84% on >1,000-line PRs"** | **Misattributed.** Anthropic's real numbers: substantive review comments rose **16% → 54% overall**; **84%** is the share of >1,000-line PRs that *received findings*. Two different statistics merged by content farms. |
| **"Sameen Karim (GitHub): 'The bottleneck is no longer writing code — it's reviewing it'"** | Quote appears **only** in dev.to content-farm posts. Not in InfoQ, InfoWorld, GitHub's changelog, or Karim's own posts. **Unverified — do not quote.** GitHub's *written* position is verified (the "reviewers lose context" language). |
| **"$3 trillion daily COBOL transactions" / "95% of ATM transactions touch COBOL"** | Ubiquitous in vendor content; no primary source found. Almost certainly a 2010s estimate recirculated. Do not cite as current. |
| **"Technical debt = 40% of enterprise IT budget"** | Consultancy figure, no methodology disclosed. WEAK. |
| **Java version debt, quantified** | No credible estimate found. **GAP.** |
| **Enterprise bus factor / onboarding time, quantified, 2025–2026** | Academic work exists (ICSE-SEIP 2022, n=269; arXiv:2401.03303) but no current quantified enterprise survey. The GitHub "onboarding-complexity" tools are hobby projects. **GAP.** |
| **Round-2 METR results (late-2025 RCT) as a citable point estimate** | Published as an *update* with explicit selection-effect caveats: panel devs −18% (CI −38% to +9%), new devs −4% (CI −15% to +9%). METR calls it "very weak evidence for the size of this increase." Reportable as a range with the caveat, not as a point estimate. |
| **SWE-bench / CodeScene evidence for this thesis** | Not researched in this pass. CodeScene was not found to have published a primary 2025/26 study on review load. **GAP.** |
| **GitClear AI-attribution methodology** | AI authorship is *inferred* from commit author/API signals; only ~6.4M of 976.2M evaluated lines are AI-attributed. Trends are measured; causal attribution to AI is inferential. State this if challenged. |

---

## 10. HOW TO USE THIS IN A PITCH (recommended framing)

**Do:**
- Lead with **CircleCI's feature-branch +15% / main-branch −7% split**. It is the single most
  credible, most concrete, most non-ideological fact you have.
- Lead with **84% of Anthropic's PRs got no substantive review** and **84.0% of agent-authored PRs
  in the EASE study got no human review**. Two independent 84%s, different methods, both pointing at
  *evasion* rather than *overload*.
- Use the **context framing**, not the speed framing. GitHub, Anthropic, LinearB, and Harness all
  independently say reviewers lack context, not that they lack speed. A tool that makes review faster
  competes with a saturated market (GitHub, Copilot, Claude Code Review, CodeRabbit, Qodo). A tool
  that makes review *possible* on code you don't understand is a different category.
- Attribute the 85% honestly: "GitLab/Harris Poll, n=1,528, vendor-commissioned, attitudinal."

**Don't:**
- Don't cite METR's 19% slowdown. It is retracted by METR.
- Don't cite DORA 2024's throughput decline without acknowledging DORA 2025 reversed it. The
  instability finding (−7.2%) survived and is the safe part.
- Don't cite IBM SSI defect-cost multipliers as dollar figures.
- Don't quote the 4.6x/16.7%/32.7% LinearB numbers without noting LinearB is a vendor selling the
  category — though at 8.1M PRs it's hard to dismiss.
- Don't let a judge catch you citing a content-farm number. The dev.to "code-board" posts, the
  neuroxai/byteiota/tech-insider aggregators, and the tianpan.co forum thread are **AI-generated
  SEO farms** that fabricate plausible-sounding statistics and attribute them to real reports with
  the details mangled. Several numbers in your original brief (Index.dev's 98%, "AI Engineering
  Report 2026" 441%, Anthropic's 16%→84%) trace to these farms. The underlying *reports* are real
  (Faros, LinearB, Anthropic) but the farms' restatements of them are wrong.
