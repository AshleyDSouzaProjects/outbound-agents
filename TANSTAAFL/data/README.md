# Data

```
raw/        immutable, content-hashed source documents (gitignored — index lives in memory/evidence/)
staging/    parsed but not yet normalised
curated/    normalised panels (Parquet / DuckDB) — regenerable from raw
reference/  universe definitions, ticker maps, exchange calendars
```

## Invariants

1. **`raw/` is append-only.** Never edit, never delete. Corrections are new records.
2. **Everything downstream is regenerable.** If `curated/` is lost, the pipeline rebuilds it
   from `raw/`. If `raw/` is lost, the corpus is gone — back it up.
3. **Prices must be corporate-action adjusted.** Indian names split and issue bonuses
   frequently; unadjusted series silently corrupt every downstream calculation.
4. **Point-in-time.** Every record carries its publication date, not just its period date.
   A FY24 annual report published Jul-2024 is not available on 31-Mar-2024.
5. **Ind AS transition (~FY16–17) breaks naive 10-year series.** Handle the discontinuity
   explicitly or restrict the window.

## reference/universe

The Nifty 500 constituent list **as it stood on each date** — not today's list. Using today's
constituents for historical analysis embeds survivor bias: the companies that collapsed were
removed, so a backtest on the current list cannot possibly find them. Delisted and ejected
names must be retained.
