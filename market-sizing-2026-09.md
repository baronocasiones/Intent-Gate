# Market Sizing: Intent Attestation for IBM Z / Regulated Enterprise

**Compiled 26 September 2026.** Companion to `evidence-dossier.md` and `ai-code-review-landscape-2026-09.md`. This document does one thing: assemble defensible, sourced figures for a TAM/SAM/SOM model, and show the arithmetic. Where a number is weak, it is labelled weak.

---

## 0. Method and confidence taxonomy

| Label | Meaning |
|---|---|
| **[F]** | **First-party primary.** The organisation's own filing, earnings call, press release, or government publication. Citable in a board deck without hedging. |
| **[S]** | **Specialist analyst.** Gartner, IDC, Forrester, Everest, Verdantix, SlashData, ISBSG, METI, GAO, McKinsey/Oxford, academic papers. Methodology generally undisclosed but the firm is accountable. |
| **[W]** | **Weak / vendor-commissioned / content-marketing.** A vendor selling the thing being measured, an agency publishing its own benchmark, or an SEO content farm. Directional only. Do not build a model on these. |
| **[X]** | **Unverified.** Could not confirm against any primary source. Treat as absent. |

**Three ground rules applied:**

1. **IBM and Micro Focus TAM claims are quoted as their claims, not as facts.** IBM is a reliable primary source *for what IBM believes about its market*. It is not a neutral estimator, and in several cases its claims are internally inconsistent (see A2: 70% vs 87% transaction share; A7: Blue Pearl).
2. **When a figure has three variants in circulation, all three are shown** (A3 COBOL lines; C17 Bob plan prices; D19 Blue Pearl). In two of those three cases the widely-repeated version is the *least* defensible one.
3. **A gap is stated as a gap.** The "Gaps" section is load-bearing, not a disclaimer.

---

# A. The mainframe / IBM Z estate

## A1. How many enterprises run mainframes?

| Figure | Value | Source | Date | Confidence | URL |
|---|---|---|---|---|---|
| Share of Fortune 500 using mainframes | **71%** | IBM (via Brainstorm/ITWeb) | Mar 2025 | **[F]** as IBM claim | https://brainstorm.itweb.co.za/article/sixty-years-on-the-mainframe-turns-hybrid/rW1xL75nwmQMRk6m |
| Share of Fortune 500 using mainframes | **70%+** | IDC Financial Insights (Jerry Silva) | Nov 2023 | **[S]** | https://www.rocketsoftware.com/sites/default/files/resource_files/idc-report-mainframe-financial-services.pdf |
| Share of Fortune 500 | **>70%** | Forbes, restating IBM IBV ("Rutten") | Nov 2024 | **[W]** | https://www.forbes.com/sites/heatherwishartsmith/2024/11/12/mainframes-the-backbone-of-the-worldwide-economy/ |
| Older vintages in circulation | 64% / 71% / 83% / 92% all appear | Planet Mainframe quiz | Nov 2023 | **[X]** unresolved | https://planetmainframe.com/2023/11/mainframes-by-the-numbers/ |
| **Financial-services penetration** | **>90%** of FS organisations use the mainframe | IDC Financial Insights | Nov 2023 | **[S]** | https://www.rocketsoftware.com/sites/default/files/resource_files/idc-report-mainframe-financial-services.pdf |
| Top-50 banks on mainframes | **44 of 50** | IBM | 2025–26, repeated | **[F]** as IBM claim | https://www.ibm.com/think/news/world-runs-on-mainframes |
| Top-10 insurers | **All 10** | IBM | 2025–26, repeated | **[F]** as IBM claim | same |
| "9 of top 10 banks, 8 of top 10 insurers, 7 of top 10 retailers, 8 of 10 airlines" | — | ReadyContacts | Aug 2026 | **[X]** unverified | https://www.readycontacts.com/target-account-profiling/ibm-system-z-mainframe/ |

**The behavioural datapoint that matters more than penetration rate:**

| Metric | Value | Source | Date | Confidence |
|---|---|---|---|---|
| Mainframe users expecting ≥5 years of continued reliance | **88%** (n=510) | IDC *State of the Modern Mainframe* | Jun 2025 | **[S]** |
| Relying on IBM Z | **89%** (n=510) | IDC, same | Jun 2025 | **[S]** |
| Running z/OS | **65%** (n=510) | IDC, same | Jun 2025 | **[S]** |
| Plan to improve mainframe data integration for AI within 2 yrs | **82%** (n=510) | IDC, same | Jun 2025 | **[S]** |
| Plan to **expand** mainframe use cases | **54%** | Forrester *State of Mainframe Global 2024* | May 2025 | **[S]** |
| Plan to **reduce** mainframe reliance | **15%** | Forrester, same | May 2025 | **[S]** |
| US banks expecting ≥50% of workloads on dedicated on-prem mainframes through 2025 | **20%** | IDC FI Nov 2023 NA Banking Tech Survey | Nov 2023 | **[S]** |

URLs: https://www.kyndryl.com/content/dam/kyndrylprogram/doc/en/2026/idc-worldwide-mainframe-modernization-infrastructure.pdf · https://www.forrester.com/report/the-state-of-mainframe-global-2025/RES183032

**Read this carefully, because it is a bear-case correction to the thesis.** Forrester's own 2025 report states mainframe *footprints are growing* and *the staffing crisis is not as bad as it was projected to be*. **Do not build a model on "mainframes are dying."** The spend is durable and expanding; the reframe required is that the money is going into *staying and extending*, not exiting.

## A2. IBM Z installed base and revenue

### Revenue — what IBM actually discloses

| Figure | Value | Source | Date | Confidence |
|---|---|---|---|---|
| IBM total revenue | **$67.5B** (FY2025) | IBM 2025 Annual Report / 10-K | FY2025 | **[F]** |
| Infrastructure segment revenue | **$15,718M** (FY2025), +12.1% rep. / +10.4% cc | IBM 10-K segment table | FY2025 | **[F]** |
| Hybrid Infrastructure revenue | **$10,618M** (FY2025), +19.1% rep. / +16.9% cc | IBM 10-K MD&A | FY2025 | **[F]** |
| **IBM Z revenue growth** | **+51.7% as reported / +48.4% cc (FY2025)** | IBM 10-K MD&A | FY2025 | **[F]** |
| IBM Z revenue, **absolute dollars** | **NOT DISCLOSED** — IBM gives % change only | — | — | **GAP** |
| IBM Z 4Q25 | **+61% y/y**, highest Q4 in >20 years | IBM 4Q25 earnings | Jan 2026 | **[F]** |
| IBM Z FY2025 characterisation | "highest annual revenue for IBM Z in about 20 years" | IBM 4Q25 prepared remarks | Jan 2026 | **[F]** |
| **IBM Z 2Q26** | **−42% y/y**; Infrastructure −7% | IBM 2Q26 earnings call | 22 Jul 2026 | **[F]** |
| z17 programme-to-programme | **~130% of z16** at same cycle point | IBM 2Q26 call | 22 Jul 2026 | **[F]** |
| FY2026 Infrastructure guidance | Down low single digits | IBM 4Q25 remarks | Jan 2026 | **[F]** |
| IBM Software ARR | **$23.6B**, up >$2B from end-2024 | IBM 4Q25 remarks | Jan 2026 | **[F]** |

URLs: https://www.sec.gov/Archives/edgar/data/51143/000005114326000027/ibmars2025.pdf · https://www.sec.gov/Archives/edgar/data/51143/000005114326000010/R39.htm · https://www.sec.gov/Archives/edgar/data/51143/000005114326000010/ibm-20251231.htm · https://www.ibm.com/downloads/documents/us-en/1550f7eea8c0ded5 · https://www-api.ibm.com/adobe/assets/urn:aaid:aem:6d33af85-88a3-4750-928b-79d7ad7d8b63/original/as/4q25-prepared-remarks.pdf · https://www.networkworld.com/article/4200347/despite-tough-quarter-ibm-says-mainframe-will-continue-to-put-the-big-in-big-blue.html

> **The 2Q26 −42% is the most important number in this section.** Anyone claiming "IBM Z is booming" is reading FY2025 and missing the current run-rate. Anyone claiming "IBM Z is collapsing" is ignoring that IBM Z is a lumpy programme-to-programme hardware business that IBM explicitly framed as the strongest cycle on record. **Honest characterisation: installed base stable-to-growing, hardware revenue extremely lumpy, Transaction Processing software inflecting back to +4% growth.**

### Installed base — capacity, not unit counts

| Metric | Value | Source | Date | Confidence |
|---|---|---|---|---|
| **Installed MIPS on IBM Z** | **>140 million MIPS** | IBM 2Q26 call (Krishna) | 22 Jul 2026 | **[F]** |
| Share of installed MIPS stable or growing | **85%** | IBM 2Q26 call (Kavanaugh) | 22 Jul 2026 | **[F]** |
| z17 customers investing in AI via Spyre Accelerator | **~50%** | IBM 2Q26 call | 22 Jul 2026 | **[F]** |
| MIPS growth among watsonx Code Assistant for Z deployers | **3× faster** than non-deployers | IBM 2Q26 call | 22 Jul 2026 | **[F]** but vendor claim about own product |
| Transaction value on mainframe | **>70% of global transaction volume by value** | IBM 2Q26 call | 22 Jul 2026 | **[F]** as IBM claim |
| Same, 10-K language | "mainframes handling **70% of the world's transactional workflows** (IBM IBV)" | IBM 2025 Annual Report | FY2025 | **[F]** as IBM claim |
| Transactions processed | **87% of all transactions in the world** | IBM Think | 4 Jun 2026 | **[F]** as IBM claim — **conflicts with the 70% figures above** |
| Credit-card transactions | **90%** | IBM via Brainstorm | Mar 2025 | **[F]** as IBM claim |
| Share of world IT production workloads | **68%**; 6% of IT expenditure | IBM via multiple | 2023–25 | **[F]** as IBM claim |
| IBM Z share of mainframe market by revenue | **63.25% (2025)** | Mordor Intelligence | 2026 | **[S]** |
| Large organisations' share of mainframe market | **82.34% (2025)** | Mordor Intelligence | 2026 | **[S]** |

https://zolmax.com/investing/international-business-machines-q2-earnings-call-highlights/11923198.html · https://www.ibm.com/think/news/world-runs-on-mainframes · https://gtsgservices.net/navigating-modernization-complexity-truly-unbiased-mainframe-experts-want-to-help/ · https://www.mordorintelligence.com/industry-reports/mainframe-market

**Note the internal IBM inconsistency (70% of transactional workflows / 70% of transaction value vs 87% of all transactions).** These are not reconcilable without knowing IBM's denominators. Pick one, attribute it, and don't mix them.

### Installed base — enterprise counts are not published, and vendors disagree 5.6×

| Technographic vendor | Claimed IBM Z / z/OS organisations | Date | Confidence | URL |
|---|---|---|---|---|
| Landbase | **2,844** | 2026 | **[W]** | https://data.landbase.com/technology/ibm-z-os/ |
| ELP Data | **6,276** (20,083 contacts; 1,569+ with 5,000+ employees; 140 countries) | 2026 | **[W]** | https://www.elpdata.com/ibm-zos-users-list |
| ReadyContacts | **15,957** | Aug 2026 | **[W]** | https://www.readycontacts.com/target-account-profiling/ibm-system-z-mainframe/ |
| IBM itself | **Does not disclose** customer counts | — | **GAP** | — |

**A 5.6× spread means nobody knows the denominator.** Any TAM starting from "number of IBM Z enterprises" inherits that uncertainty immediately. This is why the derived model below runs as a range and cross-checks top-down.

**Useful firmographic datapoint 1 — geography** (ELP Data **[W]**):

| Region | Share of z/OS deployments |
|---|---|
| United States | **44%** |
| United Kingdom | **11%** |
| Germany | **9%** |
| Canada | **8%** |
| Australia | **7%** |
| Rest of world | **21%** |

*Caveat: ELP's methods (tech detection, job postings, directories, conference registration) systematically over-detect large enterprises with web presence and under-detect small ones.*

**Useful firmographic datapoint 2 — size** (AppsRunTheWorld **[W]**):

| Employee band | Share of IBM Z customers |
|---|---|
| 10,000+ | **47.92%** |
| 1,001–10,000 | **45.83%** |
| 101–1,000 | **6.25%** |
| 0–100 | **0%** |

https://www.appsruntheworld.com/customers-database/products/view/ibm-z-systems

**Derived: 93.75% of IBM Z customers have >1,000 employees.** This is load-bearing for the SAM funnel, because it means your ">1,000 employees" serviceability filter removes almost nothing.

## A3. COBOL in production — "1.5 trillion lines" is a misreading

### The debunk, stated precisely

**There is no credible source for "1.5 trillion lines of COBOL."** The figure is a garbled IBM *token count*:

> *"These solutions will be powered by IBM's watsonx.ai code model, which will have knowledge of 115 coding languages having learned from **1.5 trillion tokens**."*
> — IBM newsroom, 22 August 2023 **[F]**
> https://newsroom.ibm.com/2023-08-22-IBM-Unveils-watsonx-Generative-AI-Capabilities-to-Accelerate-Mainframe-Application-Modernization

1.5 trillion **tokens** (words and word-parts, 115 languages) is not 1.5 trillion **lines of COBOL**. IBM Granite was subsequently trained on **1.6 trillion code tokens** — again tokens, again all languages. **[F]** https://research.ibm.com/blog/cobol-java-ibm-z

**Citing "1.5 trillion lines of COBOL" in a deck is a cheap way to lose the room.** An informed reviewer will identify it as an error and stop trusting the rest of the model.

### What is actually published

| Estimate | Lines | Primary source | Date | What it measures | Confidence |
|---|---|---|---|---|---|
| **Vanson Bourne / Micro Focus** | **775–850B** (midpoint ~800B) | Vanson Bourne, "Size of COBOL" | **Feb 2022** | **Explicitly production code.** Survey brief: "Consider only code that is in production… taking into account duplicate code." Weighted by respondent confidence and Micro Focus platform shares. n=1,104, 47 countries, quantitative. | **[S]** — best available |
| Reuters / Forrester (Phil Murphy) | 220B | Reuters citing Forrester | 2017 | Active COBOL | **[S]** |
| ACT-IAC *Legacy Code Modernization* | 240B | ACT-IAC | 2020 | COBOL "still in active operation" | **[S]** |
| IBM (Tom Ross, "Captain COBOL") | 220B | IBM Z & LinuxONE podcast | Nov 2023 | COBOL processing $3T of commerce daily | **[F]** as IBM claim |
| OpenText (via tech-stack.com) | 220B | attributed, unsourced | 2023 | "active production globally" | **[X]** |
| IBM, per average enterprise | **"tens of millions"** of COBOL lines in production | IBM via CIO Dive | Aug 2023 | Per-enterprise | **[F]** as IBM claim |
| IBM, global addressable | **"estimated billions of lines of COBOL code as potential candidates for targeted modernization"** | IBM newsroom | 22 Aug 2023 | Conversion-addressable subset | **[F]** as IBM claim |
| Dataintelo | "over $1.2 billion spent on mainframe modernisation globally in 2025" | Dataintelo | 2026 | — | **[X]** contradicts everything; discard |

URLs: https://www.vansonbourne.com/case-studies/size-of-cobol/ · https://geoinvesting.com/wp-content/uploads/2024/01/how-much-cobol-is-really-out-there_819568.pdf · https://www.isbsg.org/wp-content/uploads/2022/12/Short-Paper-2022-12-Cobol-Projects-%E2%80%93-do-they-still-exist.pdf · https://www.thestack.technology/cobol-in-daily-use/ · https://castro.fm/episode/JcJLgr

### The honest read

The credible range for **in-production** COBOL is **220B (2017) → 240B (2020) → 775–850B (2022)** — a **3.5× spread over five years**, not resolvable with public data. The 2022 figure is the best designed (explicitly production-only, weighted by respondent doubt, n=1,104) **but it is vendor-commissioned, and the Vanson Bourne case study states the commercial motive in plain language**: Micro Focus wanted to *"'own' the COBOL space by updating this number."* That is a real conflict and it inflates versus the 220–240B cluster.

**Recommendation:** write **"220–850 billion lines, most likely several hundred billion"** externally; cite Vanson Bourne for the upper bound and Reuters/ACT-IAC for the lower; never pick a point estimate without labelling it.

Corroborating detail from the same survey **[S]**: 92% of respondents describe their COBOL applications as strategic; 64% intend to **modernize** rather than rip-and-replace; 72% see modernisation as overall business strategy; ~48% expect COBOL volume to **increase** over the next 12 months; 52% expect COBOL apps to remain ≥ a decade; >4 in 5 expect COBOL in use when they retire.

## A4. COBOL developer population and the skills shortage

**No credible current count exists.** Every number traces to one of three places, all stale or methodologically broken.

| Figure | Value | Source | Date | Confidence | Assessment |
|---|---|---|---|---|---|
| Global COBOL developers | **~2 million** | Gartner | **2004** | **[X]** | 22 years old, never re-counted. Origin of the "wild figures." |
| Global COBOL workforce | **800,000–2M** | "late 2010s industry estimates" | late 2010s | **[X]** | Mixes specialists with occasional COBOL users |
| US COBOL developers | **~24,000** | Riem.ai (vendor blog) | Apr 2026 | **[W]** | No methodology |
| Average COBOL developer age | **58** | Phil Teplitzky mainframe workforce study | **2019** | **[S]**, 7 yrs stale | Most-cited demographic claim in the industry; a 2019 number quoted as current in 2026 |
| Annual retirement rate | **~10%** | Teplitzky, same | 2019 | **[S]**, stale | Same |
| Unfilled mainframe positions | **84,000** (as of 2020) | ACT-IAC | 2020 | **[S]**, 6 yrs stale | Pre-dates post-pandemic surge |
| BLS computer-programmer employment | **−6% projected 2024–34**; ~5,500 openings/yr, almost all replacement | US BLS | 2024 proj. | **[F]** | BLS cannot isolate COBOL from "Computer Programmers" |
| Mainframe teams understaffed | **71%**; 54% underfunded | BizTech Magazine | late 2025 | **[W]** | n not disclosed |
| Struggle to find right blend of modernisation skills | **70%** | Kyndryl State of Mainframe Modernisation 2025 | 2025 | **[W]** | Vendor survey |
| Mainframe talent = top challenge | **79%** | "Deloitte/Forrester" via VentureBeat via VALiNTRY | 2025 | **[X]** | Second-hand; I could not find the Deloitte or Forrester primary |
| **"92% of COBOL developers retired by 2027"** | 92% | entrans.ai + a dozen content farms | 2026 | **[X] UNSOURCED** | Widely repeated, **zero primary source found. Do not use.** |
| IBM Z Academic Initiative | **120+ schools**; Master the Mainframe **4,286 cumulative grads** | IBM via Riem.ai | 2026 | **[W]** | The real argument: pipeline throughput vs ~2,400 US retirements/yr |

### Wage data — the "premium" is not cleanly measurable

| Source | Figure | Date | Confidence |
|---|---|---|---|
| ZipRecruiter | avg **$115,475**; 25th–75th $100K–$136K; COBOL Engineer $118,624 | Mar 2026 | **[W]** — skews to high-cost metros and contract roles |
| Salary.com | avg **$81,538**; 25th–75th $73,055–$89,028; Senior (5–8yr) $127,142 | Jun 2026 | **[W]** — employer-reported base salaries, permanent staff |
| Zippia trend | **$75,997 (2021) → $84,879 (2025)**, +11.7% / ~2.8% annualised | 2025 | **[W]** |
| Coursera/Glassdoor | mainframe developer median total comp **$120,000** | Sep 2026 | **[W]** |
| Contract rates | $50–83/hr (Riem.ai); $75–125/hr standard and $125–200/hr specialised (DataField); $150–250/hr (tech-stack) | 2026 | **[W]** — all conflict |
| Contractor markup over FTE | **30–40%**; staffing-firm markup **40–60%** | 2026 | **[W]** |
| **GAO finding — the only [F] item** | ≥**10 federal agencies** had persistent difficulty recruiting COBOL staff and were **paying premium contractor rates** for routine maintenance | **Feb 2022** | **[F]** but I did not retrieve the GAO report number — **verify before citing** |

https://www.hypercubic.ai/insights/cobol-job-postings-over-time-salary-trends-and-which-industries-are-still-hiring · https://www.salary.com/research/salary/recruiting/cobol-programmer-salary · https://www.zippia.com/cobol-programmer-jobs/demographics/ · https://www.coursera.org/articles/mainframe-developer-salary

**Honest conclusion on A4:** salary data spans **$81,538 to $120,000** for nominally the same role depending on methodology — the two most-cited platforms disagree by 42%. That is a **measurement artefact, not a scarcity premium**. The defensible claims are: (a) the workforce is old and shrinking; (b) contractors cost 30–60% more than FTE; (c) GAO confirms federal agencies pay premium rates. **Do not build a model on "COBOL devs earn 40% more."** The 2016 CIO piece is refreshingly honest: *"there's not much evidence that COBOL developers command elevated salaries due to a shortage of supply — yet."*

## A5. Mainframe modernisation market size — estimates disagree by 2.2×

| Analyst | Base | Base size | Forecast | CAGR | Date | Confidence | URL |
|---|---|---|---|---|---|---|---|
| **MarketsandMarkets** | 2025 | **$8.39B** | $13.34B (2030) | 9.7% | 2026 | **[S]** | https://www.marketsandmarkets.com/Market-Reports/mainframe-modernization-market-52477.html |
| **Straits Research** | 2025 | **$8.23B** | $18.42–18.63B (2034); $9.01B (2026) | 9.5% | Aug 2026 | **[S]** | https://straitsresearch.com/report/mainframe-modernization-market |
| **The Business Research Company** | 2025 | **$18.12B** | $20.85B (2026); $36.18B (2030) | **15.1%** | Feb 2026 | **[S]** | https://www.thebusinessresearchcompany.com/report/mainframe-modernization-global-market-report |
| Datainsights | 2025 | $8.39B | $18.59B (2034) | 9.7% | Aug 2026 | **[S]** | https://www.datainsightsmarket.com/reports/mainframe-modernization-1947311 |
| Mordor (*mainframe hardware*) | 2025 | ~$4.33B | ~$7.54B (2031) | ~9.7% | 2026 | **[S]** | https://www.mordorintelligence.com/industry-reports/mainframe-market |
| Dataintelo | 2025 | $4.8B | $8.3B (2034) | 6.3% | 2026 | **[X]** AI-generated prose, internally inconsistent | https://dataintelo.com/report/global-mainframe-market |
| **IDC Financial Insights** | 2025 | **$2.3B** — *mainframe platforms, financial institutions only* | — | <10% p.a. | Nov 2023 | **[S]** | https://www.rocketsoftware.com/sites/default/files/resource_files/idc-report-mainframe-financial-services.pdf |
| **Gartner** | — | Market Guide exists, **no public size** | — | — | 17 Sep 2024 | **[F]** category exists | https://www.gartner.com/en/documents/5769515 |
| **Everest Group** | — | PEAK Matrix exists, **no public size**; $6,499, 18 providers | — | — | 2 Jul 2026 | **[F]** category exists | https://www.everestgrp.com/report/egr-2026-29-r-8245/ |
| **IDC MarketScape** | — | Infrastructure solutions, 7 providers, Z only | — | — | 2025–26 | **[F]** category exists | https://www.kyndryl.com/content/dam/kyndrylprogram/doc/en/2026/idc-worldwide-mainframe-modernization-infrastructure.pdf |

**The $18.12B outlier.** TBRC is **2.2×** MarketsandMarkets and Straits for the same market and year. Three firms clustering at $8.2–8.4B against one at $18.1B means either a materially broader definition or an error. **Use the $8.2–8.4B cluster.** Note TBRC also reports $50.72B for "governance, compliance and risk management software" (§B11) — the same inflation pattern, suggesting a definitional habit rather than a one-off.

**Gartner's most quotable mainframe claim** — and it is a *negative* market claim, which is why it matters:

> *"By 2030, 75% of vendors operating in the 'mainframe exit' market will either pivot their business models or cease to exist."* — Gartner, cited by IBM, 4 June 2026 **[S]**
> *"for most large-scale enterprises, the sheer volume and interconnected complexity of this data make wholesale migration a physical and financial impossibility."*
> https://www.ibm.com/think/news/world-runs-on-mainframes

**This is the strongest single argument for your beachhead.** A Gartner prediction that 75% of mainframe-exit vendors fail by 2030 is a prediction that **mainframe exit is not a market** — therefore the money is in staying, extending and governing.

## A6. Undocumented applications and project overrun

### The percentage that will not go in your deck

**I could not find any credible analyst or survey figure for "what % of mainframe applications are undocumented."** Everything in circulation traces to one AI-generated content cluster (entrans.ai, replay.build, softwaremodernizationservices.com) recycling the same unsourced numbers:

| Claim | Status |
|---|---|
| "70% of legacy rewrites fail or exceed their timeline" | **[X]** UNSOURCED |
| "92% of failed projects trace to incomplete business logic mapping (Gartner Advisory 2023)" | **[X]** — no such Gartner publication located |
| "72% of these apps have rules that no one wrote down" | **[X]** UNSOURCED |
| "67% of these systems still lack any usable documentation" | **[X]** UNSOURCED |
| "40 hours per screen to document a 3270 green screen" | **[X]** UNSOURCED |
| "49% of projects fail because the current state was not mapped" | **[X]** UNSOURCED |
| "+287% average budget overrun; +22.4 months" | **[X]** UNSOURCED |
| "66% of 29 migrations failed to meet goals" | **[X]** UNSOURCED |
| "92% of COBOL developers retired by 2027" | **[X]** UNSOURCED |

**Do not put any of these in a deck.** If asked for the source, there isn't one.

### What *is* sourced — and it is better

**METI (Japan) — a government primary source, and the strongest in this section:**

| Finding | Value | Date | Confidence |
|---|---|---|---|
| Japanese user companies still holding legacy systems | **61%** | 28 May 2025 | **[F]** |
| Among large enterprises | **74%** | 28 May 2025 | **[F]** |
| Method | ~4,000 companies surveyed, **799 responses**, fielded 17 Dec 2024 – 14 Feb 2025 | 28 May 2025 | **[F]** |
| **"ブラックボックス化" (black-boxing) is one of FIVE defining characteristics of a legacy system** in METI's own definition | p.7 | 28 May 2025 | **[F]** |

METI's five factors define a legacy system partly by: specifications and design documents not maintained, migration/rebuild obstructed, and maintenance becoming dependent on specific individuals. **A national government has formally defined "undocumented" as a defining property of legacy systems.** Far stronger footing than any vendor percentage, and fully citable. Report index: https://ipa.go.jp — English summary and page citations: https://aktsk.ai/en/blog/3117/

**Forrester (vendor-commissioned, but real primary research):**

| Finding | Value | Date | Confidence |
|---|---|---|---|
| Mainframe rewrite projects that **fail on first attempt** | **9 in 10** | Sept 2024, reported 24 Sep 2024 | **[S]**, conflict flagged |
| Respondents whose digital transformation was stalled by multiple migration failures | **>50%** | same | **[S]**, conflict flagged |
| Respondents who said they would remove applications from mainframes | **~25%** | same | **[S]**, conflict flagged |
| Most-cited causes | mainframe skills gaps, complex integration, inadequate tooling | same | **[S]** |

https://www.ciodive.com/news/mainframe-application-modernization-hybrid-cloud/727958/
*Source: Forrester survey of 300+ IT professionals **commissioned by Rocket Software**, which sells mainframe-modernisation tooling. A vendor-sponsored study finding 90% of rewrites fail is commercially convenient. The sample and the finding remain usable if disclosed as sponsored.*

**McKinsey + University of Oxford — the best project-overrun data available:**

| Metric | Value | Confidence |
|---|---|---|
| Projects studied | **5,400+** IT projects | **[S]** |
| Avg budget overrun, projects >$15M initial budget | **45%** | **[S]** |
| Avg schedule overrun, same cohort | **7%** | **[S]** |
| Value delivered vs predicted | **56% less** | **[S]** |
| Aggregate cost overruns across sample | **$66 billion** | **[S]** |
| Projects overrunning >200% and threatening company existence | **17%** | **[S]** |
| Overall software project outcomes | 31% successful / 50% challenged / 19% failed (Standish CHAOS 2020) | **[S]**, proprietary via secondary |

https://pmworldlibrary.net/wp-content/uploads/2026/01/pmwj160-Jan2026-Arcidiacono-research-on-IT-project-failure-rate-2025-update.pdf · secondary with McKinsey/Oxford figures: https://sthenostechnologies.com/legacy-modernization-cost-risk-2026/

**Documentation cost — the most useful number in this section:**

| Finding | Value | Date | Confidence |
|---|---|---|---|
| A COBOL invoice system handling **€4.5B revenue** was supported by **two COBOL developers**, one retiring, and **had no documentation** | — | Jul 2024 | **[W]** — vendor, but concrete and checkable |
| **150 days / 5 months** of BA time to document a **300,000-LOC** system | 150 days ÷ 300K LOC | 2024 | **[W]** |
| Manual cost to document a **1,000,000-LOC** application | **~500 dev-days** | 2024 | **[W]** |
| Implied cost at UK mid-senior rates | **~£100K minimum**, realistically 2–3× for senior COBOL staff | 2024 | **[W]** |

https://www.version1.com/en-us/killing-cobol-in-core-banking-systems/

**Derived ratio worth using** [DERIVED from **[W]** inputs]: 150 days per 300K LOC extrapolates to **500 days per 1M LOC**, matching Version 1's own figure. For a bank with **20M LOC** in scope, full manual documentation is **~10,000 dev-days ≈ 40 dev-years ≈ $6–8M in loaded senior COBOL labour alone.** The economics of automated attestation are built on this number — and note that this is *documentation* cost, which is a lower bound on *attestation* cost, because attestation additionally requires re-running it per release.

**Supporting scale datapoint:** average mainframe application = **8.86M LOC**; 64% of orgs have mainframe apps 10–20 years old, 28% have apps 20–30 years old (Advanced Systems Mainframe Report, 2021, **[W]**, n not disclosed). IBM claims **60–80% of development budgets go to modernisation** rather than net-new (newsroom, 9 Jun 2026, **[F]** as IBM claim).

https://modernsystems.oneadvanced.com/globalassets/modern-systems-assets/resources/reports/advanced_mainframe_report_2021.pdf · https://mea.newsroom.ibm.com/bluepearl-ibm-bob-pr

## A7. IBM Bob Premium Package for Z — pricing, customers, IBM's own claims

### Pricing — verified from IBM's own documentation

| Plan | Monthly Bobcoins | Notes |
|---|---|---|
| Free trial | 40 | |
| **Pro** | 40 | **$20/mo** (40 × $0.50, consistent) |
| **Pro+** | 160 | Price **not confirmed** — prior dossier recorded $60, inconsistent with 160 × $0.50 = $80 |
| **Ultra** | 500 | Price **not confirmed** — prior dossier recorded $200, inconsistent with 500 × $0.50 = $250 |
| **Enterprise** | **1,000-Bobcoin packs at $500/pack** | Sales-led |
| Enterprise overage | 1,000-Bobcoin packs at **$550/pack** (+10%) | |

**1 Bobcoin = $0.50 USD.** Overages auto-billed at $0.50/coin; Enterprise admins cap overage in pack increments. Primary sources **[F]**: https://bob.ibm.com/docs/ide/account/bobcoins · https://bob.ibm.com/pricing · https://bob.ibm.com/docs/ide/enterprise/enterprise-index

**IBM Bob Premium Package for Z pricing: NOT PUBLISHED.** IBM's own page says only: *"Prices are indicative, vary by [region], exclude taxes and duties… **Subscription is required to trial a premium package.**"* Entitlement is sales-led via IBM Sales. No price, no list, no published ACV. **[F — the absence of a price is itself the finding.]** https://bob.ibm.com/pricing

### Capabilities and IBM's own claims

| Claim | Value | Date | Confidence |
|---|---|---|---|
| Bob core **GA** | 28 Apr 2026 | 28 Apr 2026 | **[F]** |
| Bob PP for Z **GA**, supersedes watsonx Code Assistant for Z | 9 Jul 2026 | 9 Jul 2026 | **[F]** |
| Internal IBM deployment | **>80,000 IBM employees** | 28 Apr 2026 | **[F]** |
| Self-reported productivity gain, internal survey | **45% average** | 28 Apr 2026 | **[F]** self-report |
| Instana team, selected tasks | **70% reduction**, ~10 hrs/week saved | 28 Apr 2026 | **[F]** self-report |
| Maximo team | **~69% time savings** | 28 Apr 2026 | **[F]** self-report |
| **Bob PP for Z delivery speed** | **20–40% faster** | 9 Jul 2026 | **[F]** IBM claim |
| **Bob PP for Z effort reduction** | **50–80%** for structured workflows | 9 Jul 2026 | **[F]** IBM claim |
| Z Code Mode | "generate, refactor, transform **standards-aligned** code" | 2026 | **[F]** |
| Data dictionaries / documentation | "Generate local and enterprise data dictionaries to handle cryptic variables"; "Generate application documentation" | 2026 | **[F]** |
| Equivalence testing | test cases generated from source behaviour **"to prove equivalence"** | 2026 | **[F]** |

https://www.ibm.com/new/announcements/announcing-the-ibm-bob-premium-package-for-z · https://www.prnewswire.com/news-releases/introducing-ibm-bob-ai-development-partner-that-takes-enterprises-from-ai-assisted-coding-to-production-ready-software-302755018.html

**Critical competitive note:** IBM has already shipped *repository-level `agents.md` enforcement of coding standards*, deterministic COBOL→Java, business-rule extraction from metadata, and equivalence test generation. **IBM is building the intent-to-code alignment layer you are proposing to sell.** See `ai-code-review-landscape-2026-09.md` §2.2 and §4.4 for the full read; the strategic opening is that IBM cannot credibly grade code produced by Bob.

### Customer counts

**IBM has published no customer count for Bob or Bob PP for Z.** The only named external case study is Blue Pearl. Everything else is internal IBM teams. **[GAP]**

---

# B. The broader software-verification / governance market

## B8. Application security / SAST / SCA / DAST

**Critical definitional warning.** "Application security" and "application security testing" differ by roughly **4×** in published numbers. Gartner's $3.4B is *AST tools only*. The $11–14B figures are *application security* broadly (API security, WAF, ASPM, cloud-native). Citing them interchangeably is the most common error in this category.

### AST (tools) — the narrow, Gartner-anchored number

| Figure | Value | Source | Date | Confidence |
|---|---|---|---|---|
| **Worldwide end-user spending on application security *tools*** | **~$3.4B (2022)**, +27% from $2.6B (2021) | Gartner *Magic Quadrant for Application Security Testing* | **17 May 2023** | **[F]** — Gartner's own document, but 2022 data |
| North America share | **~68%** | Gartner, same | 17 May 2023 | **[F]** |
| EU + UK | **17%** | Gartner, same | 17 May 2023 | **[F]** |
| Asia-Pacific | **12%** | Gartner, same | 17 May 2023 | **[F]** |
| Middle East & Africa / South America | **2% / 1%** | Gartner, same | 17 May 2023 | **[F]** |

https://research.oz.spotlightar.com/reports/magic-quadrant-application-security-testing-2023/market-definition

**The 68% North America concentration is the only Gartner-published geographic split I found for any adjacent market.** Useful for geographic scoping.

### AST/AppSec — the 2026 estimates, which disagree by 7×

| Analyst | 2024 | 2025 | 2026 | Forecast | CAGR | Confidence |
|---|---|---|---|---|---|---|
| **MarketsandMarkets (AST)** | $1.44B | **$1.83B** | — | $7.60B (2031) | **26.7%** | **[S]** |
| **PWR/PMR (AST)** | $10.65B | **$12.62B** | $14.92B | $40.68B (2032) | 18.2% | **[S]** |
| **Juniper Research (AppSec)** | — | — | **$11B** | ~$13B (2031) | ~16% / 5yrs | **[S]** |
| **MarketsandMarkets (AppSec broad)** | — | $12.19B | **$13.63B** | $23.45B (2031) | 11.5% | **[S]** |
| **Grand View (AppSec)** | — | $10.65B | — | $42.09B (2033) | 18.8% | **[S]** |
| PWR regional split (2025) | NA $4.92B · Europe $3.28B · APAC $2.90B · LatAm $883.4M · MEA $631.0M | | | | | **[S]** |
| AppSec top-3 vendors | **Veracode, Checkmarx, Black Duck** | | | | | **[S]** |

URLs: https://www.marketsandmarkets.com/Market-Reports/application-security-testing-market-147329639.html · https://pmarketresearch.com/worldwide-application-security-testing-market-research/ · https://www.juniperresearch.com/press/appsec-enterprise-spend-to-approach-13bn-globally/ · https://www.marketsandmarkets.com/Market-Reports/application-security-market-110170194.html · https://www.giiresearch.com/report/grvi1942063-application-security-market-size-share-trends.html

**PWR's SAST/SCA/DAST sub-splits (2025)** — the only published line-item breakdown:

| Testing type | 2025 value | Share |
|---|---|---|
| **SAST** | $3,786.0M | 30.0% |
| **SCA** | $3,028.8M | 24.0% |
| **DAST** | $2,776.4M | 22.0% |
| IAST | $1,514.4M | 12.0% |
| MAST | $1,514.4M | 12.0% |

⚠️ **The source has arithmetic errors.** PWR's stated AST total is $12.62B but its type breakdown sums to $13.62B. Separately, MarketsandMarkets' AST report header says "CAGR 2.67%" while its body says 26.7%. **Use the segment shares, not the absolute totals.**

**Gartner MQ for Application Security Testing 2026 exists** (Veracode named a Leader for the 11th consecutive time, Oct 2025). The MQ is paywalled; **I could not verify the 2026 market size. [GAP]**

## B9. AI governance — a 9.3× spread that reveals the category doesn't exist yet

| Analyst | 2024 | 2025 | **2026** | Forecast | CAGR | Confidence |
|---|---|---|---|---|---|---|
| **Gartner** | — | — | **$492M** | >$1B by 2030 | — | **[F]** press release |
| Grand View | — | $308.3M | **$417.8M** | $3,590.2M (2033) | 36.0% | **[S]** |
| **Fortune Business Insights** | — | $248.99M | **$351.73M** | $2,140.82M (2034) | 25.30% | **[S]** |
| Persistence | — | — | **$429.8M** | $4,201.3M (2033) | 38.5% | **[S]** |
| Mordor — *AI Governance Platforms* | — | $0.62B | **$0.80B** | $2.38B (2031) | 24.21% | **[S]** |
| Mordor — *AI Governance* (narrower) | — | $0.34B | **$0.44B** | $1.51B (2031) | 28.15% | **[S]** |
| MarketsandMarkets | $0.89B | — | — | $5.78B (2029) | 45.3% | **[S]** |
| Market Research Future | — | $2.62B | **$3.27B** | $19.28B (2035) | 24.8% | **[W]** |
| GII — GenAI Governance Platforms | — | — | — | +$2,241.1M cumulative 2025–30 | 40.4% | **[S]** |

URLs: https://www.gartner.com/en/newsroom/press-releases/2026-02-17-gartner-global-ai-regulations-fuel-billion-dollar-market-for-ai-governance-platforms · https://www.grandviewresearch.com/industry-analysis/ai-governance-market-report · https://www.fortunebusinessinsights.com/ai-governance-market-105975 · https://www.mordorintelligence.com/industry-reports/ai-governance-platforms-market · https://www.globenewswire.com/news-release/2026/08/25/3350690/0/en/ai-governance-market-surges-to-5-78-billion-at-a-cagr-45-3-by-2029-report-by-marketsandmarkets.html

**The Gartner press release is the only [F] number here, and it is the smallest: $492M in 2026.** Two of its claims are load-bearing:

> *"By 2030, fragmented AI regulation will quadruple and extend to 75% of the world's economies, driving **$1 billion in total compliance spend**."*
> *"Gartner projects that effective governance technologies could **reduce regulatory expenses by 20%**."* **[F]**

**Read the 2026 spread honestly: $351.73M to $3.27B — 9.3× for the same year.** The dispersion is definitional, not analytical: some houses count only governance platforms, others fold in MLOps, LLMOps, AI observability and services. **The defensible statement is "high hundreds of millions today, growing 25–36% CAGR, and no two analysts agree on the definition."** Anyone quoting a single point estimate as *the* market size is overselling precision they don't have.

Adjacent: MLOps $3.4B (2026) → $25.93B (2034) at 28.90% CAGR (Fortune BI); LLMOps $7.14B (2026) → $15.59B (2030) at 21.3% (Research and Markets). Both **[W]** — sourced via a content aggregator, not verified against the primary houses.

**Gartner did publish the adjacent category properly:** *Enterprise AI Coding Agents* at **~$9.8B–$11.0B annualised as of April 2026** **[F]**, 20 May 2026. https://www.gartner.com/en/articles/enterprise-ai-coding-agent-market

## B10. "AI code governance" — yes, it is now a named category, with numbers

**This is the most important finding in Section B, and it appears on no Gartner/IDC list. Three separate houses have now invented the category independently.**

| Analyst | Category name | 2025 | 2026 | Forecast | CAGR | Confidence |
|---|---|---|---|---|---|---|
| **YH Research / MarketPublishers** | **"AI Code Review and SDLC Governance"** | **$955M** | — | **$2,465M (2032)** | **15.5%** (MarketPublishers says 16.1%) | **[S]** |
| **Fact.MR** | **"AI-Generated Code Assurance Services"** | $0.8B | **$1.1B** | $30.0B (2036) | **39.2%** | **[S]** — but *services*, not software |
| **Qodo** | **"AI Code Quality and Governance Platform"** | — | — | — | — | **[F]** as vendor self-definition |

https://www.yhresearch.com/reports/3119441/ai-code-review-and-sdlc-governance · https://pdf.marketpublishers.com/globalinfo/global-ai-code-review-n-sdlc-governance-supply-gir.pdf · https://www.factmr.com/report/ai-generated-code-assurance-services-market

**The YH Research category definition is the closest published description of what you are building:**

> *"AI Code Review and SDLC Governance platforms serve as software engineering governance frameworks embedded within Git, IDEs, CI/CD pipelines, and artifact repositories… perform comprehensive functions—including Pull Request (PR) reviews, security vulnerability prioritization, detection of secrets and dependency risks, test case generation, **release compliance gating**, and R&D efficiency analysis—for both AI-generated and human-written code."* **[S]**

Note two things: **"Release Compliance Gate" is an explicitly named functional category**, and the target verticals include **"financial IT sectors"** and **"government systems."** Stated industry gross margins: **60–85%**.

**Qodo's 2026 State of AI Code Quality Report** (Sept 2026) is the most decision-relevant dataset I found for this thesis — Censuswide, **500 US software developers + 300 US engineering leaders** at organisations where AI already does meaningful SDLC work:

| Finding | Value |
|---|---|
| Organisations that have experienced an **AI-related production incident** | **89%** |
| Engineering leaders who consider existing processes **sufficient** | **3.7%** |
| Engineering leaders who can report AI's impact to executives/the board | **90%** |
| …who have **traceability connecting AI activity to the code changes it produces** | **45%** |
| Developers working with a centralised context/rules system | 42.6% |
| …who say agents **always** follow organisational standards | **35%** |
| Engineering leaders naming insufficient agent context as a top quality/governance gap | **43%** |
| Primary delivery constraint named by *both* audiences | Reviewing and validating AI-generated code |

https://futurumgroup.com/insights/ai-code-generation-scaled-verification-didnt/
⚠️ **Conflict flag: Qodo sells an "AI Code Quality and Governance Platform." It commissioned a survey whose headline finding is that 89% of organisations have an AI incident and 3.7% of leaders think their processes suffice.** Directionally this aligns with independent peer-reviewed evidence in `evidence-dossier.md` §4.3 (human review of AI PRs is already mostly absent), so I do not think it is fabricated. But it is a vendor studying its own market and must be disclosed as such.

**The 90% / 45% gap is the number to put in a deck.** Leaders believe they can report on AI's impact; fewer than half can trace AI activity to specific code changes. That is the traceability deficit your product addresses, stated by people who admit they have the gap.

## B11. GRC / compliance software — 5× spread

| Analyst | Scope | 2025 | 2026 | Forecast | CAGR | Confidence |
|---|---|---|---|---|---|---|
| **Verdantix** | **GRC software vendor revenue only** | $4.98B (2023) | — | $9.08B (2029) | **11%** | **[S]** — most credible specialist; also the *smallest* number |
| **Mordor** | GRC software | $21.04B | **$23.32B** | $39.01B (2031) | 10.84% | **[S]** |
| The Business Research Company | **IT** GRC | $20.29B | **$22.66B** | $35.6B (2030) | 11.9% | **[S]** |
| QY Research | GRC software | $20,470M | $22,150M | $37,350M (2032) | 9.1% | **[S]** |
| Stratistics MRC | GRC (broad) | — | $22.5B | $61.8B (2034) | 13.5% | **[S]** |
| Technavio | GRC platforms | — | — | +$46.98B cumulative 2025–30 | 13.6% | **[S]** |
| **TBRC** | Governance/compliance/risk mgmt (**much broader**) | $50.72B | **$58.04B** | $98.67B (2030) | 14.4% | **[S]** |
| Grand View | Enterprise GRC (software + services) | $72.42B | $82.93B | $203.65B (2033) | 13.7% | **[S]**; software = 65.3% of revenue |
| TrendX Insights | GRC software | $4.52B | $4.90B | $14.25B (2034) | 13.6% | **[S]** |
| **IFAC** | *Global cost of fragmented financial regulation* | — | — | **$780B tax on the global economy** | — | **[S]** |

URLs: https://www.verdantix.com/venture/report/market-size-and-forecast-governance-risk-and-compliance-software-2023-2029-global · https://www.mordorintelligence.com/industry-reports/governance-risk-and-compliance-software-market · https://www.thebusinessresearchcompany.com/report/information-technology-it-governance-risk-and-compliance-grc-market-report · https://www.researchandmarkets.com/reports/5767326/governance-compliance-risk-management-software · https://www.qyresearch.com/reports/6018572/governance--risk-management-and-compliance--grc--software · https://www.grandviewresearch.com/industry-analysis/enterprise-governance-risk-compliance-egrc-market · https://www.ifac.org

**The spread is 5×: Verdantix $4.98B (2023) vs Mordor $21.04B (2025).** Verdantix counts GRC *software vendor revenue*; Mordor evidently includes services and adjacent categories. **For a software company selling into this market, Verdantix's ~$5–9B is the honest denominator and Mordor's $23B is the optimistic one.** Grand View's "software = 65.3% of revenue" is the cleanest available rule for converting a software+services market into a software market.

IFAC's $780B is a rhetorical ceiling for "what does fragmented regulation cost the economy," not a TAM.

## B12. Regulatory forcing functions — exact dates

### EU AI Act — Regulation (EU) 2024/1689

**Primary source: European Commission [F]** — https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai

| Date | Event | Status |
|---|---|---|
| **1 Aug 2024** | Entered into force | **[F]** |
| **2 Feb 2025** | Prohibited practices (Art. 5) + AI literacy (Art. 4) applicable | **[F]** |
| **2 Aug 2025** | GPAI model obligations + governance rules applicable | **[F]** |
| **2 Aug 2026** | Generally applicable. AI Office and Member State authorities become responsible for implementation, supervision, enforcement | **[F]** |
| **August 2026** | **Art. 50 transparency obligations take effect** | **[F]** — EC states "August 2026" without a day. A secondary source says 2 Dec 2026 — **[X] unresolved** |
| **2 Dec 2027** | **High-risk AI under Annex III** (biometrics, critical infrastructure, education, employment, migration, credit scoring, insurance risk assessment, law enforcement) | **[F]** — moved from 2 Aug 2026 |
| **2 Aug 2028** | **High-risk AI embedded in regulated products (Annex I)** — medical devices, machinery, vehicles | **[F]** — moved from 2 Aug 2027 |

**The AI Omnibus — how the high-risk dates moved:**

| Step | Date |
|---|---|
| Digital Package on Simplification / "AI Omnibus" proposed | **19 Nov 2025** |
| Political agreement reached | **7 May 2026** |
| Adopted by European Parliament | 16 Jun 2026 |
| Adopted by Council | 29 Jun 2026 |
| **Entered into force** | **27 Jul 2026** |

**[F]** for all. https://agledger.ai/compliance/eu-ai-act/article-12/ for the adoption detail.

**This is the strongest forcing function, and note the direction.** The Annex III deadline moved *later* (Dec 2027), which means 15 more months of build time — **but it is now fixed in law rather than provisional.** Both prior dossiers' framing of "postponed by the May 2026 Omnibus political agreement" is out of date; the postponement is enacted.

### The specific articles — and the critical limitation

**Read this before building a compliance-driven pitch. Article 12 is materially narrower than the sales narrative assumes.**

| Article | Requirement | Text |
|---|---|---|
| **Art. 12(1)** | Automatic logging over system lifetime | *"High-risk AI systems shall technically allow for the automatic recording of events (logs) over the lifetime of the system."* |
| **Art. 12(2)** | Logging must enable three things | (a) identifying situations that may result in the system presenting a risk within Art. 79(1) **or in a substantial modification**; (b) facilitating post-market monitoring under Art. 72; (c) monitoring operation under Art. 26(5) |
| **Art. 12(3)** | Minimum log content | **ONLY for remote biometric identification systems** (Annex III point 1(a)): period of each use; reference database; input data matching; identification of persons verifying results per Art. 14(5) |
| **Art. 19(1)** | Provider retention | *"…for a period appropriate to the intended purpose of the high-risk AI system, **of at least six months**…"* |
| **Art. 26(6)** | Deployer retention | Same six-month floor |
| **Art. 21(2)** | Access on request | Providers must give competent authorities access to Art. 12(1) logs on reasoned request |
| **Art. 11(1) + Annex IV** | Technical documentation | Must contain the Annex IV elements |
| **Annex IV ¶1(a)** | Version identity | Intended purpose, provider name, *"the version of the system reflecting its relation to previous versions"* |
| **Annex IV ¶2(g)** | Validation evidence | *"the validation and testing procedures used… and **test logs and all test reports dated and signed by the responsible persons**"* |
| **Annex IV ¶6** | Lifecycle change description | *"A description of relevant changes made by the provider to the system through its lifecycle"* |
| **Annex IV ¶9** | Post-market monitoring plan | Per Art. 72(3) |
| **Recital 71** | Purpose of traceability | *"Having comprehensible information on how high-risk AI systems have been developed and how they perform throughout their lifetime is essential to enable traceability of those systems, verify compliance with the requirements under this Regulation, as well as monitoring of their operations and post market monitoring."* |

**The limitation, stated precisely [F]** — from the most rigorous practitioner reading I found (Lucairn, 15 Aug 2026):

> *"Article 12 applies to **high-risk AI systems**. It is **not a general rule that every LLM integration must keep the same records**."*
> *"Article 12(3) sets a specific minimum list… **but only for the remote biometric identification systems in Annex III point 1(a)**. Other high-risk systems remain under Article 12(1) and (2)."*
> *"The Regulation uses the word [traceability] in a narrower second sense elsewhere: Annex V point 1 and Annex VIII ask for the AI system name plus 'any additional unambiguous reference allowing the identification and traceability of the AI system'. **That is product identification, not decision reconstruction.** When a supplier's datasheet promises traceability, check which sense it means."*

https://lucairn.eu/en/blog/eu-ai-act-traceability · statute: https://artificialintelligenceact.eu/article/12/ · https://ai-act-service-desk.ec.europa.eu/en/ai-act/annex-4

**Commercially:** Art. 12 creates real, dated, mandatory demand for **lifetime event logging and dated/signed test evidence on high-risk AI systems** — Annex III categories 2 (critical infrastructure), 4 (employment) and **5 (credit scoring and insurance risk assessment)** are the ones touching banking and insurance. But it does **not** make AI-code traceability mandatory for ordinary enterprise software. **Any pitch saying "the EU AI Act requires you to trace AI-generated code" is wrong and will be caught by a competent customer.**

**Penalties:** prohibited practices (Art. 5) — **€35M or 7%** of worldwide turnover; high-risk obligations (Arts. 6–49) — **€15M or 3%**; whichever is higher (Art. 99). **[F]**

**Harmonised standards are not ready.** CEN/CENELEC standards will not finalise until **Q4 2026 at earliest** — after the Aug 2026 applicability date. Companies must interpret the regulation text directly, supplemented by AI Office guidance and ISO/IEC 42001. **[W]** — Consilium Law, Apr 2026: https://consilium.law/sparkpoint/eu-ai-act-high-risk-deadline/

### DORA — Regulation (EU) 2022/2554

| Item | Value | Confidence |
|---|---|---|
| Adopted | **14 Dec 2022** | **[F]** |
| Entered into force | **16 Jan 2023** | **[F]** |
| **Directly applicable from** | **17 Jan 2025** (Art. 64) — no national transposition | **[F]** |
| Scope | Financial entities per Art. 2(1) | **[F]** |
| Relationship to NIS2 | DORA Art. 1(2) — sector-specific act prevails for financial entities also in NIS2 scope | **[F]** |
| **ICT third-party risk** | **Arts. 28–30** | **[F]** |
| Incident reporting | **Art. 19**; RTS **Delegated Regulation 2025/301**, ITS **Implementing Regulation 2025/302** | **[F]** |
| Supervision | DORA Chapter VII (Arts. 46–56); competent authority = prudential/conduct supervisor under Art. 46 | **[F]** |

https://docs.modulos.ai/frameworks/comparison/nis2-vs-dora · https://www.telefonica.com/en/communication-room/blog/dora-nis2-cra-decoding-europes-cybersecurity-regulatory-landscape/

**DORA is the better forcing function than the EU AI Act for a bank buyer.** Already in force, directly applicable, named articles on ICT third-party risk, and its incident-reporting RTS/ITS are published. For a bank, DORA is a live supervisory relationship, not a future compliance project.

### NIS2 — Directive (EU) 2022/2555

| Item | Value | Confidence |
|---|---|---|
| Adopted / in force | 14 Dec 2022 / **16 Jan 2023** | **[F]** |
| **Transposition deadline** | **17 Oct 2024** | **[F]** |
| **Applies from** | **18 Oct 2024** | **[F]** |
| Countries transposed by ~Aug 2024 | **4** — Belgium, Hungary, Lithuania, Croatia | **[F]** (DIGITALEUROPE) |
| Fragmentation | Material. Germany, Sweden, Finland, Netherlands, Poland, Slovakia, Ireland all applied later than 18 Oct 2024; Greece and several others had not published drafts | **[F]** |
| Scope | 18 sectors, medium/large enterprises; financial sector excluded (DORA is *lex specialis*) | **[F]** |

https://cdn.digitaleurope.org/uploads/2024/09/27082024-Overview-of-national-transposition-NIS2-Directive.pdf

**NIS2's problem for a forecast: it is two years past transposition and still fragmenting. Do not build a revenue model on NIS2 enforcement dates.**

### Cyber Resilience Act — Regulation (EU) 2024/2847

| Item | Value | Confidence |
|---|---|---|
| In force | **10 Dec 2024** | **[F]** |
| **Main obligations apply** | **11 Dec 2027** | **[F]** |

Covers products with digital elements; introduces CE marking, conformity assessment, vulnerability handling and mandatory security updates. **[F]**

**CRA is the sleeper.** The only EU regulation making **software vulnerability handling and update obligations mandatory on a manufacturer basis**, with a 2027 date. But IBM's Bob PP for Z and Sonar Enterprise already ship CRA compliance — the incumbent tooling is positioned for it.

### US federal — FedRAMP and OMB

**You asked about "OMB M-24-10 or successor." The successor is M-24-15, and it rescinded FedRAMP entirely.**

| Item | Value | Date | Confidence |
|---|---|---|---|
| **OMB M-24-15** published | **25 Jul 2024** — *"formally rescinded and replaced FedRAMP in its entirety, effectively creating a new program with the same name but an entirely different set of authority and responsibilities"* | 25 Jul 2024 | **[F]** |
| Legal basis | FedRAMP Authorization Act, 44 U.S.C. §3609 | | **[F]** |
| FedRAMP 20x announced | **Mar 2025** | Mar 2025 | **[F]** |
| 20x Phase 1 (Low pilot) | Apr–Sep 2025 | | **[F]** |
| **20x Phase 3 (wide-scale adoption) — ACTIVE** | **FY26 Q3–Q4** | | **[F]** |
| Consolidated Rules for 2026 (CR26) | by end of **FY26 Q3 (Jun 2026)** | | **[F]** |
| 20x submission pipeline opens | **FY26 Q4 (Jul–Sep 2026)** | | **[F]** |
| 20x certification classes | **Class A (Pilot), Class B (≈old Low), Class C (≈old Moderate)** initially | | **[F]** |
| 20x Phase 4 (Class D / High pilot) | **estimated** FY27 Q1–Q2 | | **[F]** — explicitly "estimates, not firm commitments" |
| **20x Phase 5 — Rev5 sunset for new authorizations** | **FY27 Q3–Q4** | | **[F]** |
| **OSCAL machine-readability mandate** | M-24-15 §IX: within **24 months** (i.e. by **July 2026**), *"agencies shall ensure that agency **GRC and system-inventory tools** can ingest and produce machine-readable authorization and continuous monitoring artifacts using **OSCAL**"* | | **[F]** |
| Other M-24-15 deadlines | 21 Jan 2025 agency policy; 21 Jan 2025 GSA ConMon update; Mar 2025 & Mar 2026 annual plans; Jul 2025 GSA transition plan; **Jan 2026** GSA means to receive artifacts machine-readably | | **[F]** |
| **SBOM requirement** | FedRAMP 20x **Key Security Indicators** draft requires CSPs to *"obtain a Software Bill of Materials (SBOM) for third-party commercial software components"*; also requires a **Secure Software Development Attestation on file with CISA** | 2025–26 | **[W]** — draft, in pilot, not finalised |
| **RFC-0024** | allegedly issued 13 Jan 2026, mandating machine-readable OSCAL packages for **all** FedRAMP providers by **Sept 2026** | 13 Jan 2026 | **[X] UNVERIFIED — could not retrieve from fedramp.gov** |

Primary sources **[F]**: https://www.whitehouse.gov/wp-content/uploads/2024/07/M-24-15-Modernizing-the-Federal-Risk-and-Authorization-Management-Program.pdf · https://fedramp.gov/2026/authority/m-24-15/ · https://www.fedramp.gov/20x/ · https://fedramp.gov/2026/providers/updating/ · deadline summary: https://coalfire.com/the-coalfire-blog/highlights-from-omb-m-24-15-modernizing-the-fedramp-program · SBOM/KSI **[W]**: https://fossa.com/blog/guide-sbom-fedramp-compliance/ · RFC-0024 **[X]**: https://quzara.com/fedramp/20x-roadmap

**The commercially important M-24-15 clause is the OSCAL mandate — and note who it binds: "agency GRC and system-inventory tools."** That is a direct, dated, US-federal requirement that GRC and inventory systems ingest and produce machine-readable authorisation artifacts. It is the strongest US forcing function for an evidence-grade product, and its deadline was **July 2026 — already past.**

## B13. Global developer population

| Figure | Value | Source | Date | Confidence |
|---|---|---|---|---|
| **Global developer population** | **48.4 million** | SlashData Developer Nation | **Q3 2025** | **[S]** — best methodologied |
| Prior readings | 47.2M (Q1 2025); 31M (Q1 2022) | SlashData | | **[S]** |
| Growth | +15% (2022→23), +21% (2023→24), **+10%** (latest 12 months) | SlashData | | **[S]** |
| **Enterprise split** | **Large enterprises: 7.5M developers.** Medium (51–1,000 employees): **14.5M**. Together >60% of all professional developers | SlashData | Q1 2025 | **[S]** |
| Regional | W. Europe ~9.5M; N. America ~9.5M; South Asia ~7.5M; Greater China ~5.8M; South America ~3.4M | SlashData | early 2025 | **[S]** |
| Cloud-native developers | 15.6M (Q3 2025) → **19.9M (Q1 2026)**, ~39% of total | SlashData / CNCF, 31st survey, n=12,500+ | Mar 2026 | **[S]** |
| Using AI-assisted tools | **75%** of professional developers | SlashData | | **[S]** |
| **GitHub accounts** | **180M+ developers on GitHub**; +36M in past year | GitHub Octoverse 2025 | Oct 2025 | **[F]** as GitHub's figure — **but it counts accounts, not people** |
| **GitHub's professional-developer estimate** | **~13.4M (2023 methodology); ~19.6M (2024 revised)** | GitHub | 2024 | **[F]** as GitHub's own |
| Statista | 28.7M (2024 projected) | Statista | 2024 | **[W]** — unrefreshed, off a 2020 baseline |

URLs: https://www.slashdata.co/research/developer-population · https://www.slashdata.co/post/global-developer-population-trends-2025-how-many-developers-are-there · https://www.slashdata.co/post/there-are-19-9m-cloud-native-developers-in-q1-2026 · https://cote.io/2025/10/31/what-do-we-think-of.html

**SlashData methodology [S]** — quote this when challenged: 29 waves of Developer Nation surveys, 10,000+ respondents each, triangulated against GitHub accounts, Stack Overflow accounts, and US/EU employment statistics.

**Honest picture: the credible range for global professional developers is 19.6M to 48.4M — 2.5× between GitHub's own estimate and SlashData's.** GitHub's 180M+ is a different quantity entirely (all accounts ever created, including students, hobbyists and inactive accounts) and should never be cited as a developer population.

**For your model, the number that matters is 7.5M developers at large enterprises** — with the implication that almost none of them work on IBM Z. **Developer-population-based TAMs will badly overstate a mainframe-attested-release product. Account-based TAM is the right frame.**

---

# C. Pricing and revenue benchmarks

## C14. Enterprise developer tooling ACV

**The $35K figure you cited does exist, and it is weak.** Full context:

| Vertical | Mid-market median ACV | Enterprise ACV | Pricing model |
|---|---|---|---|
| Cybersecurity | $85K | $280K | Per-seat + per-endpoint |
| Fintech | $65K | $220K | Transaction volume + base |
| Healthcare | $58K | $185K | Per-seat + module |
| **DevTools / API-first** | **$35K (lowest of all verticals)** | **$95K (still lowest)** | Usage + per-seat |

**Source: GrowthSpree ACV benchmarks 2026 [W]** — an agency publishing its own benchmark. Treat directionally. The benchmark's own explanation is the one that matters: *"DevTools runs lower because buyers (engineers) are price-sensitive and self-serve options exist."*

**Independent cross-check [W]:** SaaStr puts enterprise ~$220K / mid-market ~$40K / SMB ~$4,800, median private-SaaS ACV **$26,265**.

**The spread, honestly: $26K (median private SaaS) → $35K (DevTools mid-market) → $40K (SaaStr mid-market) → $95K (DevTools enterprise) → $220K (SaaStr enterprise / fintech). A 7× range.** The sources disagree because "enterprise" means different things and the benchmark houses have commercial incentives.

**The structural point, and the most important thing in Section C: if the $35K/$95K pair is roughly right, you cannot build a $500K ACV business selling horizontal developer tooling to engineers. You have to change the buyer.** That is why the compliance comparables below matter more than the DevTools ones.

**Pricing model is the largest ACV lever:** 2–4× difference between usage-based and flat-seat for the same category **[W]**. 87% of enterprise customers choose annual billing; median enterprise discount 16.7%; 74.5% of contracts run 13–24 months.

## C15. Compliance/audit tooling ACVs and ARR

### Company level — the observed ceiling of this category

| Company | ARR | Date | Customers | Implied ARR/customer | Valuation | Confidence |
|---|---|---|---|---|---|---|
| **Vanta** | **$300M ARR** (+69% y/y) | ~29 Apr 2026 | **16,000** (7,000 FY24 → 12,000+ Jul 2025 → 14,000+ YE2025 → 16,000 Apr 2026) | **~$19K** | $4.15B (Jul 2025 Series D, $150M led by Wellington) | **[F]** company-confirmed + Fortune exclusive |
| Drata | $98M ARR (from $95M 2024, $59M 2023) | Jan 2025 | ~7,000 (2024) | **~$13.5K ACV** | $2B (Dec 2022) | **[W]** Sacra estimate, not company-confirmed |
| Secureframe | Not disclosed | — | — | — | — | **GAP** |

https://www.vanta.com/resources/vanta-crosses-300m-in-arr-as-growth-accelerates · https://fortune.com/2026/04/29/exclusive-vanta-arr-300-million-sequoia-shadow-ai-claude-cursor/ · https://sacra.com/c/vanta/ · https://sacra.com/c/drata/ · https://sacra.com/research/vanta-at-220m-year/

**Vanta detail [F]:** NRR >100% and rising for 8 straight quarters; customer growth ~60% y/y; ~1,000 employees; >$500M raised; ~25% of revenue from outside the US. Milestone history: 2 years $10M→$100M, 15 months to $200M, 9 months to $300M.

**Vanta ARPC trajectory [W/Sacra]:** $5K (2021) → $17K (Jul 2025) → $18K (YE2025) → $18.3K (2025) → **~$19K (Apr 2026)**.

**Secureframe ARR is a real gap.** Third player in a category whose two competitors have both disclosed ARR, and it has not. No credible figure found.

### Contract level — procurement data

| Vendor | Entry tier | Mid | Enterprise | Median (Vendr) | Range (Vendr) | Onboarding |
|---|---|---|---|---|---|---|
| **Vanta** | $7.5K–$14K (Core) | $15K–$30K (Growth) | $40K–$90K | — | — | — |
| **Drata** | $10K–$15K (Startup) | $25K–$50K (Growth) | $60K–$150K | **$25K–$34K** | ~$10,250–$42,750 | $10K–$25K |
| **Secureframe** | $8K–$15K (Fundamentals) | $20K–$40K (Complete) | $50K–$120K | **~$20K** | ~$7,733–$32,575 | — |
| Hyperproof | rarely <100 employees | — | $75K–$100K+ | — | — | — |
| **OneTrust** | $25K floor (single module) | — | **$100K–$150K+** (multi-module) | — | — | — |

https://cipherssecurity.com/drata-vs-secureframe-2026-pricing-features/ · https://www.stackfyi.com/guides/vanta-vs-drata-vs-secureframe-2026 · https://aipromptshub.co/legal/ai-compliance-monitoring-cost · https://www.thesectorpost.com/compliance/soc2/vanta-vs-drata-vs-secureframe-pricing

⚠️ **All contract-level figures are [W].** Vanta and Drata are both quote-only with no published price list. The Vendr-sourced ranges come from procurement aggregators, and the aggregator explicitly warns to *"treat them as ranges, not guarantees."* The PEPM figures circulating for these vendors are derived, not published.

**Discounting [W]:** Drata/Vanta/Secureframe 15–25% multi-year prepay; Hyperproof/OneTrust 20–30% for 3-year. Expect 10–12% annual escalators by 2027 absent a price-protection clause.

### ⚠️ The Delve problem — material risk to this entire category

**This belongs in your risk section, not in a footnote.**

| Event | Detail | Confidence |
|---|---|---|
| **March 2026** | An anonymous group of former customers of compliance startup **Delve** alleged it generated **fabricated evidence and pre-written auditor conclusions**, then routed clients to audit firms that signed whatever arrived. Their analysis of leaked files found **493 of 494 SOC 2 reports shared near-identical text, down to the same grammatical error.** | **[W]** — reported by Axipro, a vendor with an interest in the story |
| Delve's response | Denied the claims; states independent auditors issue all final opinions | **[W]** |
| Precedent | **2024: the SEC shut down audit firm BF Borgers** for fabricating audit documentation behind **1,500+ filings**, described by its enforcement director as a *"sham audit mill"* | **[W]** — widely reported; I did not retrieve the SEC order directly |
| Structural cause | The AICPA's SOC 2 guidance treats auditor independence as the entire point of the attestation. When platform, readiness partner and auditor collapse into one, the attestation's value goes to zero. | reasoning |

https://axipro.co/iso-27001-certification-cost/

**Why this matters to you specifically:** you are proposing to sell *attestation*. The Delve allegation is the exact failure mode of attestation-as-a-product — **manufacturing** the evidence rather than **verifying** it. Two implications: (1) your differentiator must be **independence and verifiability**, not throughput; (2) an auditor or regulator burned by Delve will ask hard questions about how your evidence is produced. Have the answer before you're asked.

## C16. What organisations already pay for assurance

| Framework | Small (<50) | Mid (50–250) | Large (250–1,000) | Enterprise (1,000+) |
|---|---|---|---|---|
| **SOC 2 Type I** | $30K–$75K | $60K–$150K | $100K–$250K | $200K+ |
| **SOC 2 Type II** | $50K–$125K | $100K–$300K | $200K–$600K | $500K+ |
| **ISO 27001** | $60K–$150K | $125K–$350K | $250K–$700K | $600K+ |
| **PCI DSS (ROC)** | $75K–$200K | $150K–$500K | $300K–$1M+ | $1M+ |
| **CMMC Level 2** | $100K–$300K | $200K–$700K | $500K–$1.5M | $1M+ |
| **HIPAA readiness** | $25K–$75K | $50K–$200K | $150K–$500K | $500K+ |

Episki compliance cost benchmark, Feb 2026 **[W]** — https://episki.com/blog/compliance-cost-benchmark-2026

**More granular, from more varied sources:**

| Item | Value | Source | Confidence |
|---|---|---|---|
| SOC 2 audit fee (report only) | **$10K–$50K**; large enterprise w/ Big Four: low six figures and up | Vanta | **[W]** |
| SOC 2 all-in first year | **$10K–$80K+** | Vanta | **[W]** |
| SOC 2 Type 1 audit | $7.5K–$15K (small/mid) to $60K (large) | Drata | **[W]** |
| SOC 2 Type 2 audit | $12K–$100K+ by length, scope, complexity | Drata | **[W]** |
| SOC 2 total first year | **$25K (small startup) to $200K+ (large enterprise)**; enterprise 500+ ≈ $180K+ | Drata | **[W]** |
| SOC 2 annual maintenance | $15K–$40K | Drata | **[W]** |
| ISO 27001 yr 1 (small/mid) | $10K–$50K total; certification-body fees alone $12K–$22K for a 50-person co. | Axipro | **[W]** |
| ISO 27001 yr 1 (enterprise) | **>$100K**; audit fee alone can pass $50K | Axipro | **[W]** |
| ISO 27001 annual | $5K–$25K | Axipro | **[W]** |
| **ISO 27001 audit day rate** | **$1,500–$2,200/day US (ANAB-accredited); £1,000–£1,500/day UK** | Axipro | **[W]** — most concrete, most citable unit price in the section |
| **FedRAMP Rev5 Low** | **$250K–$500K** initial + $80K–$200K/yr | Paramify, Boundera, Secureframe | **[W]** — three sources agree |
| **FedRAMP Rev5 Moderate** | **$500K–$1.5M** initial + $200K–$500K/yr | same three | **[W]** — three sources agree |
| **FedRAMP Rev5 High** | **$2M–$3M+** initial + $500K–$1M/yr | Paramify, Boundera | **[W]** |
| 3PAO assessment alone | **$50K–$400K+** (Moderate complex $200K–$650K) | Boundera, Secureframe | **[W]** |
| Readiness Assessment Report | $30K–$80K | Boundera | **[W]** |
| **FedRAMP 20x Low** (early estimates) | **$100K–$300K** initial | Boundera | **[W]** — pilot stage |
| **FedRAMP 20x Moderate** | "materially below legacy Moderate's $2M–$5M lifecycle range" | Boundera | **[W]** — no firm number exists |
| FedRAMP control counts | **~156/323/410** (Low/Mod/High) per Boundera vs **125/325/421** per Paramify | — | **[W]** — sources conflict |

https://www.vanta.com/collection/soc-2/soc-2-audit-cost · https://drata.com/learn/soc-2/cost · https://axipro.co/iso-27001-certification-cost/ · https://www.paramify.com/blog/fedramp-cost · https://boundera.io/blog/20x/fedramp-cost-2026 · https://secureframe.com/hub/fedramp/costs

**The most honest fact in this section, from Boundera [W]:**

> *"**FedRAMP has no official price.** Costs come from 3PAOs, consultants, tooling, and your own engineering time — not from FedRAMP itself. **GAO has flagged the lack of standardized cost reporting as a known program gap.**"*
> A 2024 GAO review found CSP and agency cost estimates ranging *"from tens of thousands to millions of dollars."*

**Control overlap — the arbitrage map for a bundled attestation product [W]:**

| Framework pair | Approximate control overlap |
|---|---|
| SOC 2 + ISO 27001 | 40–60% |
| SOC 2 + HIPAA | 40–55% |
| SOC 2 + PCI DSS | 25–40% |
| ISO 27001 + HIPAA | 35–50% |
| **NIST 800-171 + CMMC Level 2** | **95%+** (CMMC L2 is built on 800-171) |
| NIST CSF 2.0 + any major framework | 50–70% |
| **SOC 2 + FedRAMP Moderate** | **40–55%** |

Typical cost split: audit/assessment fees 25–35%, GRC platform 10–20%, security tooling 10–25%, internal labour 25–40%, remediation reserve 10–20%, training 1–3%, contingency 10%. **Annual maintenance for an attested framework typically runs 40–70% of first-year cost.**

## C17. IBM Bob / watsonx Orchestrate published pricing

**IBM Bob — fully verified from bob.ibm.com [F]:**

| Item | Value | URL |
|---|---|---|
| 1 Bobcoin | **$0.50 USD** | https://bob.ibm.com/docs/ide/account/bobcoins |
| Pro | 40 Bobcoins/mo = **$20/mo** | https://bob.ibm.com/pricing |
| Pro+ | 160 Bobcoins/mo — **price unconfirmed** | same |
| Ultra | 500 Bobcoins/mo — **price unconfirmed** | same |
| Free trial | 40 Bobcoins | https://bob.ibm.com/docs/ide/account/bobcoins |
| **Enterprise** | 1,000-Bobcoin packs at **$500/pack** | same |
| Enterprise overage | 1,000-Bobcoin packs at **$550/pack** (+10%) | same |
| **Bob Premium Package for Z** | **NOT PUBLISHED.** *"Prices are indicative… Subscription is required to trial a premium package."* Sales-led. | https://bob.ibm.com/pricing |

**Arithmetic flag on the prior dossier's numbers.** It recorded *"Pro+ $60/160 coins"* and *"Ultra $200/500 coins."* At the documented $0.50/coin, Pro+ should be **$80** and Ultra **$250**. The coin allocations (40/160/500) and the $0.50 rate are **[F]**; the $60 and $200 prices are **[X]**. **Do not publish those two prices.**

**IBM watsonx Orchestrate: no published pricing found.** Announced 5 May 2026; on IBM Cloud Jun 2026; expanded 2 Jul 2026. Runs on AWS and IBM Cloud, on-premises, and AWS GovCloud. Agent Connect supports MCP and A2A and already contains third-party partner agents. **GAP — pricing undisclosed, which means channel economics are unknown.**

**Near-market consumption comparables:**

| Product | Published unit price | Source | Confidence |
|---|---|---|---|
| **AWS Blu Age** | **$0.10 per line** after 120K free-tier lines | softwaremodernizationservices.com | **[W]** — the only published per-LOC modernisation price found |
| Qodo | $0.012/credit | prior dossier | **[W]** |
| Cursor Bugbot | $1.00–$1.50 per run | prior dossier | **[F]** vendor pricing page |
| Intercom Fin | $0.99 per confirmed resolution | prior dossier | **[F]** — outcome-pricing precedent |
| ISO 27001 audit day | $1,500–$2,200 US / £1,000–£1,500 UK | Axipro | **[W]** |

---

# D. Bottom-up SOM inputs

## D18. IBM Z enterprises in a serviceable geography

**No published figure exists.** This is the input I had to construct. Ingredients, each labelled:

| Ingredient | Value | Source | Label |
|---|---|---|---|
| Global IBM Z / z/OS organisations | **2,844 / 6,276 / 15,957** (three estimates) | Landbase / ELP Data / ReadyContacts | **[W]** — 5.6× spread |
| US + UK + Germany share of z/OS deployments | **44% + 11% + 9% = 64%** | ELP Data | **[W]** |
| Share of IBM Z customers with >1,000 employees | **93.75%** (47.92% at 10,000+; 45.83% at 1,001–10,000) | AppsRunTheWorld | **[W]** |
| **Share of mainframe orgs that are banks or insurers** | **NOT PUBLISHED** | — | **ASSUMPTION** — I use 25% / 30% / 35% |

**Top-down cross-check [DERIVED from [F] IBM claim]:** 71% of Fortune 500 = **355 US companies**. ELP's 6,276 global implies ~17.7× the US Fortune 500 mainframe count — plausible for a global base spanning government, EU and large mid-market. **The two methods agree in order of magnitude**, which is the most validation available given the data.

**The 30% vertical assumption is the weakest link in the entire model.** Its justification is directional: banks and insurers are heavily over-represented among mainframe organisations relative to their share of all enterprises (44 of top 50 banks; all top 10 insurers; >90% FS penetration per IDC), so 25–35% of mainframe organisations being FS is conservative-but-plausible. **Replace this with a real technographic count before the model is used for anything consequential.**

## D19. Cost of a single enterprise modernisation programme

**The Blue Pearl number is the most-requested figure in this section and the most corrupted. Three versions exist:**

| Version | Claim | Source | Date |
|---|---|---|---|
| **A — IBM's own case study (most defensible)** | Full **Java 11 → 25 (LTS)** uplift in **~3 days vs ~30 days** typical. **160+ engineering hours preserved.** Zero post-deployment defects. 127 deprecated API calls resolved. **92% test coverage from zero tests.** **100% functional equivalence validated against the legacy system.** ~15% faster response times. Deployed to **~30,000 users**; matches ~26,000 consultants. ~3 hours upfront prompt/context construction. | IBM case study | 2026 |
| **B — IBM Mediacenter video title** | *"A **nine month** plan executed in three days… with a **two-person team**"* | IBM Mediacenter | 2026 |
| **C — LinkedIn post** | *"A software project scoped for **9 months and 14 engineers** just shipped in 3 days"* | LinkedIn, ullissescaruso | 12 Jul 2026 |

**These are inconsistent by two orders of magnitude in effort** — 30 person-days vs 9 months/14 engineers ≈ 378 person-months. All three describe the same company and the same project.

**Use version A.** It is IBM's own case study, corroborated across four independent IBM properties, and it is the *least* flattering version. B and C are number inflation as the story travelled — **a LinkedIn post is not a source.** If you cite "9 months / 14 engineers → 3 days" and a customer has read the IBM case study, you have a credibility problem.

**Also note what version A actually is: a Java version uplift, not a COBOL→Java re-platform, and not a mainframe modernisation.** It is a Java 11→25 dependency/API upgrade on a distributed cloud platform. Using it as evidence for COBOL mainframe modernisation efficacy is a category error, and Blue Pearl is a regional consultancy, not a bank.

https://www.ibm.com/case-studies/blue-pearl-bob · https://www.ibm.com/new/product-blog/how-blue-pearl-modernized-an-outdated-codebase-and-a-resolved-a-risky-security-posture-with-ibm-bob · https://mea.newsroom.ibm.com/bluepearl-ibm-bob-pr

**The genuine cost anchors, by pattern (all [W] — practitioner estimates, no published methodology):**

| Pattern | Cost band (5–20M LOC portfolio) | Timeline | Pays down debt? |
|---|---|---|---|
| Re-host (lift-and-shift to emulator) | **$5M–$50M** | fastest, lowest risk | No |
| Re-platform (COBOL→Java/C#) | **$20M–$200M** | 3–6 years | Partly |
| Re-write (greenfield) | **$50M–$1B+** | 5–10 years | Yes |

https://technicaldebtcost.com/cobol-mainframe-debt-cost

**Per-LOC and per-function-point unit costs — all [W], all conflicting:**

| Basis | Range | Source |
|---|---|---|
| COBOL→Java/C# migration | **$1.50–$4.00 per line of code** | entrans.ai; softwaremodernizationservices.com |
| Data migration | $0.75–$1.50/LOC (rehost) to $2.00–$5.00+/LOC (refactor) | softwaremodernizationservices.com |
| Automated refactoring (tooling) | $0.10–$0.30/line | softwaremodernizationservices.com |
| Offshore contractors | $180–$250/hour | softwaremodernizationservices.com |
| Rehosting | $800–$1,500 per function point | Capers Jones Software Benchmarks 2022–23, via tech-stack |
| Replatforming | $1,000–$2,200 per function point | same |
| **Refactoring** | **$1,200–$3,500 per function point** | same |
| Median COBOL project delivery rate | **50.4 hours per function point** — >5× slower than modern languages | ISBSG, from its own D&E repository |
| UAT budget as % of project | industry standard 40%; most projects allocate 20% and run out of time | softwaremodernizationservices.com |
| Dead code in a typical estate | **30–45%** should be deleted, not migrated | same |
| Automated COBOL→Java automation rate | 70–85% in 2026 vs 40% in 2020 | same |

**The ISBSG 50.4 hours/function point figure is the most defensible unit cost in this table** — it comes from a benchmark repository of real, size-rated projects, filtered to COBOL-primary projects with A/B-rated function-point confidence. Note the caveat ISBSG itself gives: post-2015 the median rests on only **22 data points**. https://www.isbsg.org/wp-content/uploads/2022/12/Short-Paper-2022-12-Cobol-Projects-%E2%80%93-do-they-still-exist.pdf

**Named historical cost disasters (all [F] as factual events):**

| Event | Cost | Source |
|---|---|---|
| **Commonwealth Bank of Australia** core banking replacement, 2008–2013 | 5 years; **>AUD $1bn (~$749.9M USD)** | Reuters; tech-stack; IBM community blog |
| **TSB Bank** migration, 2018 | 1.9M customers locked out; **>£330M** losses; UK regulators fined **£48.65M**; CEO resigned | dfarber.com; tech-stack |
| **NatWest/RBS** CA-7 batch scheduler corruption, 2015 | Weeks of disruption; FCA fined **£42M** | dfarber.com |
| **Hershey** SAP/Manugistics/Siebel big-bang, 1999 | **>$150M** stranded orders; Q3 revenue fell 12.4% | dfarber.com; dfarber.com |
| **FAA** legacy system assessment (GAO-24-107001) | 51 of 138 ATC systems (37%) unsustainable, 54 (39%) potentially so; some 30–50 yrs old; modernisation of the most critical not complete for **10–13 years** | GAO **[F]** |

⚠️ **Do not use the CBA, TSB, RBS or Hershey figures as evidence that modernisation is *impossible*.** They are big-bang rewrite failures, and the entire counter-argument to big-bang is incremental, verifiable migration — which is the approach you would be selling evidence for. Citing them as "modernisation always fails" is as wrong as citing Blue Pearl as "modernisation always works."

**IBM's own cost-relevant claim:** clients depending on z16 can realise **2–4× total cost of ownership** advantages depending on size and complexity (Kavanaugh, IBM 2Q26 call, **[F]** as IBM claim). And a 5,000-MIPS workload is quoted at $7.88M/yr on z/OS vs $2.40M/yr on AWS — **[X]**, from a vendor content site, not IBM; do not cite.

## D20. Applications in scope per large-bank portfolio

**This is the ratio you asked for, and there are five real anchors — with a 4-order-of-magnitude spread between "applications" and "programs."**

| Organisation | Metric | Value | Source | Date | Confidence |
|---|---|---|---|---|---|
| **BNY Mellon** | COBOL **programs** | **112,500** | David Brown, MD IT Transformation, via widely-cited reference | 2012 | **[F]** as a named-executive statement; **14 years old** |
| **BNY Mellon** | COBOL **lines of code** | **343 million** | same | 2012 | **[F]** as above |
| **KBC Bank** (Belgium) | **Applications** migrated | **1,359** (from 1,411 program sources analysed) | PKS case study | 2021–22 | **[W]** vendor case study, but concrete and named |
| **KBC Bank** | Lines of code | **>5.725M LoC** → reduced to **5.4M** after structural re-engineering; 88,645 lines auto-outsourced to 108 COPY modules | same | 2021–22 | **[W]** |
| **KBC Bank** | Programme shape | 3-month PoC (spring 2022) → **<12 months** full migration; 4 runtime modules rewritten in Assembler | same | 2021–22 | **[W]** |
| **ING Bank** | Application size + validation | **~1.5M LOC** COBOL (CICS/DB2/JCL) → Java; **~2 billion production transactions** tested side-by-side; **18 months**; in production since Feb 2022; managed in-house; all source stayed in ING's infrastructure | SoftwareMining case study | Jan 2025 | **[W]** vendor, but checkable |
| **SNS Bank** (Netherlands) | Core banking replatform | **2.8M LOC**, Unisys→IBM AIX, **150 people** involved, 95% auto-converted | Bdaily/Micro Focus | 2014 | **[W]**, 12 years old |
| Academic case study, financial sector | Portfolio shape | **>18.2M physical LOC across 47 information systems** | IEEE ICSM literature | 2005-era | **[S]** peer-reviewed, but very old |
| Belgian bank, academic | Single application | **2.6M LOC in ~1,000 programs**; ~400,000 statements | IEEE literature | 2005-era | **[S]** |
| **Average mainframe application** | LOC | **8.86 million** | Advanced Systems Mainframe Report | 2021 | **[W]**, n undisclosed |

URLs: https://www.pks.de/PKS/Referenzen/PKS_Case_Study_KBC.pdf · https://softwaremining.com/news/ING-Bank-Mainframe-Modernization.jsp · https://www.bdaily.co.uk/articles/2014/10/22/sns-bank-future-proofs-global-banking-applications-with-micro-focus-visual-cobol · https://skeptics.stackexchange.com/questions/5114 (compiling the academic citations) · https://www.dfarber.com/computer-consulting-blog/why-mainframe-modernization-projects-fail/

**Critical methodological warning on this whole table.** "Application," "system," "program," "module" and "subsystem" are used inconsistently across every one of these sources. BNY Mellon's 112,500 "programs" and KBC's 1,359 "applications" are **not the same unit** — the ratio is roughly 83 programs per application at BNY Mellon vs ~1,041 at KBC, and both cannot be right as an underlying density.

**For modelling, use this instead** [DERIVED, transparent]:

- **Applications per large bank portfolio: 1,000–5,000.** Anchored below on KBC (1,359) as the lower bound, scaled up for BNY Mellon-scale estates.
- **Average mainframe application: 8.86M LOC** (Advanced Systems 2021) — but KBC's real portfolio averaged only **4,213 LOC per application** (5.725M ÷ 1,359), a **47× discrepancy**. The 8.86M figure is almost certainly a per-*estate* or per-large-application figure mis-described as per-application.
- **Therefore: do not use 8.86M LOC/application.** Use the observed range of **~4,000 LOC (KBC, dense generated code) to ~2.6M LOC (single large banking application, academic)**.

**The honest bottom line for D20:** the *number of applications* in a large bank portfolio is knowable only per-organisation, and the only two clean published data points are **1,359 (KBC)** and **1,200 across 47 systems (fictional Continental National Bank in a vendor's training material — [X], discard)**. BNY Mellon's 112,500 programs is the only large named-bank number and it is 14 years old. **The realistic planning assumption is 1,000–5,000 applications, and it should be validated in the first five design-partner conversations rather than taken from this document.**

---

# Derived sizing inputs

**Every number below is either [SOURCED] with a citation, or [ASSUMPTION] with a stated rationale. The arithmetic is shown in full so it can be attacked line by line.**

## Method note: why account-based, not developer-based

Developer-population TAMs were rejected. Reasoning: SlashData puts **7.5M developers at large enterprises [SOURCED]**, but essentially none work on IBM Z, and an attested-release product prices per *account* and per *portfolio*, not per developer. Applying a per-seat price to the enterprise developer population would overstate this market by at least an order of magnitude. **Account-based funnel is the correct frame.**

## Step 1 — Beachhead universe

| Input | Value | Label |
|---|---|---|
| Global IBM Z / z/OS enterprises — Low | 2,844 | **[SOURCED]** Landbase [W] |
| Global IBM Z / z/OS enterprises — Base | 6,276 | **[SOURCED]** ELP Data [W] |
| Global IBM Z / z/OS enterprises — High | 15,957 | **[SOURCED]** ReadyContacts [W] |

**Cross-check [DERIVED]:** 71% × Fortune 500 = **355 US companies** [SOURCED IBM claim]. Base case 6,276 ÷ 355 ≈ **17.7×** — plausible for a global base spanning government, EU and large mid-market. *The two independent methods agree in order of magnitude.*

## Step 2 — Geography: US + Europe

US 44% + UK 11% + Germany 9% = **64%** **[SOURCED]** ELP Data [W]
*(Deliberately excludes France, Nordics, Benelux, Italy, Spain, Ireland — all inside ELP's 21% "RoW" bucket. So 64% is a **floor**, not a central estimate.)*

| Case | Calculation | Result |
|---|---|---|
| Low | 2,844 × 0.64 | **1,820** |
| Base | 6,276 × 0.64 | **4,017** |
| High | 15,957 × 0.64 | **10,212** |

## Step 3 — Size filter: >1,000 employees

**93.75%** = 47.92% (10,000+) + 45.83% (1,001–10,000) **[SOURCED]** AppsRunTheWorld [W]

| Case | Calculation | Result |
|---|---|---|
| Low | 1,820 × 0.9375 | **1,706** |
| Base | 4,017 × 0.9375 | **3,766** |
| High | 10,212 × 0.9375 | **9,574** |

**This filter removes 6.25% of the market. It is not doing meaningful work — which is itself the finding: IBM Z is an inherently large-enterprise technology.**

## Step 4 — Vertical filter: banking + insurance

**No published figure exists.** **[ASSUMPTION] 25% / 30% / 35%.**

*Rationale:* banks and insurers are heavily over-represented among mainframe organisations relative to their share of all enterprises — 44 of top 50 banks, all top 10 insurers [SOURCED, IBM claims], >90% FS penetration [SOURCED, IDC]. For a product sold *only* to regulated financial institutions, 30% of mainframe orgs being FS is conservative-plausible. **This is the weakest assumption in the model.**

| Case | Calculation | Result |
|---|---|---|
| Low | 1,706 × 0.25 | **427** |
| Base | 3,766 × 0.30 | **1,130** |
| High | 9,574 × 0.35 | **3,351** |

### ➤ **SAM (accounts): 427 – 1,130 – 3,351**

## Step 5 — Platform-tier revenue

**ACV assumptions [ASSUMPTION], benchmarked to observed comparables:**

| Tier | ACV | Anchor |
|---|---|---|
| Low | $50K | Drata median low end ($25–34K) plus a premium for attesting rather than collecting evidence [SOURCED Vendr, W] |
| **Base** | **$85K** | At the top of Vanta Enterprise ($40–90K) [SOURCED, W]; at parity with DevTools enterprise ($95K) [SOURCED, W]; below OneTrust multi-module ($100–150K+) [SOURCED, W] |
| High | $150K | OneTrust multi-module tier; requires a genuinely multi-entity platform deployment [SOURCED, W] |

| Case | Calculation | Result |
|---|---|---|
| Low | 427 × $50,000 | **$21.4M** |
| Base | 1,130 × $85,000 | **$96.1M** |
| High | 3,351 × $150,000 | **$502.7M** |

## Step 6 — Variable tier: per-attested-application

**[ASSUMPTION]** on all three inputs:

| Input | Low | Base | High | Anchor |
|---|---|---|---|---|
| Attach rate | 30% | 30% | 30% | [ASSUMPTION] |
| Applications under attestation, year 1 | 500 | 1,500 | 4,000 | [ASSUMPTION], anchored on 1,000–5,000 portfolio size **[SOURCED D20]** × 10–25% in-scope in year 1 |
| Price per application per year | $50 | $100 | $200 | [ASSUMPTION], bracketed by AWS Blu Age $0.10/LOC **[SOURCED W]** and the $6–8M manual-documentation alternative for a 20M-LOC estate **[DERIVED from SOURCED W]** |

| Case | Calculation | Result |
|---|---|---|
| Low | 128 accounts × (500 × $50) | **$3.2M** |
| Base | 339 accounts × (1,500 × $100) | **$50.9M** |
| High | 1,005 accounts × (4,000 × $200) | **$804.0M** |

## Step 7 — SAM revenue

| Case | Platform | Variable | **Total SAM** |
|---|---|---|---|
| Low | $21.4M | $3.2M | **$24.6M** |
| **Base** | **$96.1M** | **$50.9M** | **≈ $147M** |
| High | $502.7M | $804.0M | **$1,306.7M** |

⚠️ **Do not use the High column as a planning number.** It compounds the weakest three inputs simultaneously (ReadyContacts' 15,957 org count, 35% vertical share, and $200/app) and assumes ~4,000 applications under attestation per account. It is an outer bound, not an estimate.

**➤ SAM ≈ $147M annual at base case. Realistic planning range: $25M – $150M.**

## Step 8 — Broader TAM (drop geography and vertical gates)

**[ASSUMPTION]:** global × >1,000 EE × (banking + insurance + **government**) at 40%.

```
6,276 × 0.9375 × 0.40 = 5,884 × 0.40 = 2,354 accounts
Platform:  2,354 × $85,000              = $200.1M
Variable:  2,354 × 0.30 × 1,500 × $100 = $105.9M
                                TOTAL   = $306.0M
```

**➤ TAM ≈ $306M annual.** (2.08× SAM — consistent with adding geography and government.)

## Step 9 — Category-expansion TAM (drop the IBM Z gate)

**The beachhead cannot produce a venture-scale outcome. This is the arithmetic that matters.**

Addressable categories, 2026:

| Category | 2026 size | Source | Label |
|---|---|---|---|
| AI governance | **$492M** | Gartner press release | **[SOURCED] [F]** |
| AI Code Review & SDLC Governance | **~$1,103M** (from $955M in 2025 @ 15.5% CAGR) | YH Research / MarketPublishers | **[SOURCED] [S]**, growth **[DERIVED]** |
| GRC software — attestation/evidence slice @ 10–20% | **$0.5–1.8B** | from Verdantix $5–9B band | **[DERIVED]** from **[SOURCED] [S]**, slice % **[ASSUMPTION]** |
| AppSec — attestation/evidence slice @ 10–15% | **$1.1–1.65B** | from Juniper $11B | **[DERIVED]** from **[SOURCED] [S]**, slice % **[ASSUMPTION]** |
| **Total addressable category** | **≈ $3.2–5.0B** | | |
| **At 2–4% share** | **≈ $64M – $202M** | | **[ASSUMPTION]** on share |

**➤ Category-expansion serviceable revenue at maturity: $64M – $202M.**

The honest reading: **the $492M Gartner number is small, but Gartner measures *AI governance platforms*, which is not where attestation revenue lands.** Attestation revenue lands in the evidence-and-assurance layer of GRC and AppSec — a $3–5B pool — plus the new AI-code-governance category. **Gartner's number is the smallest credible estimate of the smallest relevant category. Do not lead with it.**

## Step 10 — SOM

**The binding constraint is distribution, not market size.** Evidence:

| Comparable | Time to scale | Outcome | Source | Label |
|---|---|---|---|---|
| **Vanta** | ~8 years | **$300M ARR, 16,000 customers** | company press release + Fortune | **[SOURCED] [F]** |
| Drata | ~5–6 years | ~$98M ARR, ~7,000 customers | Sacra | **[SOURCED] [W]** |
| Your likely motion | — | enterprise, air-gapped, 30–90 day POV, procurement at week 10–12 | prior dossier | **[SOURCED]** |

**Vanta reached $300M ARR — 2.0× the entire base-case SAM of this business — with 16,000 customers over eight years.** That is the observed ceiling of selling assurance tooling to enterprises, and it took a PLG-plus-inside-sales motion, a category-defining brand, and $500M+ raised. **The single most important number in this section: the most successful compliance-automation company ever built could not exceed the size of this market's entire beachhead.**

**[ASSUMPTION]** customer adds, ramping enterprise sales with a new-vendor logo requirement and sovereignty constraints:

| Year | Customers | ACV | ARR |
|---|---|---|---|
| Y1 | 3 | $85K | $0.26M |
| Y2 | 8 | $100K | $0.8M |
| **Y3** | **20–30** | **$85–120K** | **$1.7M – $3.6M** |
| Y5, direct only | 80 | $130K | **$10.4M** |
| Y5, with IBM channel | 200 | $150K | **$30.0M** |

**➤ SOM: $1.7–3.6M ARR at Y3; $10–30M ARR at Y5.**

**Sanity check [DERIVED]:** $10.4M ARR ÷ $130K ACV = **80 accounts ÷ 1,130 SAM accounts = 7.1% of SAM.** That is a credible market share for a category leader. **The SOM is execution-constrained, not market-constrained — which is the correct place for a young company to be.**

## The verdict, stated plainly

1. **The base-case SAM is ~$147M. That does not support a venture-scale outcome on its own.** At 5–10% share it yields $7–15M ARR. Say so before an investor does.
2. **IBM Z is a wedge and a credibility mechanism, not the market.** Its value is that 85% of installed MIPS is stable or growing **[SOURCED] [F]**, that Gartner predicts 75% of mainframe-exit vendors will fail by 2030 **[SOURCED]**, and that an unattested estate is a supervisory problem under DORA (in force since 17 Jan 2025 **[F]**) and the EU AI Act's Annex III high-risk regime (2 Dec 2027 **[F]**).
3. **The expansion is where the size is** — the $3–5B attestation-and-assurance pool, of which a new "AI Code Review and SDLC Governance" category ($955M in 2025 → $2,465M in 2032 **[SOURCED]**) is the fastest-growing slice.
4. **The forcing functions are dated, and the nearest one is already law.** DORA applies now. FedRAMP 20x Phase 3 is active with CR26 due FY26 Q3 and the submission pipeline opening FY26 Q4. The OMB M-24-15 OSCAL mandate on *"agency GRC and system-inventory tools"* passed in **July 2026**. EU AI Act Annex III lands **2 Dec 2027**.
5. **The most valuable single number in this entire document is Qodo's 90%/45% gap** — 90% of engineering leaders think they can report on AI's impact; fewer than half can trace AI activity to the code changes it produces. That is your wedge, stated by people who admit they have the hole. Disclose that Qodo commissioned it.
6. **Two claims you were given are wrong and should be dropped:** "1.5 trillion lines of COBOL" is 1.5 trillion *tokens* across 115 languages **[F] IBM**; and "9 months / 14 engineers → 3 days" is a LinkedPost inflation of an IBM case study that says **~30 days, 3 days, 2 people, zero defects, 100% functional equivalence** **[F] IBM**.

## What would change these numbers

| If this turns out to be true | Then |
|---|---|
| A real technographic count shows >50% of IBM Z orgs are FS (not 30%) | SAM rises ~1.7× to ~$250M |
| IBM Z enterprise count is nearer 15,957 than 6,276 | SAM rises ~2.4× (but this is the weakest input, so treat as noise) |
| Per-application attestation proves unworkable (buyers won't scope portfolios) | SAM collapses to the platform tier only: **$96M base** |
| ACV lands at Vanta Enterprise ($40–90K) not $85K+variable | SAM ≈ $70M. **This is the single biggest downside risk.** |
| IBM ships credible independent verification into Bob PP for Z | Category-expansion TAM compresses; you are now a feature, not a company |

---

# Gaps — could not verify

**This section is the point of the document.** Each item is something a serious reviewer will ask about and there is no honest answer.

### Numbers that do not exist

| # | Gap | Why it matters | Nearest available |
|---|---|---|---|
| 1 | **IBM Z revenue in absolute dollars** | Anchors the whole platform's economics | IBM discloses **% change only** (+51.7% FY2025). Cannot be derived: Hybrid Infrastructure $10,618M **[F]** also contains Distributed Infrastructure, and no prior-year IBM Z dollar figure is published. |
| 2 | **Number of IBM Z enterprises** | The TAM denominator | Technographic vendors: 2,844 / 6,276 / 15,957 — **5.6× spread** **[W]**. IBM discloses nothing. |
| 3 | **% of mainframe applications that are undocumented** | Your core problem statement | **Nothing credible exists.** METI's government definition of "black-boxing" as a defining legacy characteristic **[F]** is the strongest substitute. Every circulating percentage is unsourced. |
| 4 | **Current COBOL developer count** | Scarcity narrative | Last credible global count: **Gartner 2004, ~2 million** **[X]**. The 2026 "24,000 US" figure has no methodology. |
| 5 | **% of mainframe orgs that are banks or insurers** | The weakest assumption in the model | Nothing published. 25/30/35% is my assumption. |
| 6 | **Applications per large bank portfolio** | Drives the variable revenue tier | **One** real published data point: KBC **1,359** **[W]**. BNY Mellon's 112,500 is *programs*, 2012, a different unit. |
| 7 | **Average LOC per application** | Same | Advanced Systems says **8.86M**; KBC's real portfolio implies **4,213** — a **47× conflict**. Do not use 8.86M. |
| 8 | **IBM Bob PP for Z pricing** | Competitive positioning | Not published. Sales-led. IBM's page says only "prices are indicative." |
| 9 | **IBM Bob / Bob PP for Z customer counts** | Adoption evidence | Zero. Only internal IBM teams plus Blue Pearl. |
| 10 | **IBM watsonx Orchestrate pricing** | Channel economics | None found. |
| 11 | **Secureframe ARR** | Third comparable | Not disclosed, while Vanta ($300M **[F]**) and Drata ($98M **[W]**) both are. |
| 12 | **FedRAMP RFC-0024** (alleged Sept 2026 universal OSCAL deadline) | A near-term US forcing function | Cited only by a vendor (quzara.com). **Could not retrieve from fedramp.gov.** Treat as unverified. |
| 13 | **EU AI Act Art. 50 exact day in Aug 2026** | Compliance deadline precision | EC says "August 2026" without a day **[F]**. A secondary source says 2 Dec 2026 — unreconciled. |
| 14 | **Any analyst sizing "intent attestation" as a named category** | Your category claim | No house sizes it. Closest proxies: "AI Code Review and SDLC Governance" $955M **[S]**; "AI-Generated Code Assurance Services" $1.1B but *services not software* **[S]**. |
| 15 | **Total COBOL applications worldwide** | Bottom-up volume | Not derivable from any published LOC figure, because "application" is undefined across sources. |

### Claims that are circulating and are false or unsourced — **do not use**

| Claim | Reality |
|---|---|
| **"1.5 trillion lines of COBOL"** | 1.5 trillion **tokens**, 115 languages **[F] IBM newsroom**. No such COBOL figure exists. |
| **"9 months and 14 engineers → 3 days"** | LinkedIn inflation. IBM's own case study: **~30 days / 30+ person-days → 3 days, 2-person team**. Versions differ by two orders of magnitude in effort. |
| **"92% of COBOL developers will retire by 2027"** | **Zero primary source found.** Widely repeated by content farms. |
| **"92% of failed projects trace to incomplete business logic mapping (Gartner Advisory 2023)"** | No such Gartner publication located. |
| **"70% of legacy rewrites fail or exceed timeline"** | Unsourced. |
| **"72% of mainframe apps have rules no one wrote down"** / **"67% lack usable documentation"** / **"40 hours per screen"** / **"+287% budget overrun"** / **"66% of 29 migrations failed"** / **"49% fail because current state not mapped"** | All unsourced, all from one content-farm cluster. |
| **Bob Pro+ "$60/mo" and Ultra "$200/mo"** | Inconsistent with IBM's documented $0.50/Bobcoin. Should be $80 and $250. **Not confirmed.** |
| **RFC-0024 / universal Sept 2026 OSCAL deadline** | Unverified. |
| **Gartner AST market share "68% North America"** | This one **is** sourced — but it is **2022 data in a May 2023 document**. Do not present as current. |

### Numbers that are real but weaker than they look

| Number | The problem |
|---|---|
| COBOL "800 billion lines" | Best-designed study (production-only, weighted by respondent doubt, n=1,104) but **vendor-commissioned by a COBOL tooling vendor whose stated goal was to "own the COBOL space"**, and it sits 3.5× above the 220–240B cluster. |
| COBOL developer salaries | $81,538 (Salary.com) to $120,000 (Coursera) for nominally the same role. **A measurement artefact, not a scarcity premium.** |
| "AI Code Review and SDLC Governance $955M" | From a small Chinese research house with a Japanese-country-segmentation template. Real category definition, **low-confidence sizing**. |
| Qodo's 89% / 3.7% / 90% / 45% figures | **The most decision-relevant dataset here, and vendor-commissioned by a vendor selling the answer.** Directionally corroborated by peer-reviewed evidence in `evidence-dossier.md` §4.3. Disclose always. |
| Forrester "9 in 10 rewrites fail" | Real Forrester research, n=300+, but **commissioned by Rocket Software**, which sells modernisation tooling. |
| GrowthSpree "$35K DevTools ACV" | An agency publishing its own benchmark. The number you started from is the weakest load-bearing input in the DevTools comparison. |
| Vanta/Drata/Secureframe contract values | All **quote-only**. Ranges come from procurement aggregators, which themselves say "treat as ranges, not guarantees." |
| All assurance cost benchmarks | Vendor-authored. Nobody publishes an independent, audited cost of SOC 2 or ISO 27001. |

---

# Appendix — the credibility problem, and a source blacklist

**A large fraction of the search space for "mainframe modernisation statistics" is AI-generated content that recycles invented numbers with real-sounding attribution.** This is not a minor problem: several of the most quotable stats in this category ("287% budget overrun", "67% lack documentation", "92% retire by 2027") trace to it. Future research on this topic will keep rediscovering them.

**Identified content-farm cluster — do not cite:**

`entrans.ai` · `replay.build` · `softwaremodernizationservices.com` · `sthenostechnologies.com` · `zipdo.co` · `hypercubic.ai` · `datafield.dev` · `valintry.com` · `devsu.com` · `mainframe-brain` (PyPI) · `cegeka.com` · `riem.ai` · `noah-news.com` · `itnewsafrica.com` · `calliber.net` · `cipherssecurity.com` · `aipromptshub.co` · `stackfyi.com` · `episki.com` · `globenewswire.com` syndication of press-release-for-pay reports

**Diagnostic tells:** the same statistic restated across multiple domains; attribution to "industry data" or "industry reports" with no named author; internally contradictory figures in the same article; confident percentages with no methodology; a commercial interest in the conclusion; and — most reliably — **a URL that 429s or requires a lead-capture form.**

**Agglators that are nonetheless reliable** (verified against independent sources during this research): `zolmax.com` (IBM earnings-call highlights, cross-checked against Network World and Futurum), `brainstorm.itweb.co.za` (carried the IBM 71% claim, corroborated elsewhere), `tech-stack.com` and `dfarber.com` (used only for named, checkable historical events — CBA, TSB, RBS, Hershey — which are verifiable independently).

**The source hierarchy that actually worked for this project, in order:**

1. **SEC filings and earnings-call transcripts** — gave the only unambiguous IBM Z figures (140M MIPS, 85% stable/growing, −42% in 2Q26, and the fact that IBM Z dollars are not disclosed).
2. **Government and quasi-government publications** — METI's 2025 legacy report, GAO's FedRAMP cost finding, OMB M-24-15, the Commission's AI Act page. These are dated, methodologically described, and free of commercial interest.
3. **Named analyst documents with visible methodology** — Vanson Bourne (n, countries, sampling frame stated), METI (n, field dates, page cites), ISBSG (filter criteria and its own caveats), SlashData (survey waves and triangulation).
4. **Gartner/IDC/Forrester MQ abstracts and press releases** — usable for category structure, geography splits and named figures, but the paid reports are paywalled and the press releases under-report.
5. **Vendor case studies** — usable when the vendor is measuring something *against its own interest* (zero defects, full functional equivalence) and when corroborated across multiple properties. Blue Pearl's zero-defect and 100%-equivalence numbers pass that test; its 9-month framing does not.
6. **Vendor pricing pages** — the only genuinely reliable vendor-published numbers, because they are contractual.

---

*Compiled 26 September 2026. Sections A and B carry the sourcing; Section C carries the pricing benchmarks; Section D and the derived model carry the arithmetic. Every derived number is reproducible from the tables above. The "Gaps" section is the honest boundary of what this research establishes.*



