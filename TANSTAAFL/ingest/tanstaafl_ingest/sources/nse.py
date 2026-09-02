"""NSE India adapter.

LOCAL ONLY. NSE blocks datacenter IPs and requires a primed cookie jar, so this
will not work from a cloud sandbox even if egress is opened — the block is on
their side, not ours.

Not exercised in CI: it needs live network and a residential IP. Treat as
untested until it has run on a real machine.
"""

from __future__ import annotations

import io
import zipfile
from datetime import date, datetime
from typing import Iterator

from ..model import Document
from .base import SourceRequiresLocal, SourceUnavailable

HOST = "www.nseindia.com"
BASE = f"https://{HOST}"

# NSE rejects anything that does not look like a browser.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
}


def _session():
    try:
        import requests
    except ImportError as exc:  # pragma: no cover
        raise SourceUnavailable("pip install requests to use the nse source") from exc

    s = requests.Session()
    s.headers.update(HEADERS)
    # Cookie priming: NSE sets cookies on the homepage and rejects API calls that
    # arrive without them. This is the single most common reason NSE scrapers fail.
    try:
        s.get(BASE, timeout=15)
        s.get(f"{BASE}/market-data/securities-available-for-trading", timeout=15)
    except Exception as exc:
        raise SourceRequiresLocal("nse", HOST) from exc
    return s


class NseBhavcopySource:
    """Daily bhavcopy — the authoritative OHLCV series.

    Corporate-action adjustment is NOT applied here. Raw stays raw; adjustment is a
    normalisation concern (Tier 1), because an adjustment factor revised later must
    not silently rewrite the evidence store.
    """

    name = "nse_bhavcopy"

    def __init__(self, start: date, end: date):
        self.start = start
        self.end = end

    def fetch(self, targets: list[str] | None = None) -> Iterator[Document]:
        session = _session()
        day = self.start
        while day <= self.end:
            if day.weekday() < 5:  # skip weekends; holidays just 404
                doc = self._fetch_day(session, day)
                if doc is not None:
                    yield doc
            day = date.fromordinal(day.toordinal() + 1)

    def _fetch_day(self, session, day: date) -> Document | None:
        stamp = day.strftime("%d%m%Y")
        url = f"{BASE}/api/reports?archives=" + (
            f'[{{"name":"CM - Bhavcopy(csv)","type":"archives",'
            f'"category":"capital-market","section":"equities"}}]'
            f"&date={day.strftime('%d-%b-%Y')}&type=equities&mode=single"
        )
        try:
            resp = session.get(url, timeout=30)
        except Exception as exc:
            raise SourceRequiresLocal("nse_bhavcopy", HOST) from exc

        if resp.status_code == 404:
            return None  # holiday
        if resp.status_code != 200:
            raise SourceUnavailable(f"NSE returned {resp.status_code} for {day}")

        content = resp.content
        # Bhavcopy arrives zipped; store the CSV, not the envelope.
        if content[:2] == b"PK":
            with zipfile.ZipFile(io.BytesIO(content)) as zf:
                name = zf.namelist()[0]
                content = zf.read(name)

        return Document(
            content=content,
            doc_type="prices",
            source=self.name,
            company=None,
            published_at=day,
            url=url,
            content_type="text/csv",
            meta={"trade_date": day.isoformat(), "stamp": stamp},
        )


class NseFilingsSource:
    """Corporate announcements and filings for named tickers."""

    name = "nse_filings"

    def __init__(self, since: date):
        self.since = since

    def fetch(self, targets: list[str] | None = None) -> Iterator[Document]:
        if not targets:
            raise SourceUnavailable("nse_filings needs a list of tickers")
        session = _session()
        for symbol in targets:
            url = f"{BASE}/api/corporate-announcements?index=equities&symbol={symbol}"
            try:
                resp = session.get(url, timeout=30)
            except Exception as exc:
                raise SourceRequiresLocal("nse_filings", HOST) from exc
            if resp.status_code != 200:
                raise SourceUnavailable(f"NSE returned {resp.status_code} for {symbol}")

            for item in resp.json():
                published = _parse_dt(item.get("an_dt") or item.get("sort_date"))
                if published is None or published < self.since:
                    continue
                yield Document(
                    content=resp.content,
                    doc_type="filing",
                    source=self.name,
                    company=symbol.upper(),
                    published_at=published,
                    url=url,
                    content_type="application/json",
                    meta={"subject": item.get("desc") or item.get("subject")},
                )


def _parse_dt(value: str | None) -> date | None:
    if not value:
        return None
    for fmt in ("%d-%b-%Y %H:%M:%S", "%d-%b-%Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None
