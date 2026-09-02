"""Core types shared by the write side (ingest) and read side (analysis)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, asdict
from datetime import date, datetime, timezone
from typing import Any


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def sha256_of(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _iso(value: date | datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


@dataclass(slots=True)
class Document:
    """A document on its way into the corpus. Write side only."""

    content: bytes
    doc_type: str  # annual_report | quarterly_result | shareholding | transcript | prices | rating | other
    source: str  # which adapter produced it
    company: str | None = None  # canonical ticker, None for market-wide data
    published_at: date | None = None  # when it entered the public record
    url: str | None = None
    content_type: str = "application/octet-stream"
    retrieved_at: datetime = field(default_factory=utcnow)
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def sha256(self) -> str:
        return sha256_of(self.content)

    def to_record(self) -> "Record":
        return Record(
            sha256=self.sha256,
            doc_type=self.doc_type,
            source=self.source,
            company=self.company,
            published_at=self.published_at,
            url=self.url,
            content_type=self.content_type,
            retrieved_at=self.retrieved_at,
            bytes=len(self.content),
            meta=dict(self.meta),
        )


@dataclass(slots=True)
class Record:
    """One line of the evidence manifest. This is the contract artifact.

    The manifest is committed to git; the blobs it points at are not. A record is
    append-only and immutable once written.
    """

    sha256: str
    doc_type: str
    source: str
    company: str | None
    published_at: date | None
    url: str | None
    content_type: str
    retrieved_at: datetime
    bytes: int
    meta: dict[str, Any] = field(default_factory=dict)

    # Identity for dedup: the same bytes may legitimately arrive from two sources,
    # and recording both is provenance, not duplication.
    @property
    def key(self) -> tuple[str, str, str | None]:
        return (self.sha256, self.source, self.url)

    def to_json(self) -> str:
        d = asdict(self)
        d["published_at"] = _iso(self.published_at)
        d["retrieved_at"] = _iso(self.retrieved_at)
        return json.dumps(d, sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, line: str) -> "Record":
        d = json.loads(line)
        pub = d.get("published_at")
        ret = d.get("retrieved_at")
        return cls(
            sha256=d["sha256"],
            doc_type=d["doc_type"],
            source=d["source"],
            company=d.get("company"),
            published_at=date.fromisoformat(pub) if pub else None,
            retrieved_at=datetime.fromisoformat(ret) if ret else utcnow(),
            url=d.get("url"),
            content_type=d.get("content_type", "application/octet-stream"),
            bytes=d.get("bytes", 0),
            meta=d.get("meta", {}),
        )
