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
tanstaafl-ingest fetch nse_bhavcopy --start 2010-01-01 --end 2026-08-31
tanstaafl-ingest fetch nse_filings --universe config/nifty500.txt --start 2024-01-01

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

## Source status

| Source | Status | Needs |
|---|---|---|
| `drop` | **Tested** — 18 unit tests | nothing |
| `screener` | **Untested** — written, never run live | `SCREENER_SESSION`, `[remote]` |
| `nse_bhavcopy` | **Untested** — written, never run live | residential IP, `[remote]` |
| `nse_filings` | **Untested** — written, never run live | residential IP, `[remote]` |

The remote adapters are honest code, not stubs — cookie priming for NSE, session handling and
expiry detection for Screener — but they have never executed against the live services, because
this environment cannot reach them. **Expect to fix them on first real run.** Start with
`--dry-run` and a two-ticker universe.

Both services may also change or restrict access; `drop` is the fallback that always works, and
the reason the system never depends on any single source being reachable.

## Tests

```bash
pip install -e '.[dev]' && pytest
```

18 tests covering the store round trip, deduplication, corruption and missing-blob detection,
the filename convention, and the point-in-time guarantees — including that a pinned reader
cannot be widened and that a stale `Record` handle cannot bypass the cutoff.
