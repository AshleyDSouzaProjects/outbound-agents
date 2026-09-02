"""Manual file drop. The one source that works everywhere, including sandboxes.

Metadata comes from a filename convention or an explicit sidecar CSV:

    TICKER__doctype__YYYY-MM-DD.ext
    PAGEIND__annual_report__2019-07-15.pdf
    _market__prices__2024-03-31.csv        # market-wide data uses _market

A sidecar `_meta.csv` in the same directory overrides the convention:

    filename,company,doc_type,published_at,url
"""

from __future__ import annotations

import csv
import mimetypes
from datetime import date
from pathlib import Path
from typing import Iterator

from ..model import Document

DOC_TYPES = {
    "annual_report",
    "quarterly_result",
    "shareholding",
    "transcript",
    "prices",
    "rating",
    "filing",
    "other",
}


def parse_name(path: Path) -> tuple[str | None, str, date | None]:
    """Return (company, doc_type, published_at) from the filename convention."""
    parts = path.stem.split("__")
    if len(parts) != 3:
        return None, "other", None

    company_raw, doc_type, datestr = parts
    company = None if company_raw == "_market" else company_raw.upper()
    if doc_type not in DOC_TYPES:
        doc_type = "other"
    try:
        published = date.fromisoformat(datestr)
    except ValueError:
        published = None
    return company, doc_type, published


def _load_sidecar(directory: Path) -> dict[str, dict[str, str]]:
    sidecar = directory / "_meta.csv"
    if not sidecar.exists():
        return {}
    with sidecar.open(newline="", encoding="utf-8") as fh:
        return {row["filename"]: row for row in csv.DictReader(fh)}


class DropSource:
    """Ingest local files. Never touches the network."""

    name = "drop"

    def __init__(self, paths: list[Path]):
        self.paths = paths

    def _files(self) -> Iterator[Path]:
        for p in self.paths:
            if p.is_dir():
                for child in sorted(p.rglob("*")):
                    if child.is_file() and child.name != "_meta.csv":
                        yield child
            elif p.is_file():
                yield p

    def fetch(self, targets: list[str] | None = None) -> Iterator[Document]:
        for path in self._files():
            company, doc_type, published = parse_name(path)

            sidecar = _load_sidecar(path.parent).get(path.name)
            if sidecar:
                company = (sidecar.get("company") or company or "").upper() or None
                doc_type = sidecar.get("doc_type") or doc_type
                if sidecar.get("published_at"):
                    try:
                        published = date.fromisoformat(sidecar["published_at"])
                    except ValueError:
                        pass

            content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            yield Document(
                content=path.read_bytes(),
                doc_type=doc_type,
                source=self.name,
                company=company,
                published_at=published,
                url=(sidecar or {}).get("url") or f"file://{path.resolve()}",
                content_type=content_type,
                meta={"original_filename": path.name},
            )
