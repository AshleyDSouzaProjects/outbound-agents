"""TANSTAAFL ingestion + corpus access.

Write side (Store, sources, CLI) runs locally only — it needs network and
credentials. Read side (CorpusReader) runs anywhere and needs neither.
See ../CONTRACT.md for the boundary.
"""

from .corpus import CorpusReader, PointInTimeError
from .model import Document, Record
from .store import Paths, Store

__all__ = [
    "CorpusReader",
    "PointInTimeError",
    "Document",
    "Record",
    "Paths",
    "Store",
]
__version__ = "0.1.0"
