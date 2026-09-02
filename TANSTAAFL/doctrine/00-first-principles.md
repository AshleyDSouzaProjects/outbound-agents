# 00 — First Principles

The reasoning this whole system rests on. If this document is wrong, everything else is
wasted effort.

---

## The premise

Fundamental analysis was historically **labour-gated**. The work — obtaining annual reports,
keying in ten years of financials, reconciling restatements, reading every footnote,
cross-referencing subsidiaries — took an analyst weeks per company. That labour cost was the
barrier, and the barrier was the edge. Whoever was willing to do more of it knew more.

Agents remove that barrier almost entirely.

## The trap

The naive conclusion: *"therefore agents give us an edge."*

This is backwards. **A barrier that falls for us falls for everyone.** Capability that is
cheap and general is not edge — it is table stakes, competed to zero, and already reflected
in prices. Within a few years every serious market participant will have agents reading every
filing. The analyst-weeks that used to buy an information advantage now buy nothing.

Worse, cheap analysis is *actively dangerous*: it produces enormous volumes of plausible,
well-formatted, confidently-argued output. The constraint shifts from "can we analyse this?"
to "can we tell whether this analysis is any good?" Volume without calibration is how you lose
money quickly while feeling extremely well-informed.

## Therefore: where can edge actually live?

Edge must come from something that does **not** get cheaper when compute gets cheaper.

### 1. Structural — time horizon

Most capital cannot wait. Fund managers face redemptions, quarterly reporting, career risk,
and clients who read monthly statements. This forces short horizons *regardless of what the
manager knows*. It is a constraint of the capital, not of the analysis.

An investor genuinely able to hold ten years is arbitraging a structural feature of the
industry, not an informational gap. **No amount of AI closes this**, because it was never an
information problem. This was Prasad's real edge, and this repo's own analysis of his record
supports it: entry timing contributed roughly nothing; holding for a decade contributed
everything.

*Design implication:* the system must be built to say "hold, do nothing" for years, and must
not be scored on activity.

### 2. Accumulated — longitudinal memory

Some knowledge cannot be computed, only **accrued**. What a CEO promised on a 2019 concall
and whether it happened by 2024 is not derivable from any single document, however well read.
It requires having recorded the promise at the time, in structured form, and waited.

This is genuinely new: the tedium that made it impossible at human scale is exactly what
agents remove. But — critically — **it takes calendar time that cannot be compressed.** An
agent can read ten years of filings in an hour; it cannot generate ten years of
promise-resolutions in an hour. That asymmetry is the durable moat.

*Design implication:* the promise ledger and entity graph are the highest-priority memory
structures, and their value is back-loaded. Build them early even though they pay late.

### 3. Disciplinary — base rates over narrative

Humans reliably prefer a compelling story to a boring frequency. LLMs, trained on human text,
inherit this preference — they are *narrative engines*, and will produce a persuasive bull
case for almost anything if asked.

The counter is mechanical: force the outside view before the inside view. Not because agents
are good at base rates, but because a system can be *architecturally compelled* to check them
in a way an enthusiastic human never is.

*Design implication:* base-rate checks are a required gate, not an optional agent.

### 4. Behavioural — pre-commitment

Most investing failure is behavioural, not analytical: selling winners early, holding losers,
moving goalposts, falling in love with a thesis. Agents do not feel these emotions — but they
will happily *rationalise* on behalf of an operator who does, which is arguably worse because
it launders a bad decision as analysis.

The defence is pre-registration: kill criteria written before the position and immutable after.

*Design implication:* the decision journal is append-only. Rewriting a falsifier is the most
damaging possible action in this system.

### 5. Breadth — forensic coverage

Reading every related-party note, every auditor change, every contingent liability schedule
across 500 companies × 15 years is infeasible for a person and trivial for a fleet of agents.

This is real, but it is the *weakest* of the five and it decays fastest — it is closest to
pure extraction, and competitors will have it soonest. Treat it as a two-to-three year
advantage, not a permanent one.

---

## The ranking, and what it means

| Edge | Durability | Available when? |
|---|---|---|
| Time horizon | Permanent | Immediately |
| Longitudinal memory | Very high | Year 2–3+ |
| Base-rate discipline | High | Months 6–12 |
| Behavioural pre-commitment | High | Immediately |
| Forensic breadth | **Decaying** | Months 3–6 |

The two edges available *immediately* — horizon and pre-commitment — require no technology at
all. They are choices. The technology serves the three that need building.

## What this rules out

- Sentiment analysis, news-flow scoring, "AI price prediction." All commoditised or noise.
- Market timing. Prasad's record shows it contributed ~0%; we will not rediscover it.
- Anything that needs us to beat the market on next quarter's EPS.
- Any pitch of the form "our agents read faster." If we catch ourselves saying this, we have
  lost the plot and should stop.

## The test

> If this system makes money, can we articulate *who was on the other side of the trade and
> why they were willing to be?*

If the answer is "they hadn't read the annual report," we are wrong — they had, or their
agent had. If the answer is "they could not hold for eight years," or "they did not know this
management has missed nine of its last eleven guidance commitments because nobody was keeping
score," that is a real answer.

**No such thing as a free lunch. If the lunch looks free, find the cost — or assume we are it.**
