# 11 — Buffett & Munger

---

## Circle of competence

Not "invest only in what you know" but the sharper version: **know precisely where the boundary
of your understanding is, and behave differently outside it.**

For an agent system this is unusually important, because an LLM will generate a fluent,
confident analysis of a business it does not understand at all. Fluency is not comprehension,
and the system has no native sense of its own boundary.

> **System implication:** every dossier must carry an explicit competence assessment. Sectors
> where we cannot model the economics from first principles — most financials, early-stage
> biotech, anything whose earnings depend on a regulatory decision or a commodity price we
> cannot forecast — are marked out-of-circle and rejected regardless of how attractive the
> numbers look. A required field, not an optional one.

## Economic moats

Durable competitive advantage. Use Pat Dorsey's taxonomy — it is the most operational version:

| Moat type | Evidence to demand |
|---|---|
| **Intangibles** (brand, patents, licences) | Pricing power above peers sustained through a downturn; gross margin stability |
| **Switching costs** | Customer retention/churn data; contract length; revenue concentration stability |
| **Network effects** | Value per user rising with user count; share gains accelerating |
| **Cost advantage** | Sustained unit-cost gap vs peers with a *structural* cause (scale, process, location, resource) |
| **Efficient scale** | Market naturally supports few players; new entrants historically fail |

**The rule that matters: a moat claim must cite evidence, never assertion.** "Strong brand" is
not a moat finding. "Raised prices 6–8% annually for nine consecutive years including through
FY20, while volume grew and gross margin held at 55%±2pp" is a moat finding.

> **System implication:** `moat-analyst` output is rejected if any claimed moat lacks a
> quantitative pricing-power or share-stability test.

## Owner earnings

Buffett's correction to reported EPS:

```
Owner earnings = reported earnings
               + depreciation & amortisation
               + other non-cash charges
               − maintenance capex          ← the hard, judgment-laden term
               ± working capital investment required to maintain competitive position
```

The difficulty is entirely in separating **maintenance** capex from **growth** capex.
Companies do not disclose the split, and every model quietly cheats here — usually by assuming
maintenance capex equals depreciation, which is convenient and often wrong.

> **System implication:** the maintenance/growth split must be *derived and shown*, with the
> method stated (e.g. capex-to-sales regression against a no-growth baseline, or a
> capacity-based estimate from the fixed asset schedule). A dossier that asserts the split
> without a derivation is incomplete.

## Margin of safety (Graham)

Buy meaningfully below conservative intrinsic value. Two purposes, and the second is more
important: it protects against **our own analytical error**, not just market volatility.

Given that our valuation frame is expectations-based, margin of safety is expressed as:
*the implied expectations in the current price are comfortably below what the business has
demonstrated it can do* — not as a percentage discount to a point estimate we invented.

## Management: integrity and rationality

Buffett weights two things: **honesty** and **capital-allocation rationality**. A brilliant
operator who allocates capital badly destroys value; an honest mediocre operator who returns
excess cash does not.

Assess from the record, never from impression:
- What did they do with excess cash over 10 years? (reinvest / acquire / buy back / dividend)
- What were the returns on those decisions?
- Did they issue equity at low valuations or buy back at high ones? (the classic tell)
- Do the annual letters discuss mistakes candidly, or only successes?
- Does compensation align with per-share value creation, or with size?

> **System implication:** this is what `promise-keeper` and `capital-allocation-auditor` exist
> to measure. Management quality is scored on the **historical say/do record**, never on
> narrative impression — impressions are exactly what a persuasive management team manufactures.

---

## Munger: inversion

> "All I want to know is where I'm going to die, so I'll never go there."

Do not ask "why will this work?" Ask **"what would make this fail?"** and check whether those
conditions are present or plausible.

> **System implication:** this is the mandate of `pre-mortem-agent` and `red-team`. Inversion
> is a required pass, not an optional one, and a red-team pass that finds nothing must state
> what evidence would have changed its verdict — otherwise it did not genuinely try.

## Munger: latticework of mental models

Draw on multiple disciplines rather than a single financial frame. Most relevant here:

- **Incentives** — "show me the incentive and I'll show you the outcome." Read the remuneration
  policy before the strategy section. Promoter incentives in India often diverge sharply from
  minority shareholders'.
- **Competitive destruction** — most advantages erode. The default assumption is decay; durability
  is the claim requiring evidence.
- **Scale economics** — some advantages compound with size; others invert past an optimal scale.
- **Lollapalooza** — several forces aligning produces non-linear outcomes, good and bad.

## Munger: avoid stupidity rather than seek brilliance

> "It is remarkable how much long-term advantage people like us have gotten by trying to be
> consistently not stupid, instead of trying to be very intelligent."

This is the same asymmetry as Prasad's Type I/II framing, arrived at independently. It is the
strongest cross-validation in this doctrine, and it is why the funnel is rejection-first.

## Encoded rules

1. Circle of competence is an explicit, required field. Out-of-circle → reject.
2. Moat claims require quantitative evidence or they are struck.
3. Owner earnings, not reported EPS; maintenance capex split must be derived and shown.
4. Management scored on the 10-year capital-allocation record, not impression.
5. Read incentives before strategy.
6. Inversion is a mandatory pass.
7. Assume advantages decay; durability must be argued, not assumed.
