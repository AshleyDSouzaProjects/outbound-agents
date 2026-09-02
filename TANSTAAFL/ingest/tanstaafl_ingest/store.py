"""Content-addressed immutable blob store plus the append-only evidence manifest.

Write side. Runs locally only (see ../CONTRACT.md).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from .model import Document, Record, sha256_of


def find_root(start: Path | None = None) -> Path:
    """Locate the TANSTAAFL root: $TANSTAAFL_ROOT, or walk up for a doctrine/ dir."""
    env = os.environ.get("TANSTAAFL_ROOT")
    if env:
        return Path(env).expanduser().resolve()
    here = (start or Path.cwd()).resolve()
    for candidate in (here, *here.parents):
        if (candidate / "doctrine").is_dir() and (candidate / "memory").is_dir():
            return candidate
    raise RuntimeError(
        "Cannot locate TANSTAAFL root. Set TANSTAAFL_ROOT or run from inside the tree."
    )


@dataclass(slots=True)
class Paths:
    root: Path

    @classmethod
    def discover(cls, start: Path | None = None) -> "Paths":
        return cls(root=find_root(start))

    @property
    def raw(self) -> Path:
        return self.root / "data" / "raw"

    @property
    def manifest(self) -> Path:
        return self.root / "memory" / "evidence" / "manifest.jsonl"

    def blob(self, sha: str) -> Path:
        # Fan out on the first two hex chars; a flat dir with 10^5 files is miserable.
        return self.raw / sha[:2] / sha


class Manifest:
    """Append-only JSONL index of every document in the corpus.

    Committed to git. Small, text, diffable — this is what travels between machines
    even when the blobs do not.
    """

    def __init__(self, path: Path):
        self.path = path
        self._records: list[Record] | None = None

    def load(self) -> list[Record]:
        if self._records is None:
            if self.path.exists():
                self._records = [
                    Record.from_json(ln)
                    for ln in self.path.read_text(encoding="utf-8").splitlines()
                    if ln.strip()
                ]
            else:
                self._records = []
        return self._records

    def keys(self) -> set[tuple[str, str, str | None]]:
        return {r.key for r in self.load()}

    def shas(self) -> set[str]:
        return {r.sha256 for r in self.load()}

    def append(self, record: Record) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(record.to_json() + "\n")
        self.load().append(record)


@dataclass(slots=True)
class PutResult:
    record: Record
    blob_written: bool
    record_written: bool

    @property
    def status(self) -> str:
        if self.blob_written:
            return "new"
        return "new-provenance" if self.record_written else "duplicate"


class Store:
    """Immutable content-addressed store. Blobs are never modified or deleted."""

    def __init__(self, paths: Paths | None = None):
        self.paths = paths or Paths.discover()
        self.manifest = Manifest(self.paths.manifest)

    def put(self, doc: Document) -> PutResult:
        record = doc.to_record()
        blob_path = self.paths.blob(record.sha256)

        blob_written = False
        if not blob_path.exists():
            blob_path.parent.mkdir(parents=True, exist_ok=True)
            # Write-then-rename so a crash cannot leave a truncated blob that would
            # later fail verification for no recoverable reason.
            tmp = blob_path.with_suffix(".tmp")
            tmp.write_bytes(doc.content)
            tmp.replace(blob_path)
            blob_written = True

        record_written = False
        if record.key not in self.manifest.keys():
            self.manifest.append(record)
            record_written = True

        return PutResult(record, blob_written, record_written)

    def read(self, sha: str) -> bytes:
        return self.paths.blob(sha).read_bytes()

    def verify(self) -> "VerifyReport":
        """Recompute every blob hash against the manifest.

        Silent corruption in an immutable evidence store is the one failure that
        invalidates everything downstream, so this is cheap insurance.
        """
        missing: list[str] = []
        corrupt: list[str] = []
        seen: set[str] = set()
        for record in self.manifest.load():
            if record.sha256 in seen:
                continue
            seen.add(record.sha256)
            path = self.paths.blob(record.sha256)
            if not path.exists():
                missing.append(record.sha256)
            elif sha256_of(path.read_bytes()) != record.sha256:
                corrupt.append(record.sha256)

        orphans = [
            p.name
            for p in self.paths.raw.glob("*/*")
            if p.is_file() and not p.name.endswith(".tmp") and p.name not in seen
        ] if self.paths.raw.exists() else []

        return VerifyReport(len(seen), missing, corrupt, orphans)


@dataclass(slots=True)
class VerifyReport:
    checked: int
    missing: list[str]
    corrupt: list[str]
    orphans: list[str]

    @property
    def ok(self) -> bool:
        return not self.missing and not self.corrupt
