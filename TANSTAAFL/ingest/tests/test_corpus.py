"""Round-trip and point-in-time guarantees.

The point-in-time tests are the important ones: CLAUDE.md §1 makes lookahead the
cardinal sin, and a rule enforced only by instructions is not enforced at all.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from tanstaafl_ingest.corpus import CorpusReader, PointInTimeError
from tanstaafl_ingest.model import Document
from tanstaafl_ingest.sources.drop import DropSource, parse_name
from tanstaafl_ingest.store import Paths, Store


@pytest.fixture
def root(tmp_path: Path) -> Path:
    (tmp_path / "doctrine").mkdir()
    (tmp_path / "memory" / "evidence").mkdir(parents=True)
    (tmp_path / "data" / "raw").mkdir(parents=True)
    return tmp_path


@pytest.fixture
def store(root: Path) -> Store:
    return Store(Paths(root=root))


def doc(company="PAGEIND", published=date(2019, 7, 15), content=b"x", **kw) -> Document:
    return Document(
        content=content,
        doc_type=kw.pop("doc_type", "annual_report"),
        source=kw.pop("source", "test"),
        company=company,
        published_at=published,
        **kw,
    )


# ---- store ---------------------------------------------------------------

def test_put_then_read_roundtrip(store: Store):
    result = store.put(doc(content=b"hello corpus"))
    assert result.status == "new"
    assert store.read(result.record.sha256) == b"hello corpus"


def test_identical_content_is_deduped(store: Store):
    assert store.put(doc(content=b"same")).status == "new"
    assert store.put(doc(content=b"same")).status == "duplicate"
    assert len(store.manifest.load()) == 1


def test_same_bytes_from_another_source_records_provenance(store: Store):
    """Two sources supplying identical bytes is provenance, not duplication."""
    store.put(doc(content=b"same", source="screener"))
    result = store.put(doc(content=b"same", source="nse"))
    assert result.status == "new-provenance"
    assert len(store.manifest.load()) == 2
    assert len({r.sha256 for r in store.manifest.load()}) == 1  # one blob


def test_verify_detects_corruption(store: Store):
    result = store.put(doc(content=b"original"))
    store.paths.blob(result.record.sha256).write_bytes(b"tampered")
    report = store.verify()
    assert not report.ok
    assert result.record.sha256 in report.corrupt


def test_verify_detects_missing_blob(store: Store):
    result = store.put(doc(content=b"vanishing"))
    store.paths.blob(result.record.sha256).unlink()
    report = store.verify()
    assert not report.ok
    assert result.record.sha256 in report.missing


def test_verify_passes_on_clean_corpus(store: Store):
    store.put(doc(content=b"a"))
    store.put(doc(content=b"b", company="BERGEPAINT"))
    assert store.verify().ok


# ---- point-in-time -------------------------------------------------------

def test_reader_hides_documents_published_after_as_of(store: Store, root: Path):
    store.put(doc(content=b"early", published=date(2018, 1, 1)))
    store.put(doc(content=b"late", published=date(2020, 1, 1)))

    reader = CorpusReader(paths=Paths(root=root)).as_of(date(2019, 1, 1))
    visible = reader.records()
    assert len(visible) == 1
    assert reader.read(visible[0]) == b"early"


def test_undated_documents_are_invisible_to_pinned_reader(store: Store, root: Path):
    """Unknown provenance is not a licence to assume the document was available."""
    store.put(doc(content=b"whenever", published=None))
    reader = CorpusReader(paths=Paths(root=root))
    assert len(reader.records()) == 1                      # unpinned sees it
    assert len(reader.as_of(date(2020, 1, 1)).records()) == 0  # pinned does not
    assert len(reader.undated()) == 1


def test_reader_cannot_be_widened(root: Path):
    reader = CorpusReader(paths=Paths(root=root)).as_of(date(2019, 1, 1))
    with pytest.raises(PointInTimeError):
        reader.as_of(date(2021, 1, 1))
    assert reader.as_of(date(2018, 1, 1))._as_of == date(2018, 1, 1)  # narrowing is fine


def test_read_rejects_a_stale_record_handle(store: Store, root: Path):
    """Holding a Record from an unpinned reader must not smuggle it past the cutoff."""
    store.put(doc(content=b"future", published=date(2025, 1, 1)))
    unpinned = CorpusReader(paths=Paths(root=root))
    record = unpinned.records()[0]

    pinned = CorpusReader(paths=Paths(root=root)).as_of(date(2019, 1, 1))
    with pytest.raises(PointInTimeError):
        pinned.read(record)


def test_read_reports_unsynced_corpus_clearly(store: Store, root: Path):
    result = store.put(doc(content=b"gone"))
    store.paths.blob(result.record.sha256).unlink()
    reader = CorpusReader(paths=Paths(root=root))
    with pytest.raises(FileNotFoundError, match="not synced"):
        reader.read(reader.records()[0])


# ---- drop source ---------------------------------------------------------

@pytest.mark.parametrize(
    "name,expected",
    [
        ("PAGEIND__annual_report__2019-07-15.pdf", ("PAGEIND", "annual_report", date(2019, 7, 15))),
        ("_market__prices__2024-03-31.csv", (None, "prices", date(2024, 3, 31))),
        ("PAGEIND__nonsense__2019-07-15.pdf", ("PAGEIND", "other", date(2019, 7, 15))),
        ("PAGEIND__annual_report__notadate.pdf", ("PAGEIND", "annual_report", None)),
        ("random.pdf", (None, "other", None)),
    ],
)
def test_filename_convention(name, expected):
    assert parse_name(Path(name)) == expected


def test_drop_reads_files_and_sidecar(tmp_path: Path):
    (tmp_path / "PAGEIND__annual_report__2019-07-15.pdf").write_bytes(b"ar")
    (tmp_path / "mystery.csv").write_bytes(b"m")
    (tmp_path / "_meta.csv").write_text(
        "filename,company,doc_type,published_at,url\n"
        "mystery.csv,BERGEPAINT,shareholding,2020-03-31,https://example.com/x\n",
        encoding="utf-8",
    )

    docs = {d.company: d for d in DropSource([tmp_path]).fetch()}
    assert docs["PAGEIND"].doc_type == "annual_report"
    assert docs["BERGEPAINT"].doc_type == "shareholding"
    assert docs["BERGEPAINT"].published_at == date(2020, 3, 31)
    assert docs["BERGEPAINT"].url == "https://example.com/x"


def test_drop_ingest_is_idempotent(store: Store, tmp_path: Path):
    src = tmp_path / "drop"
    src.mkdir()
    (src / "PAGEIND__annual_report__2019-07-15.pdf").write_bytes(b"content")

    first = [store.put(d) for d in DropSource([src]).fetch()]
    second = [store.put(d) for d in DropSource([src]).fetch()]
    assert [r.status for r in first] == ["new"]
    assert [r.status for r in second] == ["duplicate"]
