# Agent Manifest

Agents are organised by funnel tier. Numbering is execution order; cost per name rises ~100×
from Tier 2 to Tier 6, which is what makes covering 500 names affordable.

Specs marked ★ are the differentiated agents — the ones that create edge rather than parity.
Full specs exist for those; the rest are contracts to be implemented.

```
500 → T2 reject → ~80 → T3/T4 quality+mgmt → ~30 → T5 valuation → ~15 → T6 red team → ~5
```

---

## Tier 0 — Ingestion (`00-ingest/`)

| Agent | Input | Output | Cadence |
|---|---|---|---|
| `filing-harvester` | Exchange feeds | Hashed docs → `data/raw/`, index → `memory/evidence/` | Continuous |
| `document-parser` | Raw PDF/XBRL | Structured tables, notes, segments → `data/staging/` | On ingest |
| `transcript-processor` | Concall audio/text | Speaker-attributed, claim-tagged → `data/staging/` | Quarterly |

**Contract:** never mutate `data/raw/`. Every output carries the source hash.

## Tier 1 — Extraction (`10-extract/`)

| Agent | Purpose |
|---|---|
| `financial-normalizer` | Common-basis restatement; consolidation, exceptionals, Ind AS breaks |
| `entity-resolver` | Canonical entity IDs; maintains the `memory/graph/` edges |

**Contract:** every normalised cell points back to a source document, page and line.
Missing data is marked missing, never interpolated.

## Tier 2 — Rejection (`20-reject/`) — runs on all 500

| Agent | Rejects on |
|---|---|
| `governance-sentinel` ★ | Promoter pledge, RPT intensity/trend, auditor events, board independence, contingent liabilities |
| `forensic-accountant` | Cash conversion, accruals, receivable/inventory drift, expense capitalisation, tax anomalies, subsidiary losses |
| `capital-allocation-auditor` | Incremental ROIC, dilution, acquisition record, buyback-vs-issuance behaviour |

**Contract:** hard-reject authority. Every reject logged with reasons to
`research/shortlist/rejects.md`. Revisited annually, never permanently blacklisted.
**When in doubt, reject.**

## Tier 3 — Business quality (`30-quality/`) — survivors only

| Agent | Purpose |
|---|---|
| `moat-analyst` | Dorsey taxonomy; **evidence-based** — a moat claim without a quantitative pricing-power or share-stability test is struck |
| `roce-persistence-analyst` | ROCE = margin × turns; durability against `memory/base-rates/` |
| `reinvestment-runway-analyst` ★ | Akre's third leg. Runway by arithmetic, not TAM hand-waving |
| `industry-structure-analyst` | Porter; concentration; regulatory exposure |

## Tier 4 — Management (`40-management/`)

| Agent | Purpose |
|---|---|
| `promise-keeper` ★ | Owns `memory/promise-ledger/`. Extracts forward-looking claims, resolves them at maturity, scores management credibility on the say/do delta |
| `scuttlebutt-agent` | Tier C alt data — job posts, employee/customer reviews, shipment data. **Corroborates or contradicts management; never originates a thesis** |

## Tier 5 — Valuation (`50-valuation/`)

| Agent | Purpose |
|---|---|
| `owner-earnings-analyst` | Buffett owner earnings; maintenance/growth capex split **derived and shown** |
| `epv-analyst` | Greenwald EPV + asset reproduction; growth credited only after a passed moat test |
| `expectations-analyst` ★ | Reverse DCF — what does the price imply, and how does that compare to base rates? |
| `scenario-modeler` | Distributions, not point estimates |

**Contract:** no agent in this tier emits a target price. Output is always implied-expectations
vs base rate.

## Tier 6 — Adversarial (`60-adversarial/`)

| Agent | Purpose |
|---|---|
| `red-team` ★ | **Mandated and rewarded for killing the thesis.** Must not be the agent that built it |
| `pre-mortem-agent` | "It is 2031, this lost 60%, write the post-mortem" |
| `base-rate-checker` | Flags any thesis requiring above-base-rate outcomes, and by how much |

**Contract:** a red-team pass that finds nothing must state what evidence would have changed
its verdict. Otherwise it did not genuinely try and the pass is void.

## Tier 7 — Portfolio (`70-portfolio/`)

| Agent | Purpose |
|---|---|
| `portfolio-constructor` | Fractional-Kelly-capped sizing; concentration and correlation limits; liquidity check |
| `investment-committee` | Synthesises; forces written kill criteria before any position |
| `monitor` | Continuous watch on holdings for **thesis-breaking events only** — not price alerts |

## Tier 8 — Learning (`80-learning/`)

| Agent | Purpose | Feedback lag |
|---|---|---|
| `calibration-scorer` | Brier/log scores by agent, sector, horizon, claim type | 1–4 quarters |
| `post-mortem-agent` | On broken theses: what did we miss and was it knowable? | Event |
| `base-rate-updater` | Refreshes `memory/base-rates/` from our own corpus | Quarterly |
| `heuristic-evolver` | Proposes agent-instruction changes from **scored** errors only | Quarterly |

**Contract:** `heuristic-evolver` may propose but never auto-apply. Every change is reviewed,
dated and reversible — an unreviewed self-modifying prompt loop is how a system silently
optimises itself into nonsense.

---

## Universal contracts

Every agent, without exception:

1. **Point-in-time.** Declares its as-of date; never reads data published after it.
2. **Provenance.** Every number carries a source pointer. Estimates labelled `ESTIMATE` with derivation.
3. **Uncertainty.** States confidence and what would change its mind.
4. **Source discrimination.** Never presents a management claim as fact.
5. **No-action default.** Silence is a valid and expected output.

## Implementation note

These become Claude Code subagent definitions (`.claude/agents/*.md` with frontmatter) when
built, following the pattern already used elsewhere in this repository. The tier directories
hold the specs; orchestration lives in `pipelines/`.
