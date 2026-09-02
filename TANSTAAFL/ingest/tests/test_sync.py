"""Incremental sync: gaps are computed from the manifest, never remembered."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from tanstaafl_ingest.model import Document
from tanstaafl_ingest.sources.bhavcopy import UDIFF_CUTOVER, nse_url, trading_days
from tanstaafl_ingest.store import Paths, Store
from tanstaafl_ingest.sync import (
    gap_report,
    last_ingested,
    missing_trading_days,
    resolve_window,
)


@pytest.fixture
def paths(tmp_path: Path) -> Paths:
    (tmp_path / "doctrine").mkdir()
    (tmp_path / "memory" / "evidence").mkdir(parents=True)
    (tmp_path / "data" / "raw").mkdir(parents=True)
    return Paths(root=tmp_path)


def ingest_day(store: Store, day: date, source="nse_bhavcopy") -> None:
    store.put(Document(
        content=f"prices for {day}".encode(),
        doc_type="prices",
        source=source,
        company=None,
        published_at=day,
        meta={"trade_date": day.isoformat()},
    ))


# ---- URL eras -------------------------------------------------------------

def test_legacy_url_before_cutover():
    url = nse_url(date(2019, 7, 15))
    assert "content/historical/EQUITIES/2019/JUL/cm15JUL2019bhav.csv.zip" in url


def test_udiff_url_on_and_after_cutover():
    assert "BhavCopy_NSE_CM_0_0_0_20240708_F_0000.csv.zip" in nse_url(UDIFF_CUTOVER)
    assert "BhavCopy_NSE_CM_0_0_0_20260901_F_0000.csv.zip" in nse_url(date(2026, 9, 1))


def test_day_before_cutover_still_legacy():
    """Off-by-one here silently loses or corrupts a day at the boundary."""
    assert "historical" in nse_url(date(2024, 7, 5))
    assert "BhavCopy_NSE" in nse_url(date(2024, 7, 8))


def test_trading_days_excludes_weekends():
    days = list(trading_days(date(2024, 7, 1), date(2024, 7, 7)))  # Mon..Sun
    assert len(days) == 5
    assert all(d.weekday() < 5 for d in days)


# ---- gap computation ------------------------------------------------------

def test_missing_excludes_what_is_held(paths: Paths):
    store = Store(paths)
    for day in (date(2024, 7, 1), date(2024, 7, 2)):
        ingest_day(store, day)

    missing = missing_trading_days(paths, "nse_bhavcopy", date(2024, 7, 1), date(2024, 7, 5))
    assert missing == [date(2024, 7, 3), date(2024, 7, 4), date(2024, 7, 5)]


def test_missing_is_per_source(paths: Paths):
    store = Store(paths)
    ingest_day(store, date(2024, 7, 1), source="nse_bhavcopy")
    assert date(2024, 7, 1) not in missing_trading_days(
        paths, "nse_bhavcopy", date(2024, 7, 1), date(2024, 7, 1))
    assert date(2024, 7, 1) in missing_trading_days(
        paths, "bse_bhavcopy", date(2024, 7, 1), date(2024, 7, 1))


def test_interrupted_backfill_is_self_healing(paths: Paths):
    """Kill a backfill halfway, rerun, and it resumes from the computed gaps."""
    store = Store(paths)
    window = list(trading_days(date(2024, 7, 1), date(2024, 7, 19)))
    for day in window[:5]:
        ingest_day(store, day)

    still_needed = missing_trading_days(paths, "nse_bhavcopy", window[0], window[-1])
    assert still_needed == window[5:]

    for day in still_needed:
        ingest_day(store, day)
    assert missing_trading_days(paths, "nse_bhavcopy", window[0], window[-1]) == []


# ---- window resolution ----------------------------------------------------

def test_start_last_continues_from_day_after_newest(paths: Paths):
    store = Store(paths)
    ingest_day(store, date(2024, 7, 10))
    start, end = resolve_window(paths, "nse_bhavcopy", "last", "2024-07-20", date(2005, 1, 1))
    assert start == date(2024, 7, 11)
    assert end == date(2024, 7, 20)


def test_start_last_on_empty_corpus_uses_default(paths: Paths):
    start, _ = resolve_window(paths, "nse_bhavcopy", "last", "2024-07-20", date(2005, 1, 1))
    assert start == date(2005, 1, 1)


def test_explicit_start_overrides(paths: Paths):
    store = Store(paths)
    ingest_day(store, date(2024, 7, 10))
    start, _ = resolve_window(paths, "nse_bhavcopy", "2020-01-01", None, date(2005, 1, 1))
    assert start == date(2020, 1, 1)


def test_up_to_date_corpus_yields_empty_window(paths: Paths):
    """A daily cron on a current corpus must be a no-op, not a re-fetch."""
    store = Store(paths)
    ingest_day(store, date(2024, 7, 20))
    start, end = resolve_window(paths, "nse_bhavcopy", "last", "2024-07-20", date(2005, 1, 1))
    assert start > end


def test_last_ingested(paths: Paths):
    store = Store(paths)
    assert last_ingested(paths, "nse_bhavcopy") is None
    for day in (date(2024, 7, 1), date(2024, 7, 9), date(2024, 7, 5)):
        ingest_day(store, day)
    assert last_ingested(paths, "nse_bhavcopy") == date(2024, 7, 9)


def test_gap_report_shape(paths: Paths):
    store = Store(paths)
    ingest_day(store, date(2024, 7, 1))
    report = gap_report(paths, "nse_bhavcopy", date(2024, 7, 1), date(2024, 7, 5))
    assert report["held"] == 1
    assert report["missing"] == 4
    assert report["first_held"] == "2024-07-01"
    assert report["first_missing"][0] == "2024-07-02"
