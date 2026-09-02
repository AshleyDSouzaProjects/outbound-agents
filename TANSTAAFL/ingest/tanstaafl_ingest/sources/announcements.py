"""NSE and BSE corporate-announcement firehose.

The single highest-leverage harvest in the system. One adapter yields four of the
inputs TANSTAAFL depends on most:

  * concall transcripts        -> promise-ledger  (no bulk transcript API exists
                                  anywhere; they are filed as exchange announcements,
                                  so this IS the bulk transcript source)
  * auditor changes/resignations -> governance-sentinel's best single signal
  * shareholding patterns & pledge disclosures -> the pledge veto
  * related-party approvals, board changes, ratings

Every announcement is classified on ingest by `..classify`, which is deterministic
rule-based rather than an LLM — see that module for why (reproducibility, cost,
auditability, testability).

Attachments are fetched selectively. Downloading every PDF for 500 companies over
15 years is terabytes of mostly-routine filings; downloading the ones whose category
carries analytical weight is a few gigabytes.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from typing import Iterator

from ..classify import Severity, classify
from ..model import Document
from .base import SourceRequiresLocal, SourceUnavailable

NSE_HOST = "www.nseindia.com"
BSE_API = "https://api.bseindia.com/BseIndiaAPI/api"

# Categories worth pulling the underlying document for.
ATTACHMENT_CATEGORIES = {
    "transcript",           # promise ledger
    "auditor_resignation",
    "auditor_change",
    "auditor_qualification",
    "annual_report",
    "shareholding_pattern",
    "related_party",
    "pledge",
    "pledge_invocation",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
}


def _session(referer: str):
    try:
        import requests
    except ImportError as exc:  # pragma: no cover
        raise SourceUnavailable("pip install '.[remote]' for network sources") from exc
    s = requests.Session()
    s.headers.update({**HEADERS, "Referer": referer})
    return s


def windows(start: date, end: date, days: int = 30) -> Iterator[tuple[date, date]]:
    """Both exchanges cap the queryable date range, so walk it in chunks."""
    cursor = start
    while cursor <= end:
        stop = min(cursor + timedelta(days=days - 1), end)
        yield cursor, stop
        cursor = stop + timedelta(days=1)


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    text = value.strip().replace("T", " ")
    for fmt in (
        "%d-%b-%Y %H:%M:%S", "%d-%b-%Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d",
        "%d/%m/%Y", "%d-%m-%Y %H:%M:%S", "%d-%m-%Y",
    ):
        try:
            return datetime.strptime(text[: len(fmt) + 4], fmt).date()
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text).date()
    except ValueError:
        return None


def _announcement_doc(
    *,
    source: str,
    company: str | None,
    published: date | None,
    subject: str,
    description: str | None,
    attachment: str | None,
    raw: dict,
    url: str,
) -> Document:
    result = classify(subject, description, attachment)
    return Document(
        content=json.dumps(raw, sort_keys=True, ensure_ascii=False).encode("utf-8"),
        doc_type="announcement",
        source=source,
        company=company,
        published_at=published,
        url=url,
        content_type="application/json",
        meta={
            "subject": (subject or "")[:400],
            "category": result.category,
            "severity": result.severity.value,
            "evidence": result.evidence,       # the exact substring that matched
            "also": result.also,
            "attachment_url": attachment,
        },
    )


class NseAnnouncementsSource:
    """NSE corporate announcements across a date range, all companies."""

    name = "nse_announcements"
    REFERER = "https://www.nseindia.com/companies-listing/corporate-filings-announcements"
    API = "https://www.nseindia.com/api/corporate-announcements"

    def __init__(
        self,
        start: date,
        end: date,
        with_attachments: bool = False,
        polite_delay: float = 1.0,
    ):
        self.start = start
        self.end = end
        self.with_attachments = with_attachments
        self.delay = polite_delay

    def fetch(self, targets: list[str] | None = None) -> Iterator[Document]:
        import time

        session = _session(self.REFERER)
        try:
            session.get("https://www.nseindia.com", timeout=15)  # cookie priming
        except Exception as exc:
            raise SourceRequiresLocal(self.name, NSE_HOST) from exc

        universe = {t.upper() for t in targets} if targets else None

        for lo, hi in windows(self.start, self.end):
            time.sleep(self.delay)
            url = (
                f"{self.API}?index=equities"
                f"&from_date={lo:%d-%m-%Y}&to_date={hi:%d-%m-%Y}"
            )
            try:
                resp = session.get(url, timeout=60)
            except Exception as exc:
                raise SourceRequiresLocal(self.name, NSE_HOST) from exc
            if resp.status_code != 200:
                raise SourceUnavailable(
                    f"NSE announcements returned {resp.status_code} for {lo}..{hi}"
                )
            try:
                items = resp.json()
            except ValueError:
                raise SourceUnavailable(
                    f"NSE announcements returned non-JSON for {lo}..{hi} — "
                    "usually a rate limit or an expired cookie."
                )
            if isinstance(items, dict):
                items = items.get("data", [])

            for item in items:
                symbol = (item.get("symbol") or "").upper() or None
                if universe and symbol not in universe:
                    continue
                doc = _announcement_doc(
                    source=self.name,
                    company=symbol,
                    published=parse_date(item.get("an_dt") or item.get("sort_date")),
                    subject=item.get("desc") or item.get("sm_name") or "",
                    description=item.get("attchmntText") or item.get("smIndustry"),
                    attachment=item.get("attchmntFile"),
                    raw=item,
                    url=url,
                )
                yield doc
                if self.with_attachments:
                    yield from self._attachment(session, doc)

    def _attachment(self, session, doc: Document) -> Iterator[Document]:
        import time

        link = doc.meta.get("attachment_url")
        if not link or doc.meta.get("category") not in ATTACHMENT_CATEGORIES:
            return
        time.sleep(self.delay)
        try:
            resp = session.get(link, timeout=90)
        except Exception:
            return  # a missing attachment is not worth failing the whole run
        if resp.status_code != 200:
            return
        yield Document(
            content=resp.content,
            doc_type=(
                "transcript" if doc.meta["category"] == "transcript"
                else "annual_report" if doc.meta["category"] == "annual_report"
                else "filing"
            ),
            source=f"{self.name}_attachment",
            company=doc.company,
            published_at=doc.published_at,
            url=link,
            content_type=resp.headers.get("Content-Type", "application/pdf"),
            meta={
                "category": doc.meta["category"],
                "severity": doc.meta["severity"],
                "subject": doc.meta["subject"],
            },
        )


class BseAnnouncementsSource:
    """BSE corporate announcements. Complementary to NSE, not redundant.

    Some companies are BSE-only, and filers occasionally submit to one exchange
    ahead of the other — for a veto-grade event like an auditor resignation, the
    earlier of the two is the date that matters.
    """

    name = "bse_announcements"
    REFERER = "https://www.bseindia.com/corporates/ann.html"

    def __init__(
        self,
        start: date,
        end: date,
        with_attachments: bool = False,
        polite_delay: float = 1.0,
    ):
        self.start = start
        self.end = end
        self.with_attachments = with_attachments
        self.delay = polite_delay

    def fetch(self, targets: list[str] | None = None) -> Iterator[Document]:
        import time

        session = _session(self.REFERER)
        for lo, hi in windows(self.start, self.end):
            page = 1
            while True:
                time.sleep(self.delay)
                url = (
                    f"{BSE_API}/AnnSubCategoryGetData/w?pageno={page}&strCat=-1"
                    f"&strPrevDate={lo:%Y%m%d}&strScrip=&strSearch=P"
                    f"&strToDate={hi:%Y%m%d}&strType=C"
                )
                try:
                    resp = session.get(url, timeout=60)
                except Exception as exc:
                    raise SourceRequiresLocal(self.name, "api.bseindia.com") from exc
                if resp.status_code != 200:
                    raise SourceUnavailable(
                        f"BSE announcements returned {resp.status_code} for {lo}..{hi}"
                    )
                try:
                    payload = resp.json()
                except ValueError:
                    raise SourceUnavailable(f"BSE returned non-JSON for {lo}..{hi}")

                rows = payload.get("Table") or []
                if not rows:
                    break

                for item in rows:
                    attachment = item.get("ATTACHMENTNAME")
                    link = (
                        f"https://www.bseindia.com/xml-data/corpfiling/AttachLive/{attachment}"
                        if attachment else None
                    )
                    yield _announcement_doc(
                        source=self.name,
                        company=(item.get("SCRIP_CD") and str(item["SCRIP_CD"])) or None,
                        published=parse_date(item.get("DT_TM") or item.get("News_submission_dt")),
                        subject=item.get("NEWSSUB") or item.get("HEADLINE") or "",
                        description=item.get("MORE") or item.get("CATEGORYNAME"),
                        attachment=link,
                        raw=item,
                        url=url,
                    )
                page += 1
                if page > 200:  # runaway guard
                    break


def summarise(docs: list[Document]) -> dict[str, int]:
    """Category histogram for a harvest. Watch the `unclassified` share over time:
    a rise means exchange phrasing drifted and the rules need extending."""
    out: dict[str, int] = {}
    for d in docs:
        key = d.meta.get("category", "unclassified")
        out[key] = out.get(key, 0) + 1
    return out


def veto_events(docs: list[Document]) -> list[Document]:
    return [d for d in docs if d.meta.get("severity") == Severity.VETO.value]
