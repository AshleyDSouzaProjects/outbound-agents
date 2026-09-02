# 30 — Kill Criteria Template

Every thesis carries pre-registered falsifiers. Written **before** the position, **immutable**
after. Rewriting or reinterpreting a kill criterion after the fact is the most damaging action
possible in this system — it converts a learning system into a rationalising one.

---

## Why pre-registration

Without it, a thesis is unfalsifiable. Every disappointing result gets absorbed:
*"margins compressed, but that's temporary"*; *"they missed guidance, but the industry is weak."*
Each individual rationalisation is plausible. Together they mean nothing can ever be wrong, and
a position is held to zero with a coherent story at every step down.

Pre-registration forces the question **while we are still honest**: what would actually change
our mind?

## Rules

1. **Specific and observable.** "Deteriorating fundamentals" is not a kill criterion.
   "ROCE below 15% for four consecutive quarters" is.
2. **Dated.** Every criterion names when it is evaluated.
3. **Falsifiable from public data.** If we cannot check it from filings, it is not a criterion.
4. **Written before the position.**
5. **Immutable.** A triggered criterion is reported as triggered. The *response* is a
   documented decision; the criterion itself is never edited.
6. **Distinguish thesis-break from price move.** A 40% drawdown is not a kill criterion —
   Indian mid-caps do that routinely. A structural break in the business is.

---

## Template

```markdown
# Kill Criteria — [COMPANY] ([TICKER])
Thesis opened: YYYY-MM-DD   |   Author: [agent/human]   |   Journal: [decision-journal ref]

## Thesis in one sentence
[What we believe that the market does not, and why the price is wrong.]

## What the price currently implies
[From expectations-analyst: implied growth, margin, capital intensity, duration.]

## The three things that must remain true
1. [e.g. ROCE stays above 20% — currently 27%, 10yr range 22–31%]
2. [e.g. Reinvestment runway supports 15%+ capital deployment for 5+ years]
3. [e.g. Promoter holding stable, zero pledge, RPT below 2% of revenue]

---

## HARD KILL — exit, no discretion
| # | Criterion | Check | Source |
|---|---|---|---|
| H1 | Promoter pledge > 10% of holding | Quarterly | Shareholding pattern |
| H2 | Auditor resigns or is changed without clear explanation | Event | Exchange filing |
| H3 | RPT > 5% of revenue, or rising 2 consecutive years | Annual | AR related-party note |
| H4 | Cash conversion (FCF/PAT) < 60% for 2 consecutive years | Annual | Cash flow statement |
| H5 | [Company-specific structural break] | | |

## SOFT KILL — review within 30 days, decision documented
| # | Criterion | Check | Source |
|---|---|---|---|
| S1 | ROCE < [X]% for 4 consecutive quarters | Quarterly | Computed |
| S2 | Market share loss > [X]pp over 2 years | Annual | Industry data |
| S3 | Key person departure (CEO/CFO) | Event | Exchange filing |
| S4 | Guidance missed 3 of last 4 times | Quarterly | Promise ledger |
| S5 | Implied expectations now exceed [X] — priced for perfection | Quarterly | expectations-analyst |

## EXPLICITLY NOT KILL CRITERIA
- Price decline of any magnitude absent a thesis break.
- One weak quarter attributable to a stated, verifiable, transient cause.
- Sector de-rating unaccompanied by company-specific deterioration.
- Analyst downgrades, media negativity, index exclusion.

---

## Pre-mortem
> It is [today + 5 years] and this position has lost 60%. What happened?

[Written at thesis open by pre-mortem-agent. The most likely failure paths, ranked, with the
early indicators that would show each one developing.]

## Base rates
| Claim the thesis requires | Base rate | Source |
|---|---|---|
| [e.g. sustaining ROCE > 25% for 5 more years] | [N%] | `memory/base-rates/...` |

**This thesis requires the company to be in the top [X]% of outcomes. Justification: [...]**

## Review log
| Date | Criteria checked | Status | Action | Notes |
|---|---|---|---|---|
| | | | | |
```

---

## Worked example (illustrative — not a recommendation)

```markdown
## The three things that must remain true
1. Gross margin holds above 50% — evidence of genuine pricing power, not mix
2. Store/distribution expansion continues at 8%+ annually with stable unit economics
3. Promoter holding stable, zero pledge

## HARD KILL
H1  Any promoter pledge appears                          → exit
H2  Gross margin < 45% for 2 consecutive quarters
    absent a disclosed one-off input-cost shock          → exit
H3  Auditor change without clear explanation             → exit

## SOFT KILL
S1  Same-store growth negative for 3 consecutive quarters
S2  New-store payback period exceeds 30 months (was 18)  ← runway is the thesis;
                                                            this is the real tell
S3  Guidance missed 3 of last 4 → promise ledger downgrade
```

Note S2: the kill criterion tracks **the thing the thesis actually depends on** (reinvestment
runway), not a generic financial metric. This is what distinguishes a real kill criterion from
a checklist item.
