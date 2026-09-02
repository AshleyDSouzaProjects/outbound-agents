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
from .sync import gap_report, resolve_window
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


# Earliest sensible start per source, used when neither --start nor `last` applies.
DEFAULT_START = {
    "nse_bhavcopy": date(2005, 1, 1),
    "bse_bhavcopy": date(2007, 1, 1),
    "nse_announcements": date(2015, 1, 1),
    "bse_announcements": date(2015, 1, 1),
}


def _universe(path: str | None) -> list[str] | None:
    if not path:
        return None
    return [
        ln.strip().upper()
        for ln in Path(path).read_text(encoding="utf-8").splitlines()
        if ln.strip() and not ln.startswith("#")
    ]


def cmd_fetch(args) -> int:
    paths = Paths.discover()
    store = Store(paths)
    targets = _universe(args.universe)
    name = args.source

    if name == "screener":
        from .sources.screener import ScreenerSource
        source = ScreenerSource()
        print("Fetching from screener")
        return _ingest(store, source, targets, args.dry_run)

    start, end = resolve_window(
        paths, name, args.start, args.end, DEFAULT_START.get(name, date(2015, 1, 1))
    )
    if start > end:
        print(f"nothing to do: corpus is current through {end}")
        return 0

    if name == "nse_bhavcopy":
        from .sources.bhavcopy import NseBhavcopySource
        source = NseBhavcopySource(start, end)
    elif name == "bse_bhavcopy":
        from .sources.bhavcopy import BseBhavcopySource
        source = BseBhavcopySource(start, end)
    elif name == "nse_announcements":
        from .sources.announcements import NseAnnouncementsSource
        source = NseAnnouncementsSource(start, end, with_attachments=args.attachments)
    elif name == "bse_announcements":
        from .sources.announcements import BseAnnouncementsSource
        source = BseAnnouncementsSource(start, end, with_attachments=args.attachments)
    else:
        print(f"unknown source: {name}", file=sys.stderr)
        return 2

    print(f"Fetching {name}: {start} .. {end}")
    return _ingest(store, source, targets, args.dry_run)


def cmd_gaps(args) -> int:
    """What is missing, computed from the manifest rather than a stored cursor."""
    paths = Paths.discover()
    start, end = resolve_window(
        paths, args.source, args.start, args.end,
        DEFAULT_START.get(args.source, date(2015, 1, 1)),
    )
    report = gap_report(paths, args.source, start, end)
    for key, value in report.items():
        print(f"  {key:<15} {value}")
    if report["missing"]:
        print(f"\nRun: tanstaafl-ingest fetch {args.source} "
              f"--start {report['window'][0]} --end {report['window'][1]}")
    return 0


def cmd_classify(args) -> int:
    """Category histogram over ingested announcements.

    Watch the unclassified share: a rise means exchange phrasing drifted and the
    rules in classify.py need extending.
    """
    from .classify import Severity

    reader = CorpusReader.open()
    records = reader.records(doc_type="announcement")
    if not records:
        print("no announcements ingested yet")
        return 0

    hist: dict[str, int] = {}
    vetoes: list = []
    for r in records:
        cat = r.meta.get("category", "unclassified")
        hist[cat] = hist.get(cat, 0) + 1
        if r.meta.get("severity") == Severity.VETO.value:
            vetoes.append(r)

    total = len(records)
    for cat, n in sorted(hist.items(), key=lambda kv: -kv[1]):
        print(f"  {cat:<24} {n:>7,}  {n/total:>6.1%}")
    unclassified = hist.get("unclassified", 0)
    print(f"\n  {total:,} announcements, {unclassified/total:.1%} unclassified")

    if vetoes:
        print(f"\n  {len(vetoes)} VETO-grade event(s):")
        for r in vetoes[: args.limit]:
            print(f"    {r.published_at}  {r.company or '?':<12} "
                  f"{r.meta.get('category'):<22} {r.meta.get('subject', '')[:60]}")
    return 0


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

    sources = [
        "nse_bhavcopy", "bse_bhavcopy",
        "nse_announcements", "bse_announcements",
        "screener",
    ]

    p = sub.add_parser("fetch", help="fetch from a remote source (local machine only)")
    p.add_argument("source", choices=sources)
    p.add_argument("--universe", help="file of tickers, one per line")
    p.add_argument("--start", help="ISO date, or 'last' to continue from the corpus")
    p.add_argument("--end", help="ISO date (default: today)")
    p.add_argument("--attachments", action="store_true",
                   help="also fetch attachment PDFs for analytically weighty categories")
    p.set_defaults(func=cmd_fetch)

    p = sub.add_parser("gaps", help="what is missing, computed from the manifest")
    p.add_argument("source", choices=sources)
    p.add_argument("--start", help="ISO date, or 'last'")
    p.add_argument("--end", help="ISO date")
    p.set_defaults(func=cmd_gaps)

    p = sub.add_parser("classify", help="category histogram over ingested announcements")
    p.add_argument("--limit", type=int, default=20, help="veto events to list")
    p.set_defaults(func=cmd_classify)

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
