# tanstaafl-ingest

**Runs on your machine, not in the cloud.** Ingestion needs network access, credentials and a
residential IP; analysis needs none of those. See `CONTRACT.md` for why the split exists and
what each side may assume.

```
your laptop                          anywhere (laptop, CI, cloud sandbox)
─────────────                        ──────────────────────────────────
tanstaafl-ingest fetch ──┐
tanstaafl-ingest drop  ──┤
                         ▼
                  data/raw/**        ── rsync/S3 ──▶  data/raw/**
                  manifest.jsonl     ──── git ─────▶  manifest.jsonl
                                                          │
                                                          ▼
                                                    CorpusReader
                                                   (read-only, offline)
```

## Install

```bash
cd TANSTAAFL/ingest
pip install -e .              # core is stdlib-only
pip install -e '.[remote]'    # adds `requests` for the network sources
cp .env.example .env          # then fill in credentials — never commit this
```

## Commands

```bash
# Ingest local files. Works anywhere, no network, no credentials.
tanstaafl-ingest drop ~/Downloads/annual-reports/

# Fetch from a remote source. Local machine only.
tanstaafl-ingest fetch screener --universe config/nifty500.txt
tanstaafl-ingest fetch nse_bhavcopy --start last          # daily catch-up
tanstaafl-ingest fetch nse_announcements --start last --attachments

# Re-hash every blob against the manifest. Run after any transfer.
tanstaafl-ingest verify

# Coverage, optionally as the corpus stood on a past date.
tanstaafl-ingest status
tanstaafl-ingest status --as-of 2018-09-30

# Preview without writing.
tanstaafl-ingest --dry-run drop ~/Downloads/
```

## Filename convention for `drop`

```
TICKER__doctype__YYYY-MM-DD.ext

PAGEIND__annual_report__2019-07-15.pdf
PAGEIND__shareholding__2020-03-31.csv
_market__prices__2024-03-31.csv          # market-wide data
```

`doctype` ∈ `annual_report`, `quarterly_result`, `shareholding`, `transcript`, `prices`,
`rating`, `filing`, `other`.

The date is **when the document became public**, not the period it covers. A FY2019 annual
report published in July 2019 is dated `2019-07-15`, because that is when a real investor
could first have read it.

For files you cannot rename, drop a `_meta.csv` alongside them:

```csv
filename,company,doc_type,published_at,url
scan001.pdf,PAGEIND,annual_report,2019-07-15,https://example.com/ar2019.pdf
```

**A file with no publication date is invisible to every point-in-time reader.** It is ingested,
but no analysis pinned to a date will ever see it. `status` warns when any exist.

## Reading the corpus (the analysis side)

```python
from datetime import date
from tanstaafl_ingest import CorpusReader

reader = CorpusReader.open().as_of(date(2018, 9, 30))   # pin first

for record in reader.records(company="YESBANK", doc_type="shareholding"):
    print(record.published_at, record.sha256[:12])
    data = reader.read(record)
```

The pinned reader cannot see anything published after 2018-09-30, cannot be widened, and
re-checks on `read()` — so a `Record` obtained elsewhere cannot be used to smuggle a future
document past the cutoff.

## Moving the corpus

Manifest travels by git (small, text, reviewable). Blobs travel out of band (large, binary,
gitignored):

```bash
rsync -av --ignore-existing TANSTAAFL/data/raw/  remote:/path/TANSTAAFL/data/raw/
tanstaafl-ingest verify
```

If the manifest is present but blobs are not, `reader.read()` fails with a message saying the
corpus was not synced, rather than a bare missing-file error.

## Staying current

**There is no cursor or state file.** The manifest already records every document and its
date, so "what do we still need?" is a query, not a thing to keep in step. Two consequences:

- A daily update is `--start last`, which resumes from the day after the newest document held.
- An interrupted backfill is **self-healing** — kill it halfway, rerun it, and it resumes from
  the computed gaps.

```bash
tanstaafl-ingest gaps  nse_bhavcopy --start 2005-01-01   # what's missing
tanstaafl-ingest fetch nse_bhavcopy --start last         # catch up to today
```

Schedule it (cron, weekdays after the ~19:00 IST publication):

```cron
30 20 * * 1-5  cd ~/tanstaafl/TANSTAAFL/ingest && \
               tanstaafl-ingest fetch nse_bhavcopy --start last >> ~/logs/bhav.log 2>&1
0  21 * * 1-5  cd ~/tanstaafl/TANSTAAFL/ingest && \
               tanstaafl-ingest fetch nse_announcements --start last --attachments >> ~/logs/ann.log 2>&1
```

On macOS use a `launchd` plist instead — it runs missed jobs after a wake, which cron does not.
Either way a run against a current corpus is a no-op, so over-scheduling is harmless.

## Backfilling 20 years

Do it in slices, not one run — a 5,000-day sweep from one IP invites a temporary ban:

```bash
for y in $(seq 2005 2026); do
  tanstaafl-ingest fetch nse_bhavcopy --start $y-01-01 --end $y-12-31
  sleep 300
done
tanstaafl-ingest gaps nse_bhavcopy --start 2005-01-01   # confirm, then re-run for stragglers
```

Long runs of missing days mean a dead URL era or a rate-limit ban, not holidays — `gaps` shows
the first few so you can tell which.

## Announcement classification

Every announcement is classified on ingest by `classify.py` — **deterministic rules, not an
LLM**, because a backtest must give identical answers on every rerun, ~375k announcements is a
one-cent problem with regexes, and every classification cites the exact substring that matched.

```bash
tanstaafl-ingest classify        # category histogram + veto-grade events
```

Five categories carry `VETO` severity and feed `governance-sentinel`'s hard-reject authority:
`auditor_resignation`, `auditor_qualification`, `pledge_invocation`, `insolvency`, `default`.

**Watch the unclassified share.** A rise means exchange phrasing drifted and the rules need
extending. Precision is deliberately favoured over recall: an untagged announcement is caught
by the annual full-text pass, whereas a mis-tagged auditor resignation silently defeats the
highest-value governance filter in the system.

## Source status

| Source | Status | Needs |
|---|---|---|
| `drop` | **Tested** — offline | nothing |
| `classify` | **Tested** — 37 unit tests | nothing |
| sync / gap logic | **Tested** — 17 unit tests incl. URL eras | nothing |
| `nse_bhavcopy` | URL construction tested; **never run live** | residential IP, `[remote]` |
| `bse_bhavcopy` | as above | residential IP, `[remote]` |
| `nse_announcements` | classification tested; **fetch never run live** | residential IP, `[remote]` |
| `bse_announcements` | as above | residential IP, `[remote]` |
| `screener` | **Untested** — written, never run live | `SCREENER_SESSION`, `[remote]` |

The remote adapters are honest code, not stubs — NSE cookie priming, both URL eras, date-window
chunking, BSE pagination, rate limiting — but none has executed against the live services,
because this environment cannot reach them. **Expect to fix them on first real run.** Start with
`--dry-run` and a one-week window.

Exchanges change formats without notice (NSE did exactly that in July 2024); `drop` is the
fallback that always works, and the reason the system never depends on one source being reachable.

## Tests

```bash
pip install -e '.[dev]' && pytest
```

18 tests covering the store round trip, deduplication, corruption and missing-blob detection,
the filename convention, and the point-in-time guarantees — including that a pinned reader
cannot be widened and that a stale `Record` handle cannot bypass the cutoff.
