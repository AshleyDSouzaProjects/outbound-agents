# 12 — Other Encoded Sources

Recommended additions beyond Prasad and Buffett/Munger, each earning its place by contributing
something the others do not.

---

## Chuck Akre — the three-legged stool

Akre's framing is the most operationally useful summary of quality investing:

1. **The business** — high returns on capital, durable.
2. **The management** — able, honest, shareholder-oriented.
3. **The reinvestment runway** — *can they redeploy earnings at similarly high rates?*

The third leg is **the one everybody skips**, and it is decisive. A business earning 40% ROCE
with nowhere to reinvest is a cash cow — pleasant, but its value compounds at the dividend
yield. A business earning 25% ROCE that can reinvest 80% of earnings at 25% for fifteen years
is a compounding machine worth many times more.

> **System implication:** `reinvestment-runway-analyst` is a first-class Tier-3 agent, and
> runway must be argued with **arithmetic** — store/plant expansion maths, unit economics,
> geographic or category headroom — not with TAM hand-waving. "The market is ₹50,000cr and we
> have 3%" is not a runway analysis.

## Bruce Greenwald — EPV and the valuation hierarchy

Greenwald's ordering of valuation methods by reliability, most reliable first:

1. **Asset reproduction value** — what would it cost a competitor to rebuild this business?
2. **Earnings power value (EPV)** — sustainable current earnings ÷ cost of capital, *assuming zero growth*.
3. **Growth value** — only credible when protected by a moat, and only then.

The discipline: **growth is worth something only inside a franchise.** Growth in a competitive
business with no moat destroys value, because it is reinvestment at the cost of capital.

EPV is more honest than DCF for durable businesses because it does not smuggle the answer into
a terminal value. If EPV alone justifies the price, the growth is free optionality — the most
attractive setup available.

> **System implication:** `epv-analyst` computes EPV and reproduction value *before* any growth
> is credited. Growth value requires a passed moat test as a precondition.

## Michael Mauboussin — expectations investing

The single most important methodological import. **Do not value the company — reverse-engineer
what the price already assumes, then judge whether those assumptions are plausible.**

> "The market is a forecasting machine. Your job is not to out-forecast it in general, but to
> find the specific cases where its embedded forecast is implausible."

Also from Mauboussin:
- **Base rates** — his ROIC-persistence and growth-rate studies are the empirical backbone of
  our base-rate library.
- **Skill vs luck** — outcomes in high-luck domains are terrible feedback. Judge the *process*,
  which is why the decision journal exists.
- **Expectations infrastructure** — decompose the price into the operating drivers (sales
  growth, margin, capital intensity) that would have to be true.

> **System implication:** `expectations-analyst` is the primary valuation agent. Output format
> is always *"the price implies X; the base rate for X is Y; here is why this company is or is
> not an exception."* Never a target price.

## Howard Marks — second-level thinking and cycles

- **First-level:** "It's a good company, buy it." **Second-level:** "It's a good company, but
  everyone knows that and the price assumes perfection — so it's a sell."
  *The question is never "is this a good business?" but "is it better than the price assumes?"*
- **Risk is permanent loss of capital, not volatility.** Never use beta or standard deviation
  as a risk measure in this system.
- **Cycle awareness without timing.** Know where we are in the cycle to calibrate *expectations*,
  never to time entries.

> **System implication:** risk assessment is scenario-based (what causes permanent impairment?),
> never volatility-based. And every thesis must answer: *what does the market believe that we
> think is wrong?* A thesis with no differentiated view is not a thesis.

## Terry Smith — three rules, ruthlessly applied

1. Buy good companies.
2. Don't overpay.
3. **Do nothing.**

Smith's specific contribution is the **cash-conversion** discipline: free cash flow ÷ net
income, tracked over a decade. Persistent conversion below ~80–100% means reported earnings are
not turning into cash — the single most reliable early warning of accounting aggression.

> **System implication:** cash conversion is a Tier-2 rejection metric, not a Tier-3 nicety.

## Nick Sleep — scale economics shared

Some businesses deliberately pass scale savings to customers rather than taking them as margin,
building a self-reinforcing advantage that looks like *under*-earning in the short term.
Standard screens reject these businesses precisely when they are most attractive.

Also **destination analysis**: what does this business look like at maturity, and is the current
price sensible against that end state?

> **System implication:** flag deliberate margin suppression as a *potential positive*, requiring
> human review, rather than auto-rejecting on low margins. A rare but valuable exception to the
> quality screen.

## Phil Fisher — scuttlebutt

Talk to customers, suppliers, competitors and ex-employees. Historically the highest-effort,
highest-value research activity available.

**This is the technique most transformed by agents.** Employee reviews, job postings, customer
reviews, app telemetry and shipment data are scuttlebutt at machine scale — and they are the
independent check on management claims.

> **System implication:** `scuttlebutt-agent`, Tier C sources. Used to *corroborate or
> contradict* management, never as a standalone signal.

## Joel Greenblatt — the cheap first pass

ROC + earnings yield ranking. Not a strategy for us, but an excellent **cheap prior** for
ordering the 500 before expensive analysis, and a useful sanity check: if a name ranks terribly
on both and we like it, we should be able to say precisely why.

## Kahneman & Tetlock — the meta-layer

- **Outside view first.** Base rates before the specific story.
- **Calibration.** Probabilities must be scored (Brier/log) and tracked. An unscored forecast
  is entertainment.
- **Decision journal.** Record reasoning *before* outcomes. Hindsight bias makes unrecorded
  reasoning worthless within weeks.
- **Premortem.** Assume failure has occurred; explain it.

> **System implication:** this is the entire Tier-8 learning layer, and the reason `memory/calibration/`
> and `memory/decision-journal/` exist. Without these the system accumulates data but never learns.

## Saurabh Mukherjea / Marcellus — India-specific

- **Coffee Can** — buy quality, hold 10 years untouched. An independent Indian arrival at
  Prasad's conclusion, which is meaningful corroboration.
- **Forensic screens** on Indian accounting: cash conversion, RPT intensity, auditor changes,
  contingent liabilities, provisioning behaviour, subsidiary opacity.
- The blunt observation that in India, **governance risk — not valuation risk — is what
  permanently impairs capital.**

> See `20-india-context.md`.

---

## Where these sources disagree (and what we do)

Honest tensions, resolved explicitly rather than papered over:

| Tension | Resolution |
|---|---|
| Greenblatt/Graham favour statistical cheapness; Prasad/Akre reject it | **Quality first.** Cheapness is not a reason to own a bad business. Greenblatt is used only as a cheap prior for ordering work. |
| Greenwald distrusts growth value; Akre's whole thesis is reinvestment | Growth is credited **only** after a moat test passes. Then it is the dominant term. Not contradictory — sequenced. |
| Fisher's scuttlebutt is qualitative; Prasad prefers hard historical financials | Scuttlebutt **corroborates or contradicts**; it never originates a thesis. |
| Marks emphasises cycles; Prasad's record shows timing added ~0% | Cycles calibrate *expectations*, never entry timing. |
