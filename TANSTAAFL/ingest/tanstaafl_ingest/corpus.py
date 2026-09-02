"""Read-only corpus access. This is the ONLY module the analysis tiers import.

No network, no credentials, no writes. Runs anywhere the corpus is present —
including inside a sandbox with no egress (see ../CONTRACT.md).

The point-in-time filter lives here rather than in each agent, because
`../../CLAUDE.md` §1 makes it the cardinal rule and a rule enforced in one place
is a rule that actually holds.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterator

from .model import Record
from .store import Manifest, Paths


class PointInTimeError(RuntimeError):
    """Raised when a caller reaches for a document it must not be able to see."""


@dataclass(slots=True)
class CorpusReader:
    """Read access to the evidence corpus, optionally pinned to an as-of date.

    A reader pinned with `as_of` cannot see documents published later. It cannot be
    unpinned — `as_of()` returns a new reader and only ever narrows, never widens.
    """

    paths: Paths
    _as_of: date | None = None

    @classmethod
    def open(cls, root: Path | None = None, as_of: date | None = None) -> "CorpusReader":
        return cls(paths=Paths.discover(root), _as_of=as_of)

    def as_of(self, when: date) -> "CorpusReader":
        """Narrow to documents published on or before `when`. Never widens."""
        if self._as_of is not None and when > self._as_of:
            raise PointInTimeError(
                f"cannot widen a pinned reader from {self._as_of} to {when}"
            )
        return CorpusReader(paths=self.paths, _as_of=when)

    # ---- querying -------------------------------------------------------

    def _visible(self) -> Iterator[Record]:
        manifest = Manifest(self.paths.manifest)
        for record in manifest.load():
            if self._as_of is None:
                yield record
                continue
            # An undated document cannot be proven to predate the cutoff, so under a
            # pinned reader it is withheld. Unknown provenance is not a licence.
            if record.published_at is not None and record.published_at <= self._as_of:
                yield record

    def records(
        self,
        company: str | None = None,
        doc_type: str | None = None,
        source: str | None = None,
    ) -> list[Record]:
        out = []
        for r in self._visible():
            if company is not None and r.company != company:
                continue
            if doc_type is not None and r.doc_type != doc_type:
                continue
            if source is not None and r.source != source:
                continue
            out.append(r)
        return sorted(out, key=lambda r: (r.published_at or date.min, r.sha256))

    def read(self, record: Record) -> bytes:
        """Fetch blob bytes, re-checking visibility so a stale Record cannot leak."""
        if self._as_of is not None:
            if record.published_at is None or record.published_at > self._as_of:
                raise PointInTimeError(
                    f"{record.sha256[:12]} published {record.published_at} "
                    f"is not visible as of {self._as_of}"
                )
        path = self.paths.blob(record.sha256)
        if not path.exists():
            raise FileNotFoundError(
                f"blob {record.sha256[:12]} is in the manifest but not on disk — "
                "the corpus was not synced. See ingest/README.md."
            )
        return path.read_bytes()

    # ---- coverage -------------------------------------------------------

    def companies(self) -> list[str]:
        return sorted({r.company for r in self._visible() if r.company})

    def coverage(self) -> dict[str, dict[str, int]]:
        """Per-company document counts by type. Thin coverage is itself a finding:
        a filter that rejects on an absent RPT note is not the same as one that
        rejects on an adverse RPT note."""
        out: dict[str, dict[str, int]] = {}
        for r in self._visible():
            key = r.company or "_market"
            out.setdefault(key, {})
            out[key][r.doc_type] = out[key].get(r.doc_type, 0) + 1
        return out

    def undated(self) -> list[Record]:
        """Documents with no publication date. These are invisible to any pinned
        reader, so they are a data-quality backlog, not merely untidy."""
        manifest = Manifest(self.paths.manifest)
        return [r for r in manifest.load() if r.published_at is None]
