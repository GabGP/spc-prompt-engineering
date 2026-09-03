"""Unit tests for input_resolver module."""

from pathlib import Path

import pytest

from src.ingestion.input_resolver import (
    discover_input_files,
    natural_sort_key,
    resolve_input_path,
    resolve_source_book,
)


def test_natural_sort_key() -> None:
    """Verify natural sorting key correctly decomposes numeric chunks."""
    p1 = Path("page_2.pdf")
    p2 = Path("page_10.pdf")
    p3 = Path("PAGE_01.pdf")
    assert natural_sort_key(p1) < natural_sort_key(p2)
    assert natural_sort_key(p3) < natural_sort_key(p1)


def test_discover_input_files_filtering_and_order(tmp_path: Path) -> None:
    """Verify discovery filters extensions, ignores hidden files, and sorts naturally."""
    # Non-existent directory
    assert discover_input_files(tmp_path / "missing") == []

    # Populate directory
    in_dir = tmp_path / "inputs"
    in_dir.mkdir()
    assert discover_input_files(in_dir) == []

    (in_dir / "page_10.pdf").write_text("10")
    (in_dir / "page_2.pdf").write_text("2")
    (in_dir / "notes.txt").write_text("text")
    (in_dir / "summary.md").write_text("md")
    (in_dir / ".gitkeep").write_text("")
    (in_dir / "ignore.json").write_text("{}")

    files = discover_input_files(in_dir)
    names = [f.name for f in files]
    assert names == ["notes.txt", "page_2.pdf", "page_10.pdf", "summary.md"]


def test_resolve_input_path_explicit(tmp_path: Path) -> None:
    """Verify explicit page resolution succeeds if existing, or raises FileNotFoundError."""
    existing = tmp_path / "custom.pdf"
    existing.write_text("content")

    assert resolve_input_path(existing, run_id=1) == existing

    with pytest.raises(FileNotFoundError, match="Input file not found"):
        resolve_input_path(tmp_path / "missing.pdf", run_id=1)


def test_resolve_input_path_by_order(tmp_path: Path) -> None:
    """Verify input file resolution uses discovered files in natural order."""
    in_dir = tmp_path / "inputs"
    in_dir.mkdir()

    # Empty directory
    with pytest.raises(FileNotFoundError, match="No input files found"):
        resolve_input_path(None, run_id=1, inputs_dir=in_dir)

    # Add sliced files starting at page_002.pdf
    (in_dir / "page_002.pdf").write_text("page 2")
    (in_dir / "page_003.pdf").write_text("page 3")

    # Run 1 selects first order found (page_002.pdf)
    assert resolve_input_path(None, run_id=1, inputs_dir=in_dir).name == "page_002.pdf"
    # Run 2 selects second order found (page_003.pdf)
    assert resolve_input_path(None, run_id=2, inputs_dir=in_dir).name == "page_003.pdf"

    # Run 3 exceeds available inputs
    with pytest.raises(IndexError, match="requested run exceeds available inputs"):
        resolve_input_path(None, run_id=3, inputs_dir=in_dir)


def test_resolve_source_book(tmp_path: Path) -> None:
    """Verify source book discovery and validation."""
    raw_dir = tmp_path / "raw"
    data_dir = tmp_path / "data"
    raw_dir.mkdir()
    data_dir.mkdir()

    # Explicit existing
    book = tmp_path / "my_book.pdf"
    book.write_text("pdf")
    assert resolve_source_book(book) == book

    # Explicit missing
    with pytest.raises(FileNotFoundError, match="Source textbook PDF not found"):
        resolve_source_book(tmp_path / "none.pdf")

    # No PDFs in raw or data
    with pytest.raises(ValueError, match="No PDF found"):
        resolve_source_book(None, raw_dir=raw_dir, data_dir=data_dir)

    # Single in raw_dir
    b1 = raw_dir / "book1.pdf"
    b1.write_text("b1")
    assert resolve_source_book(None, raw_dir=raw_dir, data_dir=data_dir) == b1

    # Multiple PDFs in raw_dir
    b2 = raw_dir / "book2.pdf"
    b2.write_text("b2")
    with pytest.raises(ValueError, match="Multiple PDFs found"):
        resolve_source_book(None, raw_dir=raw_dir, data_dir=data_dir)

    # Fallback to data_dir when raw_dir is empty
    b1.unlink()
    b2.unlink()
    b_data = data_dir / "fallback.pdf"
    b_data.write_text("data")
    assert resolve_source_book(None, raw_dir=raw_dir, data_dir=data_dir) == b_data
