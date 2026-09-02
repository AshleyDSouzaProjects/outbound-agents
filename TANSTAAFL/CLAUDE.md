# TANSTAAFL — Operating Rules for Agents

Rules for any agent or session working inside `TANSTAAFL/`. These override general
helpfulness instincts. Read `PLAN.md` before doing substantive work here.

---

## 0. Analysis runs offline

**No agent above Tier 1 may touch the network.** Not for a price quote, not for a "quick
check". The corpus is the only input.

Ingestion is a separate program that runs on the operator's machine (`ingest/`, and
`ingest/CONTRACT.md` for the boundary). Analysis reads through exactly one import:

```python
from tanstaafl_ingest import CorpusReader
reader = CorpusReader.open().as_of(decision_date)   # pin before anything else
```

This is not a sandbox limitation, it is the point: **analysis that can reach the network cannot
be reproduced.** Rerun it next month and the inputs have moved, and every backtest built on it
is worthless.

## 1. Point-in-time integrity — the cardinal rule

**No agent may use information published after the decision date it is reasoning about.**

A pinned `CorpusReader` enforces most of this mechanically: it hides later documents, hides
undated ones, cannot be widened, and re-checks on `read()`. Use it rather than filtering by
hand — a rule enforced in one place is a rule that actually holds.

When analysing a historical decision or running a backtest, every input must carry a
publication timestamp, and anything later than the as-of date is invisible. This includes:

- Financials from periods not yet reported (a FY24 annual report published Jul-2024 is **not**
  available on 31-Mar-2024).
- Restated figures — use what was *originally* reported at the time, not the later restatement.
- Index constituent lists (today's Nifty 500 is survivor-biased; use the list as it stood).
- Your own pretrained knowledge of what happened next. **This is the hardest one.** If you
  know Yes Bank collapsed, you cannot use that when evaluating Yes Bank as of 2017 — you must
  reason only from what the 2017 filings showed.

Violating this produces backtests that flatter us and teach us nothing. If you cannot
establish an input's publication date, treat it as unavailable and say so.

## 2. Provenance or it did not happen

Every quantitative claim entering a dossier, screen or thesis must carry a pointer to its
source: document ID (L1 hash), page, and line or table reference.

- A number you recall, inferred, or estimated is **not a fact**. Label it `ESTIMATE` with the
  derivation, or omit it.
- Never silently interpolate a missing year. Mark it missing.
- If sources conflict, record both and flag the conflict. Do not quietly pick one.

## 3. Rejection is cheap; acceptance is expensive

Prasad's asymmetry, made operational. When in doubt, **reject**. A rejected company costs us
an opportunity we never had. An accepted bad company costs us capital we cannot recover.

- Reject with **written reasons**, into the reject log. Never drop a name silently.
- Rejects are revisited annually, not permanently blacklisted.
- Do not soften a reject because the business sounds exciting. Excitement is not evidence.

## 4. Base rates before narrative

Before accepting any forward-looking claim, state the relevant base rate and the source of it.

> Bad: "This company can sustain 25% ROCE given its brand strength."
> Good: "Sustaining ROCE > 25% for five more years has a base rate of ~N% in our corpus
> (`memory/base-rates/roce-persistence.md`). This thesis requires the company to be in that
> minority. The specific reasons to believe it is: [evidence]."

If a base rate does not exist yet, say so explicitly rather than substituting confidence.

## 5. Valuation states what the price implies, never what the price should be

Use the expectations frame (Mauboussin). We do **not** produce target prices.

> Bad: "Our DCF gives a fair value of ₹1,450, so there is 32% upside."
> Good: "At ₹1,100 the market implies ~14% revenue CAGR and stable 18% EBIT margins for a
> decade. Only ~X% of Indian companies of this size have delivered that. The implied
> expectations look [too high / too low] because [evidence]."

DCF terminal values smuggle the conclusion into the assumptions. Prefer EPV, reverse DCF and
scenario distributions.

## 6. Separation of powers

An agent that builds a thesis may not evaluate it. Red-team agents are rewarded for killing
theses, and a red-team pass that finds nothing must state what evidence would have changed
its mind — otherwise it did not actually try.

## 7. Kill criteria are written first and are immutable

Every thesis must carry pre-registered falsifiers: specific, observable, dated conditions that
would end the position. If a kill criterion triggers, that is reported as triggered.
**Rewriting or reinterpreting a kill criterion after the fact is the single most damaging thing
an agent can do in this system** — it converts a learning system into a rationalising one.

## 8. "No action" is the expected output

Prasad: *don't be lazy — be very lazy.* Most runs should conclude that nothing needs doing.
Do not manufacture activity, do not surface marginal ideas to appear productive, and never
lower a threshold to produce a candidate.

## 9. Report uncertainty honestly

State confidence as a calibrated probability where possible, and name what would change your
mind. Distinguish clearly between: sourced fact / our estimate / management's claim / our
inference. Never present a management claim as a fact — the promise ledger exists precisely
because management claims have a measurable failure rate.

## 10. Data hygiene

- `data/raw/` is **append-only and immutable.** Never edit or delete. Corrections are new
  records. Only `ingest/` writes here; analysis has read access and nothing more.
- **Run `tanstaafl-ingest verify` after any corpus transfer.** Silent corruption in an immutable
  evidence store invalidates everything above it, and it is cheap to rule out.
- A manifest entry with no blob on disk means **the corpus was not synced**, not that the
  document does not exist. Blobs travel out of band; the manifest travels by git.
- Credentials live in `config/` and are **never committed**. No API key, token or password in
  any file that git tracks.
- Prices must be corporate-action adjusted. Indian names have frequent splits and bonuses;
  unadjusted series silently corrupt every downstream calculation.
- Ind AS transition (~FY16–17) breaks naive 10-year series. Handle the discontinuity explicitly
  or restrict the window.

## 11. Scope discipline

This tree is a research system, not a trading system. It does not place orders, does not
connect to a broker, and does not size real positions autonomously. It produces documented
hypotheses for a human to act on.
