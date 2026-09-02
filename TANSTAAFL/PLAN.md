# TANSTAAFL — Build Plan

**Goal:** identify mispriced equities in the Nifty 500 using the principles of Prasad,
Buffett and others, operated by a system of AI agents.

**Name:** *There Ain't No Such Thing As A Free Lunch.* The name is the first design
constraint, not a joke. If a lunch looks free, we have not found an edge — we have
failed to find the cost.

---

## 0. The premise, and the problem with it

The observation that motivates this project is correct:

> The main work of fundamental analysis used to be collecting, collating and analysing
> tons of data from annual reports. That is now trivially possible with an AI agent.

The conclusion most people draw from it is wrong. If extraction is trivial for us, it is
trivial for everyone. **Anything an agent can do in one pass over public filings will be
in the price.** Commoditised capability is not edge; it is table stakes. A system built
on "we read annual reports faster" is a system with no edge, and it will underperform
after costs.

So the first job of this plan is to say **where the edge actually is**, and to build only
things that serve it.

### Where edge can still exist

| # | Source of edge | Why it survives commoditisation |
|---|---|---|
| 1 | **Time horizon** | Most capital cannot wait 5–10 years. Career risk, redemption risk and quarterly reporting force short horizons. This is *structural*, not informational — it cannot be arbitraged away by better data. It was Prasad's actual edge. |
| 2 | **Longitudinal say/do memory** | Nobody systematically tracks what management *promised* on a concall in 2019 against what they *delivered* by 2024, across 500 companies. It is pure tedium at human scale, and it compounds: worthless in month 1, decisive by year 3. |
| 3 | **Base rates over narrative** | Humans systematically ignore the outside view. An agent can be forced to check "how often does ROCE > 25% persist five more years?" before accepting any story. |
| 4 | **Behavioural pre-commitment** | Pre-registered kill criteria that cannot be rewritten after the fact. The system does not panic, does not fall in love, and does not quietly move the goalposts. |
| 5 | **Forensic breadth** | Reading every related-party note, auditor change and contingent-liability schedule across 500 companies × 15 years. Feasible for an agent, not for a person. |

Items **2 and 5** are the genuinely *new* capabilities. Items **1, 3 and 4** are old edges
that agents make easier to *hold*. Everything in this plan exists to serve one of these five.

### What we explicitly do NOT claim as edge

- Faster reading of filings.
- Sentiment scores, news scraping, "AI-powered" price prediction.
- Discretionary macro or market timing. (Established earlier in this repo's Nalanda
  work: timing contributed ~0% to Prasad's record. We are not going to rediscover it.)
- Anything requiring us to be smarter than the market about next quarter's EPS.

---

## 1. Information sources

Three tiers, roughly by cost and by how much edge they actually carry.

### Tier A — Regulatory primary (free, mandatory, high trust)

These are the backbone. Everything traces back here.

| Source | Contents | Cadence | Notes |
|---|---|---|---|
| **BSE / NSE corporate filings** | Announcements, results, board outcomes | Continuous | Primary trigger for all ingestion |
| **Annual reports (PDF)** | MD&A, notes, RPTs, auditor report, CARO | Annual | The single richest document; notes matter more than the P&L |
| **Quarterly results (XBRL)** | Standalone + consolidated financials | 45 days post-quarter | Structured — cheap to normalise |
| **Shareholding patterns** | All holders > 1%, promoter pledge % | Quarterly | Reconstructs any institution's position history, incl. Nalanda's |
| **SEBI SAST / PIT filings** | Insider and promoter transactions | Event-driven | Promoter *buying* is a real signal; selling is noisier |
| **Bulk / block deals** | Executed price, quantity, counterparty | Daily | Actual institutional execution prices |
| **Credit rating rationales** (CRISIL, ICRA, CARE) | Debt structure, covenants, analyst concerns | Event-driven | **Underrated.** Rating agencies see the debt schedule and often flag stress 2–4 quarters before equity analysts |
| **MCA21 / RoC** | Unlisted subsidiary and RPT-counterparty accounts | Annual | Where money hidden from the consolidated view can be found |
| **Concall transcripts + audio** | Management guidance, Q&A, evasions | Quarterly | Feeds the promise ledger — our highest-value proprietary asset |
| **Exchange bhavcopy** | OHLCV, adjusted for corp actions | Daily | Must be corporate-action adjusted or every backtest lies |
| **RBI / MOSPI / GST aggregates** | Rates, credit growth, IIP, CPI | Monthly | Sector context only — never a timing input |

### Tier B — Commercial (cheap → expensive)

- **Screener.in** — 10-year standardised financials, exportable. Best value in the Indian market; the pragmatic starting point.
- **Trendlyne / Tijori / Finology** — shareholding history, concall archives, forensic flags.
- **Refinitiv / Bloomberg / CapIQ** — only if the operation scales enough to justify it. Not needed for v1.
- **EODHD / AlphaVantage** — adjusted price series if exchange bhavcopy handling proves painful.

### Tier C — Alternative / scuttlebutt (Fisher's method, automated)

Genuinely differentiated, and cheap. This is Phil Fisher's "scuttlebutt" at machine scale.

- **Job postings** — headcount by function is a leading indicator of capex and expansion intent, and it contradicts management guidance more often than you would expect.
- **Employee reviews** (Glassdoor, AmbitionBox) — attrition and culture; strong leading indicator of execution problems in services businesses.
- **Customer reviews** (Amazon, Flipkart) — product quality drift for consumer names.
- **App download / DAU** (Sensor Tower et al.) — for platform businesses.
- **Import/export shipment data** (Volza, Zauba) — actual physical volumes, hard to fake.
- **Google Trends** — brand demand proxy.

**Rule:** alt data is used to *corroborate or contradict* management claims. It is never a
primary thesis driver. It is evidence in the promise ledger, not a signal in a model.

---

## 2. Memory architecture

The memory design *is* the system. Agents are replaceable; the accumulated, structured,
provenance-tracked memory is the moat. Nine layers.

```
memory/
├── evidence/          L1  immutable raw + provenance index
├── graph/             L3  entities and relationships over time
├── dossiers/          L4  living per-company thesis (git-versioned)
├── promise-ledger/    L5  management say → do, resolved over time   ★
├── decision-journal/  L6  every call, with pre-registered falsifiers ★
├── base-rates/        L7  empirical outside-view distributions
└── calibration/       L8  forecast vs outcome scoring
```

**L1 — Evidence store (immutable).** Every document content-hashed, dated, never edited.
Append-only. Provenance is sacred: *every number in the system must be traceable to a
document, page and line.* A number without provenance is not a fact and cannot enter a thesis.

**L2 — Structured facts.** Normalised financial panels (Parquet/DuckDB), each cell carrying
a pointer back into L1. Handles restatements, consolidation changes, exceptional items and
accounting-standard transitions (Ind AS migration breaks most naive 10-year series).

**L3 — Entity graph.** Companies, promoters, directors, auditors, subsidiaries, RPT
counterparties, customers, suppliers, competitors — with **time-valid edges**. This is what
catches *"this company's new auditor is the same firm that signed off on three companies that
later restated"* and *"this independent director sits on six boards, two of which had
qualified opinions."* Cross-company pattern detection is impossible without it.

**L4 — Company dossiers.** Living markdown, git-versioned so the *diff history is itself
memory*: we can see exactly what we believed about a company in 2026 and what changed. Each
holds business model, moat assessment with evidence, quality scorecard, valuation range,
and explicit kill criteria.

**L5 — Promise ledger ★.** Every forward-looking management statement, extracted from
concalls and annual reports with date and speaker, then **resolved** at maturity as
kept / missed / vague / abandoned. Produces a per-management credibility score grounded in
evidence rather than impression. *This is the crown jewel.* It is worth nothing in month one
and cannot be bought at any price in year three — which is exactly what a durable edge looks like.

**L6 — Decision journal ★.** Every recommendation with reasoning, confidence, position size
and **pre-registered falsifiers**. Written before the outcome is known, immutable after.
Without this, learning is impossible — a system that can rewrite its reasoning after the fact
learns nothing and will confidently narrate its own luck back to itself.

**L7 — Base-rate library.** Empirical distributions built from our own corpus: ROCE
persistence by decile, margin mean-reversion by sector, capex-cycle outcomes, acquisition
success rates, the fate of companies whose receivable days rose three years running. The
outside view, on tap.

**L8 — Calibration store.** Predictions vs outcomes, scored (Brier / log score), sliced by
agent, sector, horizon and claim type. Drives the learning loop in §4.

**L9 — Working memory.** Per-run scratch, compacted into L1–L8 on completion. Nothing of
value lives only here.

### Pragmatic stack

DuckDB + Parquet (panels) · Postgres with pgvector *or* LanceDB (semantic retrieval over
transcripts) · edge tables for the graph (Neo4j only if it earns its keep) · git for
dossiers and journals. **Resist over-engineering.** A solo operator can run all of this on
one machine; distributed infrastructure at v1 is a way to spend two years not investing.

---

## 3. Agent architecture

Shaped as a **rejection-first funnel** — Prasad's asymmetry between Type I and Type II
errors made structural. Cheap, brutal filters run on all 500; expensive judgment runs only
on survivors. Cost per name falls by ~100× across the funnel, which is what makes covering
500 names affordable.

```
   500 names
      │  Tier 0-1  ingest + normalise (mechanical)
      ▼
   500 names
      │  Tier 2  REJECT — governance, forensics, capital allocation
      ▼
   ~80 survive                          ← most value is created HERE
      │  Tier 3-4  quality + management
      ▼
   ~30 survive
      │  Tier 5  valuation (expectations-based)
      ▼
   ~15 candidates
      │  Tier 6  adversarial — mandate to kill
      ▼
   ~5 pass          →  Tier 7 portfolio  →  Tier 8 learning (continuous)
```

### Tier 0 — Ingestion — **runs on the operator's machine**

Built as a CLI, not an agent: `ingest/` (`tanstaafl-ingest`). It is split out because ingestion
and analysis have opposite requirements — ingestion needs network, credentials and a residential
IP; analysis needs none of them and must be **reproducible**, which anything touching the live
web cannot be. `ingest/CONTRACT.md` states the boundary.

- `tanstaafl-ingest drop` — ingest local files; works offline. *Built and tested.*
- `tanstaafl-ingest fetch {screener,nse_bhavcopy,nse_filings}` — remote adapters. *Written, not
  yet run against the live services.*
- `document-parser` — PDF/XBRL → structured tables, notes, segment data. Must handle scanned reports.
- `transcript-processor` — concalls → speaker-attributed text, claims tagged and dated.

Everything from Tier 1 upward reads through `CorpusReader`, which is stdlib-only, read-only and
enforces the point-in-time cutoff in code.

### Tier 1 — Extraction & normalisation
- `financial-normalizer` — common-basis restatement; consolidation, exceptionals, Ind AS breaks.
- `entity-resolver` — canonical entity IDs; builds and maintains the L3 graph.

### Tier 2 — Rejection filters *(run on all 500, aggressive, cheap)*
- `governance-sentinel` — promoter pledge, RPT magnitude and trend, auditor changes and resignations, board independence, contingent liabilities. **Hard reject authority.**
- `forensic-accountant` — cash conversion (CFO/EBITDA), accrual ratios, receivable and inventory-day drift, expense capitalisation, tax-rate anomalies, subsidiary losses, Beneish-style composites.
- `capital-allocation-auditor` — incremental ROIC, dilution history, acquisition track record, buyback-vs-issuance behaviour, dividend policy sanity.

> A reject is **logged with reasons and revisited annually**, never silently dropped. The
> reject list is an asset: it is where the Type I errors we successfully avoided are recorded.

### Tier 3 — Business quality *(survivors only)*
- `moat-analyst` — Dorsey taxonomy (intangibles, switching costs, network effects, cost advantage, efficient scale). **Evidence-based, not assertion-based**: a moat claim must cite a pricing-power test or a share-stability fact.
- `roce-persistence-analyst` — decomposes ROCE into margin × turns; assesses durability against the L7 base rates.
- `reinvestment-runway-analyst` — Akre's third leg. Can they redeploy capital at high ROIC? Runway maths, not TAM hand-waving. *The most commonly skipped and most decisive question.*
- `industry-structure-analyst` — Porter, concentration, regulatory exposure.

### Tier 4 — Management
- `promise-keeper ★` — owns L5. Scores credibility on the historical say/do delta.
- `scuttlebutt-agent` — Tier C alt data; corroborates or contradicts management claims.

### Tier 5 — Valuation
- `owner-earnings-analyst` — Buffett owner earnings; splits maintenance from growth capex (the hard part, and where most models quietly cheat).
- `epv-analyst` — Greenwald earnings power value + asset reproduction value + franchise value. More honest than DCF for durable businesses because it does not smuggle the answer into the terminal value.
- `expectations-analyst ★` — Mauboussin **reverse DCF**: solve for what the *current price* implies, then judge whether those implied expectations are plausible against base rates. This is the correct way to locate mispricing. We never say "our DCF says ₹X"; we say "the price requires 18% revenue growth for a decade, and only 6% of Indian companies have ever done that."
- `scenario-modeler` — distributions, not point estimates.

### Tier 6 — Adversarial *(separate agents, opposing mandate)*
- `red-team` — mandated and **rewarded for killing the thesis**. Must be a different agent from the one that built it. An agent that grades its own homework produces confident nonsense.
- `pre-mortem-agent` — "it is 2031 and this position lost 60%. Write the post-mortem."
- `base-rate-checker` — flags any thesis requiring above-base-rate outcomes, and states how far above.

### Tier 7 — Portfolio
- `portfolio-constructor` — position sizing (fractional-Kelly capped), concentration and correlation limits.
- `investment-committee` — synthesises, forces explicit written kill criteria before any position.
- `monitor` — continuous watch on holdings for thesis-breaking events only. **Not** price alerts.

### Tier 8 — Learning *(continuous — see §4)*
- `calibration-scorer`, `post-mortem-agent`, `base-rate-updater`, `heuristic-evolver`.

### Non-negotiable operating rules

1. **Point-in-time integrity.** No agent may see data published after the decision date. Violate this and every backtest becomes a lie that flatters you.
2. **Provenance or it did not happen.** Numbers without a source pointer cannot enter a thesis.
3. **Separation of powers.** Thesis-builder ≠ thesis-killer.
4. **Pre-registered falsifiers.** Kill criteria written before the position, immutable after.
5. **Default action is nothing.** The system should recommend "no action" the overwhelming majority of the time. Prasad: *don't be lazy — be very lazy.*
6. **Human disposes.** The system proposes and documents; a human commits capital, at least until calibration is proven over years.

---

## 4. How the system gets smarter over 12–24 months

### The hard problem, stated honestly

**Investment feedback loops are far slower than learning loops need to be.** A five-year
thesis takes five years to validate. In 24 months we will have almost **zero** signal on
whether our stock picks were good. Any plan claiming the system "learns from returns" inside
two years is selling something — with ~15 positions over 2 years, the noise utterly swamps
the signal, and a system that learns from that noise will confidently learn the wrong thing.

So we do not learn from returns. We learn from **fast proxies** with short feedback cycles,
chosen because they are causally upstream of investment quality.

| Proxy | Feedback lag | What it actually validates |
|---|---|---|
| Extraction accuracy | Days | Is the data layer trustworthy at all? |
| Blowup detection (historical) | **Immediate** | Would the filters have caught known frauds? |
| Short-horizon operating forecasts | 1 quarter | Do we understand the business mechanics? |
| Promise resolution | 1–4 quarters | Is the management-credibility model real? |
| Red-flag precision/recall | 1–8 quarters | Do our governance flags precede bad events? |
| Thesis-durability | 4–8 quarters | How often do our theses break, and did we foresee why? |

The single highest-leverage trick: **the blowup-detection eval is available on day one.**
Run the Tier-2 filters on point-in-time data for Satyam, Yes Bank, DHFL, IL&FS, Manpasand,
Vakrangee, Zee, Coffee Day and Gitanjali. If the filters do not reject those *before* their
collapse, using only data available at the time, the filters are worthless and we know it
immediately rather than in 2031.

### Roadmap

**Months 0–3 — Foundation.** Ingestion and normalisation for the Nifty 500; backfill 10–15
years; L1/L2/L3 live. Gate: **>99% extraction accuracy** on a hand-audited 200-line sample.
*No recommendations are produced in this phase.* Resist the urge; a fast wrong answer here
poisons every layer above it.

**Months 3–6 — Rejection engine.** Tier 2 built and validated against the historical blowup
set on point-in-time data. Gate: catches ≥7 of 9 known frauds pre-collapse, with a false-positive
rate low enough to leave a workable universe. Deliverable: a defensible reject list with
reasons, and a ~50–80 name survivor shortlist.

**Months 6–12 — Quality, valuation, first theses.** Tiers 3–6. First 10–15 full dossiers with
pre-registered kill criteria and calibrated probabilities. Paper portfolio opens; decision
journal live. Promise ledger begins accumulating — **it produces no value yet, and that is expected.**

**Months 12–18 — Calibration compounding.** Four-plus quarters of promise resolutions; first
real calibration curves; base-rate library populated from our own corpus rather than borrowed
studies; agent instructions refined from *scored* errors rather than impressions. Scuttlebutt
integrated. First post-mortems on broken theses — broken theses are the highest-information
events available at this stage.

**Months 18–24 — Compounding memory.** Eight quarters of say/do data. This is the inflection:
the promise ledger and entity graph now contain patterns **nobody else has structured** —
auditor networks, director networks, serial over-promisers. The system starts flagging things
a human analyst would not see, not because it is smarter but because it remembers more,
across more companies, for longer. Real capital is deployed only against documented calibration.

### The compounding curve

The value of this system is **not linear in time, and it is back-loaded.** Months 0–12 build
infrastructure with little visible output — this phase looks like failure and is not.
Months 12–24 the memory layers begin to pay. Beyond 24 months the promise ledger and graph
become genuinely unbuyable. Anyone can replicate the agents in a weekend; nobody can
replicate eight years of resolved management promises without waiting eight years.

**That is the free lunch that is not free, and it is the whole point of the name.**

---

## 5. Doctrine — whose principles, and why

Detailed in `doctrine/`. Summary of who is encoded and what each contributes:

| Source | Contribution |
|---|---|
| **Pulak Prasad** | Rejection-first filtering; Type I/II asymmetry; ROCE persistence; permanence; historical financials over forecasts |
| **Buffett / Munger** | Circle of competence; moats; owner earnings; margin of safety; inversion; management rationality |
| **Chuck Akre** | The three-legged stool — business, management, **reinvestment runway** |
| **Bruce Greenwald** | EPV and asset reproduction value; a more honest valuation frame than DCF |
| **Michael Mauboussin** | Expectations investing (reverse DCF); base rates; ROIC persistence; skill vs luck |
| **Howard Marks** | Second-level thinking; risk as permanent loss, not volatility; cycle awareness |
| **Terry Smith** | Cash conversion discipline; "do nothing" as an active strategy |
| **Nick Sleep** | Scale economics shared; destination analysis |
| **Phil Fisher** | Scuttlebutt — now automatable at scale (Tier C) |
| **Joel Greenblatt** | ROC + earnings yield as a cheap first-pass screen |
| **Kahneman / Tetlock** | Outside view; calibration; forecast scoring; the decision journal itself |
| **Saurabh Mukherjea** | India-specific forensic screens and promoter-governance framing |

**India-specific additions** (`doctrine/20-india-context.md`): promoter dominance and pledging,
related-party transactions as the primary expropriation mechanism, auditor resignations as a
leading fraud indicator, group/holdco structures, and the reality that governance risk — not
valuation risk — is what permanently impairs capital in Indian mid-caps.

---

## 6. Honest risks

- **Overfitting to the past.** Backtests on 2010–2020 will flatter any quality strategy, because that decade contained a once-in-a-generation quality re-rating (see this repo's Nalanda analysis: ~38% of Page Industries' return was multiple expansion, not earnings). **That lever is spent.** A system tuned on that decade will expect a re-rating that does not come.
- **The base-rate library is built from our own corpus** — small, Indian, recent. It will be noisy for years, and it will encode the survivor bias of the Nifty 500 constituent list unless we deliberately include delisted and ejected names.
- **Concentration is a double-edged multiplier.** It amplified Prasad's selection; it will amplify our errors identically.
- **We cannot escape TANSTAAFL.** If this works, it works because we held a horizon others could not and remembered things others did not bother to record. If we ever catch ourselves believing it works because our agents read faster, we have lost the plot and should stop.

---

*See `README.md` for orientation, `doctrine/` for encoded principles, `agents/README.md`
for the full agent manifest and I/O contracts.*
