"""Screener.in adapter.

LOCAL ONLY. Requires a logged-in session cookie (SCREENER_SESSION in .env).
Not exercised in CI — treat as untested until it has run on a real machine.

Screener is the pragmatic starting point for TANSTAAFL: 10 years of standardised
financials per company, exportable, at negligible cost. Respect their terms and
rate limits — this fetches slowly on purpose.
"""

from __future__ import annotations

import os
import time
from datetime import date
from typing import Iterator

from ..model import Document
from .base import SourceRequiresLocal, SourceUnavailable

HOST = "www.screener.in"
BASE = f"https://{HOST}"
DELAY_SECONDS = 3.0  # deliberate politeness; do not lower


class ScreenerSource:
    """Per-company 10-year financial export (xlsx)."""

    name = "screener"

    def __init__(self, session_cookie: str | None = None, delay: float = DELAY_SECONDS):
        self.cookie = session_cookie or os.environ.get("SCREENER_SESSION")
        self.delay = delay

    def fetch(self, targets: list[str] | None = None) -> Iterator[Document]:
        if not targets:
            raise SourceUnavailable("screener needs a list of tickers")
        if not self.cookie:
            raise SourceUnavailable(
                "SCREENER_SESSION not set. Log in at screener.in, copy the "
                "'sessionid' cookie, and put it in ingest/.env (see .env.example)."
            )
        try:
            import requests
        except ImportError as exc:  # pragma: no cover
            raise SourceUnavailable("pip install requests to use the screener source") from exc

        session = requests.Session()
        session.headers.update({"User-Agent": "TANSTAAFL-ingest/0.1"})
        session.cookies.set("sessionid", self.cookie, domain=HOST)

        for i, symbol in enumerate(targets):
            if i:
                time.sleep(self.delay)
            yield self._fetch_one(session, symbol)

    def _fetch_one(self, session, symbol: str) -> Document:
        url = f"{BASE}/api/company/{symbol}/export/"
        try:
            resp = session.get(url, timeout=60)
        except Exception as exc:
            raise SourceRequiresLocal("screener", HOST) from exc

        if resp.status_code in (401, 403):
            raise SourceUnavailable(
                f"screener rejected the session for {symbol} (HTTP {resp.status_code}). "
                "The sessionid cookie has probably expired — log in again."
            )
        if resp.status_code != 200:
            raise SourceUnavailable(f"screener returned {resp.status_code} for {symbol}")

        return Document(
            content=resp.content,
            doc_type="quarterly_result",
            source=self.name,
            company=symbol.upper(),
            # The export is a snapshot as of retrieval; that IS its publication date
            # for point-in-time purposes. Per-period dates are recovered in Tier 1
            # normalisation, which can see inside the workbook.
            published_at=date.today(),
            url=url,
            content_type=(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
            meta={"export_kind": "10y_financials", "snapshot": True},
        )
