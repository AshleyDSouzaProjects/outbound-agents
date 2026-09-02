"""Incremental sync: what is missing from the corpus, derived from the corpus.

There is deliberately NO separate state file, cursor or watermark. The manifest
already records every document and its date, so "what do we still need?" is a query
rather than a thing to keep in step. A separate cursor is one more thing that can
disagree with reality — and when it does, it does so silently.

This makes daily updates trivial and, more importantly, makes an interrupted
backfill self-healing: kill it halfway, rerun it, and it resumes from the gaps
because the gaps are computed, not remembered.
"""

from __future__ import annotations

from datetime import date, timedelta

from .store import Manifest, Paths


def ingested_trade_dates(paths: Paths, source: str) -> set[date]:
    """Trade dates already held for a daily source (bhavcopy et al.)."""
    out: set[date] = set()
    for record in Manifest(paths.manifest).load():
        if record.source != source:
            continue
        stamp = record.meta.get("trade_date")
        if stamp:
            try:
                out.add(date.fromisoformat(stamp))
            except ValueError:
                continue
        elif record.published_at:
            out.add(record.published_at)
    return out


def last_ingested(paths: Paths, source: str) -> date | None:
    dates = ingested_trade_dates(paths, source)
    return max(dates) if dates else None


def missing_trading_days(
    paths: Paths, source: str, start: date, end: date
) -> list[date]:
    """Weekdays in [start, end] not yet held.

    Exchange holidays are indistinguishable from gaps here — both are simply absent.
    They 404 on fetch and are skipped, so a holiday is retried once per run and
    costs one cheap request. Materialising a holiday calendar would be faster but
    is another thing to keep correct for 30 years; not worth it.
    """
    have = ingested_trade_dates(paths, source)
    out: list[date] = []
    day = start
    while day <= end:
        if day.weekday() < 5 and day not in have:
            out.append(day)
        day += timedelta(days=1)
    return out


def resolve_window(
    paths: Paths,
    source: str,
    start: str | None,
    end: str | None,
    default_start: date,
) -> tuple[date, date]:
    """Turn CLI arguments into a concrete window.

    `--start last` continues from the day after the newest document held, which is
    the normal mode for a scheduled daily run.
    """
    today = date.today()
    stop = date.fromisoformat(end) if end else today

    if start == "last":
        latest = last_ingested(paths, source)
        begin = (latest + timedelta(days=1)) if latest else default_start
    elif start:
        begin = date.fromisoformat(start)
    else:
        begin = default_start

    return begin, stop


def gap_report(paths: Paths, source: str, start: date, end: date) -> dict[str, object]:
    have = ingested_trade_dates(paths, source)
    missing = missing_trading_days(paths, source, start, end)
    in_window = [d for d in have if start <= d <= end]
    return {
        "source": source,
        "window": (start.isoformat(), end.isoformat()),
        "held": len(in_window),
        "missing": len(missing),
        "first_held": min(in_window).isoformat() if in_window else None,
        "last_held": max(in_window).isoformat() if in_window else None,
        # Long runs of missing days are usually a dead URL era or a rate-limit ban,
        # not a holiday. Surface the first few so it is obvious which.
        "first_missing": [d.isoformat() for d in missing[:5]],
    }
