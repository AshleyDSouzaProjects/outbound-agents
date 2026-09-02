"""tanstaafl-ingest — the local ingestion CLI.

Owns all writes to the corpus. Source adapters only yield documents; this module
decides what lands on disk, so a broken adapter cannot corrupt the evidence store.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from .corpus import CorpusReader
from .sources.base import SourceUnavailable
from .sources.drop import DropSource
from .store import Paths, Store


def _ingest(store: Store, source, targets: list[str] | None, dry_run: bool) -> int:
    counts = {"new": 0, "new-provenance": 0, "duplicate": 0}
    try:
        for doc in source.fetch(targets):
            if dry_run:
                print(f"  would ingest {doc.doc_type:20s} {doc.company or '_market':12s} "
                      f"{doc.published_at} {len(doc.content):>9,}b")
                counts["new"] += 1
                continue
            result = store.put(doc)
            counts[result.status] += 1
            print(f"  {result.status:15s} {result.record.sha256[:12]} "
                  f"{result.record.doc_type:20s} {result.record.company or '_market'}")
    except SourceUnavailable as exc:
        print(f"\nSOURCE UNAVAILABLE: {exc}", file=sys.stderr)
        return 2

    total = sum(counts.values())
    if total == 0:
        # Silently ingesting nothing is how a corpus quietly rots.
        print("\nWARNING: source yielded zero documents.", file=sys.stderr)
        return 1

    print(f"\n{total} document(s): {counts['new']} new, "
          f"{counts['new-provenance']} new provenance, {counts['duplicate']} duplicate")
    return 0


def cmd_drop(args) -> int:
    store = Store(Paths.discover())
    paths = [Path(p) for p in args.paths]
    missing = [p for p in paths if not p.exists()]
    if missing:
        print(f"no such path: {', '.join(str(m) for m in missing)}", file=sys.stderr)
        return 2
    print(f"Ingesting from {len(paths)} path(s) into {store.paths.raw}")
    return _ingest(store, DropSource(paths), None, args.dry_run)


def cmd_fetch(args) -> int:
    store = Store(Paths.discover())
    targets = None
    if args.universe:
        targets = [
            ln.strip().upper()
            for ln in Path(args.universe).read_text(encoding="utf-8").splitlines()
            if ln.strip() and not ln.startswith("#")
        ]

    if args.source == "screener":
        from .sources.screener import ScreenerSource
        source = ScreenerSource()
    elif args.source == "nse_bhavcopy":
        from .sources.nse import NseBhavcopySource
        source = NseBhavcopySource(
            start=date.fromisoformat(args.start), end=date.fromisoformat(args.end)
        )
    elif args.source == "nse_filings":
        from .sources.nse import NseFilingsSource
        source = NseFilingsSource(since=date.fromisoformat(args.start))
    else:
        print(f"unknown source: {args.source}", file=sys.stderr)
        return 2

    print(f"Fetching from {args.source}")
    return _ingest(store, source, targets, args.dry_run)


def cmd_verify(args) -> int:
    store = Store(Paths.discover())
    report = store.verify()
    print(f"checked   {report.checked} blob(s)")
    print(f"missing   {len(report.missing)}")
    print(f"corrupt   {len(report.corrupt)}")
    print(f"orphaned  {len(report.orphans)}")

    for sha in report.missing[:10]:
        print(f"  MISSING  {sha[:16]} — in manifest, not on disk (corpus not synced?)")
    for sha in report.corrupt[:10]:
        print(f"  CORRUPT  {sha[:16]} — hash mismatch; the evidence store is compromised")

    if not report.ok:
        print("\nFAIL — do not run analysis against this corpus.", file=sys.stderr)
        return 1
    print("\nOK")
    return 0


def cmd_status(args) -> int:
    as_of = date.fromisoformat(args.as_of) if args.as_of else None
    reader = CorpusReader.open(as_of=as_of)
    coverage = reader.coverage()

    if as_of:
        print(f"Corpus as of {as_of} (point-in-time)\n")
    else:
        print("Corpus (all documents)\n")

    if not coverage:
        print("  empty — nothing ingested yet")
        return 0

    doc_types = sorted({t for c in coverage.values() for t in c})
    width = max(len(c) for c in coverage) + 2
    print(f"{'company':<{width}}" + "".join(f"{t[:12]:>14}" for t in doc_types))
    for company in sorted(coverage):
        row = coverage[company]
        print(f"{company:<{width}}" + "".join(f"{row.get(t, 0):>14}" for t in doc_types))

    undated = reader.undated()
    print(f"\n{len(coverage)} companies, "
          f"{sum(sum(c.values()) for c in coverage.values())} documents")
    if undated:
        print(f"WARNING: {len(undated)} document(s) have no publication date and are "
              f"invisible to any point-in-time reader.", file=sys.stderr)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="tanstaafl-ingest",
        description="Local ingestion for the TANSTAAFL evidence corpus.",
    )
    parser.add_argument("--dry-run", action="store_true", help="show what would happen")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("drop", help="ingest local files (works with no network)")
    p.add_argument("paths", nargs="+")
    p.set_defaults(func=cmd_drop)

    p = sub.add_parser("fetch", help="fetch from a remote source (local machine only)")
    p.add_argument("source", choices=["screener", "nse_bhavcopy", "nse_filings"])
    p.add_argument("--universe", help="file of tickers, one per line")
    p.add_argument("--start", help="ISO date")
    p.add_argument("--end", help="ISO date")
    p.set_defaults(func=cmd_fetch)

    p = sub.add_parser("verify", help="re-hash every blob against the manifest")
    p.set_defaults(func=cmd_verify)

    p = sub.add_parser("status", help="coverage report")
    p.add_argument("--as-of", help="ISO date — show the corpus as it stood then")
    p.set_defaults(func=cmd_status)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
