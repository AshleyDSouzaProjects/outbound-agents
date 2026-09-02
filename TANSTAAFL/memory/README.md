# Memory

**The memory design is the system.** Agents are replaceable — swap a model, rewrite a prompt,
and the agent layer is rebuilt in a weekend. The accumulated, structured, provenance-tracked
memory here cannot be rebuilt at any speed, because it requires calendar time to accrue.

That asymmetry is the moat (`../doctrine/00-first-principles.md`).

## Layers

| Dir | Layer | What it holds | Value accrues |
|---|---|---|---|
| `evidence/` | L1 | Immutable provenance index over `data/raw/` | Immediately |
| `graph/` | L3 | Entities + time-valid edges: companies, promoters, directors, auditors, subsidiaries, RPT counterparties | Year 1+ |
| `dossiers/` | L4 | Living per-company theses, git-versioned | Year 1+ |
| `promise-ledger/` | L5 ★ | Management say → do, resolved over time | **Year 2–3+** |
| `decision-journal/` | L6 ★ | Every call with pre-registered falsifiers | Year 2+ |
| `base-rates/` | L7 | Empirical outside-view distributions from our own corpus | Year 1–2 |
| `calibration/` | L8 | Forecast vs outcome scoring | Year 2+ |

L2 (normalised financial panels) lives in `../data/curated/` — it is data, not memory.

## Why git-versioned markdown for dossiers

The **diff history is itself memory.** We can see exactly what we believed about a company in
2026, when that changed, and what evidence changed it. A database row that gets updated in
place destroys precisely the information a learning system needs.

## The two ★ layers

`promise-ledger/` and `decision-journal/` are the ones that make this system different from a
well-organised screener.

- The **promise ledger** answers *"does this management do what it says?"* with a record rather
  than an impression. It requires having recorded claims at the time and waiting.
- The **decision journal** answers *"is our process any good?"* It must be **append-only**.
  A system that can revise its stated reasoning after seeing the outcome learns nothing and
  will narrate its own luck back to itself as skill.

## Invariants

1. `evidence/` is append-only. Corrections are new records, never edits.
2. Every fact carries a source pointer: document hash, page, line.
3. Every entry carries the date it was written, not just the date it describes.
4. Nothing here is ever deleted. Superseded entries are marked superseded.
5. `decision-journal/` entries are immutable after the outcome is known.
