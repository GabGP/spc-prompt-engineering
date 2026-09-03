"""Unit tests for slice_handler module."""

from pathlib import Path

from src.ui.cli import build_parser
from src.ui.slice_handler import handle_slice
from tests.ingestion.test_pdf_slicer import make_test_pdf


def test_handle_slice_success_and_errors(tmp_path: Path, monkeypatch) -> None:
    """Verify handle_slice processes valid slicing and error paths."""
    monkeypatch.chdir(tmp_path)
    parser = build_parser()

    # Missing book file error
    args_fail = parser.parse_args(
        ["slice", "-b", str(tmp_path / "missing.pdf"), "-s", "1", "-e", "2"]
    )
    assert handle_slice(args_fail) == 1

    # Valid slice
    pdf_path = make_test_pdf(tmp_path / "book.pdf", page_count=2)
    out_dir = tmp_path / "out"
    args_ok = parser.parse_args(
        ["slice", "-b", str(pdf_path), "-s", "1", "-e", "2", "-o", str(out_dir)]
    )
    assert handle_slice(args_ok) == 0
    assert (out_dir / "page_001.pdf").exists()


def test_handle_slice_range_error(tmp_path: Path, monkeypatch) -> None:
    """Verify handle_slice returns 1 when requested page range is invalid."""
    monkeypatch.chdir(tmp_path)
    parser = build_parser()
    pdf_path = make_test_pdf(tmp_path / "book.pdf", page_count=2)
    args_err = parser.parse_args(
        ["slice", "-b", str(pdf_path), "-s", "5", "-e", "10", "-o", str(tmp_path / "out")]
    )
    assert handle_slice(args_err) == 1
