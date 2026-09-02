"""Source adapter protocol.

Every adapter is a generator of Documents. Adapters do not touch the store — the
CLI owns writing, so an adapter cannot corrupt the corpus and can be tested with
no filesystem at all.
"""

from __future__ import annotations

from typing import Iterator, Protocol, runtime_checkable

from ..model import Document


@runtime_checkable
class Source(Protocol):
    name: str

    def fetch(self, targets: list[str] | None = None) -> Iterator[Document]:
        """Yield documents. Must not write anything.

        Raise SourceUnavailable for a transient/network/credential problem so the
        CLI can distinguish "could not reach it" from "there was nothing there" —
        silently ingesting zero documents is how a corpus quietly rots.
        """
        ...


class SourceUnavailable(RuntimeError):
    """Network, credential or upstream failure. Distinct from an empty result."""


class SourceRequiresLocal(SourceUnavailable):
    """Raised when a source needs egress this environment does not have.

    Carries the diagnosis rather than a bare connection error, because the failure
    is architectural (see ../../CONTRACT.md) and not something a retry will fix.
    """

    def __init__(self, source: str, host: str):
        super().__init__(
            f"source '{source}' needs network access to {host}, which is blocked here.\n"
            f"Ingestion is designed to run on your own machine — see ingest/README.md.\n"
            f"To work inside a sandbox instead, use: tanstaafl-ingest drop <files>"
        )
        self.source = source
        self.host = host
