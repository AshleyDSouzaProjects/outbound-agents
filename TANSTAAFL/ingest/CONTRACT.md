# The Ingestion Contract

The boundary between the **write side** (local, networked, credentialed) and the
**read side** (portable, offline, no secrets).

Everything above this boundary — every screen, filter, valuation and thesis — depends on
exactly one guarantee: *the corpus is a faithful, immutable, timestamped record of what was
public when.* This document states what ingestion promises and what analysis may assume.

---

## Why the split exists

Ingestion and analysis have opposite requirements, and forcing them into one process makes
both worse:

| | Ingestion | Analysis |
|---|---|---|
| Network | Required | **None** |
| Credentials | Required | **None** |
| IP reputation | Matters (NSE blocks datacentre IPs) | Irrelevant |
| Reproducibility | Impossible — the web changes | **Required** |
| Where it runs | Your machine, stable identity | Anywhere: laptop, CI, cloud sandbox |
| Failure mode | Transient, retryable | Must be deterministic |

The immediate trigger was practical: this project's cloud sandbox blocks every market-data
host at the proxy's `CONNECT` (403), so ingestion cannot run there. But the split is correct
independently. **Analysis that can reach the network is analysis that cannot be reproduced** —
rerun it a month later and the inputs have moved. Cutting the network off from the analysis
tiers is what makes a backtest mean anything.

---

## What ingestion guarantees

1. **Immutability.** A blob, once written, is never modified or deleted. Corrections arrive as
   new documents; the old one stays and stays visible to any reader pinned before the correction.
2. **Content addressing.** Every document is stored under the SHA-256 of its bytes. Identical
   content is stored once.
3. **Provenance.** Every document carries its source adapter, URL, retrieval time and — where
   obtainable — its publication date.
4. **Append-only manifest.** `memory/evidence/manifest.jsonl` is the index. One JSON object per
   line, never rewritten.
5. **Verifiability.** `tanstaafl-ingest verify` re-hashes every blob against the manifest.
   Any mismatch fails loudly and blocks analysis.
6. **Raw stays raw.** No cleaning, no adjustment, no normalisation. Corporate-action adjustment,
   restatement handling and Ind AS reconciliation are Tier-1 concerns operating on a *copy*.
   An adjustment factor revised next year must never silently rewrite the evidence.

## What analysis may assume

- The corpus is a faithful record of the source bytes.
- `published_at`, where present, is when the document entered the public record.
- A `CorpusReader` pinned with `as_of` **cannot** return anything published later.
- Nothing it reads has been altered since ingestion.

## What analysis may NOT do

- Reach the network. Not for a "quick check", not for a price quote.
- Write to `data/raw/` or the manifest.
- Assume coverage. Thin coverage is normal and is itself a finding — a filter that rejects on
  an *absent* related-party note is doing something quite different from one that rejects on an
  *adverse* one, and the two must never be conflated.

---

## The interface

Exactly one import crosses the boundary:

```python
from tanstaafl_ingest import CorpusReader

reader = CorpusReader.open().as_of(date(2018, 9, 30))   # pin before anything else
for record in reader.records(company="YESBANK", doc_type="shareholding"):
    data = reader.read(record)      # raises if published after the cutoff
```

`CorpusReader` is stdlib-only and read-only. It has no network code to disable and no
credentials to leak.

### The point-in-time guarantee, enforced in one place

`CLAUDE.md` §1 makes lookahead the cardinal sin. Instructions alone do not enforce it, so the
reader does:

- A pinned reader hides anything published after its cutoff.
- **Undated documents are hidden from any pinned reader.** Unknown provenance is not a licence
  to assume availability.
- `as_of()` only ever narrows. A pinned reader cannot be widened.
- `read()` re-checks the record, so holding a `Record` obtained from an unpinned reader cannot
  smuggle a future document past the cutoff.

The one thing code cannot prevent is an agent using its *pretrained* knowledge of what happened
next. That is what `blowup-eval-harness`'s blinding and contamination-gap measurement exist for.

---

## Moving the corpus between machines

Two artefacts, deliberately handled differently:

| Artefact | Size | Travels by |
|---|---|---|
| `memory/evidence/manifest.jsonl` | KB–MB, text | **git** — committed, diffable, reviewable |
| `data/raw/**` | GB, binary | **out of band** — rsync, S3, external disk. Gitignored. |

So a collaborator (or a cloud session) can always see *what the corpus contains* from the
committed manifest, even without the bytes. `reader.read()` on an unsynced blob fails with a
message naming the cause rather than a bare `FileNotFoundError`.

To sync:

```bash
rsync -av --ignore-existing ~/tanstaafl/TANSTAAFL/data/raw/  remote:/path/TANSTAAFL/data/raw/
tanstaafl-ingest verify        # always verify after transfer
```

`--ignore-existing` is safe precisely because content addressing means a given path always
holds the same bytes.

---

## Adding a source

Implement the `Source` protocol — a generator of `Document`s that writes nothing:

```python
class MySource:
    name = "my_source"
    def fetch(self, targets=None) -> Iterator[Document]: ...
```

Rules:

1. **Never write.** The CLI owns all writes, so a broken adapter cannot corrupt the corpus.
2. **Set `published_at`** whenever it can be determined. A document without it is invisible to
   every point-in-time reader — technically ingested, practically useless.
3. **Raise `SourceUnavailable`** for network, credential or upstream failures. Never return an
   empty iterator to signal failure: silently ingesting nothing is how a corpus rots unnoticed.
4. **Store the payload, not the envelope.** Unzip, but do not parse.
5. **Rate-limit deliberately.** Be a good citizen of someone else's servers.
