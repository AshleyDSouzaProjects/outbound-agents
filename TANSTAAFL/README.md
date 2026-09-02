# TANSTAAFL

**There Ain't No Such Thing As A Free Lunch.**

An agent system for finding mispriced Indian equities in the Nifty 500, built on the
principles of Pulak Prasad, Warren Buffett, and others (`doctrine/`).

---

## The one-paragraph thesis

Fundamental analysis used to be gated by labour: collecting, collating and analysing years of
annual reports. Agents make that labour trivial — and therefore worthless as an edge. If we
can do it in one pass, so can everyone, and it is already in the price. This system is built
on the assumption that **the edge is not extraction**. It is (1) holding a time horizon most
capital cannot hold, (2) remembering what management promised and whether they delivered,
across 500 companies over a decade, (3) forcing base rates ahead of narrative, and
(4) pre-committing to kill criteria that cannot be rewritten later. The name is a reminder:
if the lunch looks free, we have not found an edge — we have failed to find the cost.

## Layout

```
TANSTAAFL/
├── PLAN.md          ← start here: sources, memory, agents, 12–24mo roadmap
├── CLAUDE.md        operating rules for agents working in this tree
├── doctrine/        encoded investment principles (the "why")
├── agents/          agent specs by funnel tier (00-ingest → 80-learning)
├── data/            raw (immutable) → staging → curated panels
├── memory/          evidence, graph, dossiers, promise-ledger, journal,
│                    base-rates, calibration   ← the actual moat
├── pipelines/       ingest, normalize, screen, backtest
├── research/        shortlist, deep-dives, post-mortems
├── portfolio/       paper, watchlist, monitoring
├── evals/           extraction accuracy, blowup detection, calibration, PIT
├── config/          universe definitions, thresholds, credentials (never committed)
└── scripts/         operational entry points
```

## The funnel

```
500 → [reject: governance, forensics, capital allocation] → ~80
    → [quality + management] → ~30
    → [expectations-based valuation] → ~15
    → [adversarial red team] → ~5
```

Rejection-first, because the asymmetry matters: a missed opportunity costs us nothing we had,
while a permanent loss costs us capital we cannot get back. We deliberately accept many
Type II errors (missing good investments) to avoid Type I errors (owning bad ones).

## Status

**Pre-implementation.** This tree currently contains the plan and doctrine. Nothing is
ingesting data and nothing is producing recommendations. See `PLAN.md` §4 for the phased
build and the gates each phase must pass before the next begins.

## Non-negotiables

1. **Point-in-time integrity** — no agent sees data published after the decision date.
2. **Provenance or it did not happen** — every number traces to document, page, line.
3. **Thesis-builder ≠ thesis-killer** — separate agents, opposing mandates.
4. **Pre-registered falsifiers** — written before the position, immutable after.
5. **Default action is nothing** — the system should usually recommend doing nothing.
6. **Human commits capital** — the system proposes and documents; it does not trade.

## Not investment advice

This is a research system. Its outputs are hypotheses with documented reasoning and explicit
falsifiers, not recommendations. Calibration must be demonstrated over years before any output
deserves weight.
