"""NSE/BSE bhavcopy — daily end-of-day snapshots of every traded security.

WHY THIS MATTERS MORE THAN PRICES
---------------------------------
Each bhavcopy is a point-in-time snapshot of everything that traded that day, so
companies that later delisted are simply present in the historical files. That
satisfies `rerating-researcher`'s hard rule #2 (include delisted and ejected names)
for free. No "current Nifty 500 constituents" feed can give you this at any price —
they have already removed the failures, which is precisely the survivor bias that
would make the study conclude multiples mostly go up.

THE CUTOVER
-----------
NSE discontinued the legacy bhavcopy on 2024-07-08 (Circular 62424) in favour of
UDiFF. Any tool written before mid-2024 fetches only dead URLs; any tool written
after it usually handles only the new ones. We need both eras, so we implement both.
"""

from __future__ import annotations

import io
import zipfile
from datetime import date, timedelta
from typing import Iterator

from ..model import Document
from .base import SourceRequiresLocal, SourceUnavailable

ARCHIVES = "https://nsearchives.nseindia.com"
NSE_HOST = "nsearchives.nseindia.com"
BSE_HOST = "www.bseindia.com"

# NSE retired the legacy format on this date; UDiFF ran in parallel from 2024-06-21.
UDIFF_CUTOVER = date(2024, 7, 8)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/all-reports",
}


def _session(prime: bool = True):
    try:
        import requests
    except ImportError as exc:  # pragma: no cover
        raise SourceUnavailable("pip install '.[remote]' for network sources") from exc

    s = requests.Session()
    s.headers.update(HEADERS)
    if prime:
        # NSE rejects requests arriving without cookies set by the main site.
        try:
            s.get("https://www.nseindia.com", timeout=15)
        except Exception as exc:
            raise SourceRequiresLocal("bhavcopy", NSE_HOST) from exc
    return s


def nse_url(day: date) -> str:
    """Return the correct URL for whichever era `day` falls in.

    The legacy path needs an uppercase month directory and a DDMMMYYYY stamp, so
    build the pieces explicitly rather than case-folding the whole URL.
    """
    if day >= UDIFF_CUTOVER:
        return f"{ARCHIVES}/content/cm/BhavCopy_NSE_CM_0_0_0_{day:%Y%m%d}_F_0000.csv.zip"
    mon = f"{day:%b}".upper()
    stamp = f"{day:%d%b%Y}".upper()
    return f"{ARCHIVES}/content/historical/EQUITIES/{day:%Y}/{mon}/cm{stamp}bhav.csv.zip"


def _unzip(content: bytes) -> bytes:
    """Store the CSV, not the envelope. Raw stays raw otherwise."""
    if content[:2] != b"PK":
        return content
    with zipfile.ZipFile(io.BytesIO(content)) as zf:
        names = [n for n in zf.namelist() if not n.endswith("/")]
        if not names:
            raise SourceUnavailable("bhavcopy zip was empty")
        return zf.read(names[0])


def trading_days(start: date, end: date) -> Iterator[date]:
    """Weekdays only. Exchange holidays simply 404 and are skipped."""
    day = start
    while day <= end:
        if day.weekday() < 5:
            yield day
        day += timedelta(days=1)


class NseBhavcopySource:
    """Daily NSE equity bhavcopy across both URL eras.

    Prices are stored UNADJUSTED. Corporate-action adjustment is a Tier-1
    normalisation concern operating on a copy — an adjustment factor revised later
    must never silently rewrite the evidence store (see ../CONTRACT.md).
    """

    name = "nse_bhavcopy"

    def __init__(self, start: date, end: date, polite_delay: float = 0.4):
        self.start = start
        self.end = end
        self.delay = polite_delay

    def fetch(self, targets: list[str] | None = None) -> Iterator[Document]:
        import time

        session = _session()
        holidays = 0
        for day in trading_days(self.start, self.end):
            time.sleep(self.delay)
            url = nse_url(day)
            try:
                resp = session.get(url, timeout=45)
            except Exception as exc:
                raise SourceRequiresLocal("nse_bhavcopy", NSE_HOST) from exc

            if resp.status_code == 404:
                holidays += 1
                continue
            if resp.status_code != 200:
                raise SourceUnavailable(
                    f"NSE returned {resp.status_code} for {day} ({url}). "
                    "A sustained non-404 usually means the IP is rate-limited."
                )

            yield Document(
                content=_unzip(resp.content),
                doc_type="prices",
                source=self.name,
                company=None,          # market-wide: one file, every security
                published_at=day,
                url=url,
                content_type="text/csv",
                meta={
                    "trade_date": day.isoformat(),
                    "exchange": "NSE",
                    "format": "udiff" if day >= UDIFF_CUTOVER else "legacy",
                    "adjusted": False,
                },
            )


class BseBhavcopySource:
    """Daily BSE equity bhavcopy. BSE ran a parallel format change; both handled."""

    name = "bse_bhavcopy"
    BSE_UDIFF_CUTOVER = date(2024, 7, 8)

    def __init__(self, start: date, end: date, polite_delay: float = 0.4):
        self.start = start
        self.end = end
        self.delay = polite_delay

    def _url(self, day: date) -> str:
        if day >= self.BSE_UDIFF_CUTOVER:
            return (
                f"https://{BSE_HOST}/download/BhavCopy/Equity/"
                f"BhavCopy_BSE_CM_0_0_0_{day:%Y%m%d}_F_0000.CSV"
            )
        return f"https://{BSE_HOST}/download/BhavCopy/Equity/EQ{day:%d%m%y}_CSV.ZIP"

    def fetch(self, targets: list[str] | None = None) -> Iterator[Document]:
        import time

        session = _session(prime=False)
        for day in trading_days(self.start, self.end):
            time.sleep(self.delay)
            url = self._url(day)
            try:
                resp = session.get(url, timeout=45)
            except Exception as exc:
                raise SourceRequiresLocal("bse_bhavcopy", BSE_HOST) from exc
            if resp.status_code == 404:
                continue
            if resp.status_code != 200:
                raise SourceUnavailable(f"BSE returned {resp.status_code} for {day}")

            yield Document(
                content=_unzip(resp.content),
                doc_type="prices",
                source=self.name,
                company=None,
                published_at=day,
                url=url,
                content_type="text/csv",
                meta={
                    "trade_date": day.isoformat(),
                    "exchange": "BSE",
                    "format": "udiff" if day >= self.BSE_UDIFF_CUTOVER else "legacy",
                    "adjusted": False,
                },
            )
