# Handover — state as of 2026-09-02

Checkpoint for starting a clean session. Read this, then `PLAN.md`.

---

## Where things stand

TANSTAAFL is **designed and scaffolded, with a working ingestion layer and no data yet.**
Doctrine, agent specs, and the corpus plumbing are built and tested. Nothing has been
ingested at scale, no analysis has run, and no recommendation has ever been produced.

The one thing that changed today: **network egress now works**, verified against live NSE.

---

## Environment — read this first

| | |
|---|---|
| `Tanstaafl` | `env_01PuYMcn6jyNoyqNKqKbPL17` — **Full** network access ✅ |
| `Default` | `env_01HMKHmVyAnbDK7zuZNr9uGN` — Trusted; NSE/BSE blocked |

**Start sessions in `Tanstaafl`** (the cloud pill above the composer at claude.ai/code).
Network policy is minted when a session's container is provisioned and cannot change during
the session's life — so a session started in `Default` can never reach NSE, no matter what
the environment list says now.

---

## Verified live, 2026-09-02

Raw evidence in `EGRESS-TEST.txt` (run from a session in the `Tanstaafl` environment).

| Check | Result |
|---|---|
| NSE bhavcopy download | ✅ **HTTP 200, valid zips** — 3 consecutive days, ~202 KB each |
| Bhavcopy content | ✅ **3,613 rows** for 2026-08-28, correct UDiFF schema |
| `nse_url()` construction | ✅ Correct — the exact filename our code builds returned 200 |
| NSE cookie priming | ✅ Works |
| NSE announcements API | ✅ **HTTP 200, 1.76 MB** for a 3-day window |
| NSE announcement field names | ✅ `an_dt`, `desc`, `attchmntFile`, `attchmntText` — match our parser |
| eodhd.com | ✅ 200 — the commercial-API path is open |
| **BSE announcements API** | ❌ **HTTP 200 but empty `{}` (2 bytes)** |

Two things this settles:

1. **NSE does not block Anthropic's egress IPs.** I had flagged datacentre-IP blocking as a
   likely wall; on this evidence it isn't one for NSE. Do not treat that caveat as live.
2. **The bhavcopy adapter's URL construction is correct against the live service** — the
   part most likely to be wrong after NSE's July-2024 UDiFF change.

---

## Known broken

**`BseAnnouncementsSource` returns an empty result.** `api.bseindia.com` answers 200 but the
body is `{}`. The URL parameters in `sources/announcements.py` are wrong, or the endpoint now
needs different headers/params. **Fix this before trusting any BSE coverage** — and note the
adapter currently treats an empty `Table` as "no more pages" and stops silently, which is
exactly the corpus-rots-unnoticed failure the CLI's zero-document warning exists to catch.

NSE announcements is unaffected and is the more important of the two.

---

## What's built

```
TANSTAAFL/
├── PLAN.md              sources, 9-layer memory, agent funnel, 12-24mo roadmap
├── CLAUDE.md            operating rules — point-in-time is the cardinal one
├── doctrine/            Prasad, Buffett/Munger, others, India context, kill criteria
├── agents/              specs by tier; full specs for the 5 differentiated agents
├── ingest/              WORKING CODE — 68 tests passing
│   ├── CONTRACT.md      the write/read boundary
│   ├── bootstrap.sh     first-run backfill, year-sliced
│   └── tanstaafl_ingest/
│       ├── store.py     content-addressed immutable store + append-only manifest
│       ├── corpus.py    CorpusReader — enforces point-in-time IN CODE
│       ├── classify.py  deterministic announcement classifier (37 tests)
│       ├── sync.py      gaps computed from the manifest, no cursor
│       └── sources/     drop, bhavcopy (both URL eras), announcements, screener
└── EGRESS-TEST.txt      raw evidence from the live run
```

Run tests: `cd TANSTAAFL/ingest && pytest` → 68 pass.

---

## Decisions already made — don't relitigate

- **Edge is not extraction.** If an agent can do it in one pass over filings, it is in the
  price. Edge is time horizon, longitudinal say/do memory, base-rate discipline, behavioural
  pre-commitment, forensic breadth. (`doctrine/00-first-principles.md`)
- **No market timing.** Our own analysis found timing contributed ~0% to Nalanda's record —
  their celebrated Oct-2008 Page entry at ₹450 was 25% *dearer* than the Mar-2007 IPO at ₹360.
- **Do not tune on 2010–2020.** ~38% of Page's 51x was multiple re-rating (P/E ~14x → ~65x).
  That lever is spent and now runs in reverse.
- **Classification is rules, not an LLM.** Reproducibility on rerun is non-negotiable for
  point-in-time work.
- **Rejection-first funnel.** When in doubt, reject and log.
- **No target prices.** Valuation states what the price implies vs base rates.

---

## Next actions, in order

1. **Fix `BseAnnouncementsSource`** (returns `{}`). Small, concrete, blocks BSE coverage.
2. **Ingest a real slice** — one year of NSE bhavcopy plus announcements — and run
   `tanstaafl-ingest classify` over live announcements. First real check of whether the
   classifier's precision holds outside hand-written test strings. Expect the unclassified
   share to be higher than the demo suggested.
3. **`rerating-researcher`** — the study that decides whether the strategy is viable at all.
   Needs prices (now obtainable) + earnings. Start with the Page reconstruction test:
   ~11.3x earnings, ~4.6x multiple, 2008→2019, ±10%.
4. **`blowup-eval-harness`** — build the matched-control set *before* running anything, or
   the result proves nothing.

---

## The open question: where does the corpus live?

Egress now works in the cloud, but **`data/raw/` is gitignored and cloud containers are
ephemeral.** A backfill run in a cloud session evaporates when the container is reclaimed.

Three options, undecided:

- **Local** (`bootstrap.sh` on the operator's machine) — what `CONTRACT.md` assumes. No
  persistence problem, no allowlist dependency.
- **Cloud + S3** — works, but is infrastructure to build and maintain.
- **Cloud + commit a small universe** — viable for a 20–30 company slice to get the
  re-rating study moving; not viable for 500 companies × 20 years of blobs.

Recommendation: **option 3 for the next milestone, option 1 for the real corpus.** Enough
data to run and validate the re-rating decomposition is a few hundred MB, and getting that
study answered matters more than corpus completeness.

Whatever is chosen, `CorpusReader` is unaffected — analysis reads the same way regardless of
where ingestion ran.
