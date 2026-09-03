"""Unit tests for PDF page slicing and text density extraction."""

import io
from pathlib import Path

import pypdf
import pytest

from src.ingestion.pdf_slicer import PDFSlicer

SAMPLE_PDF_BYTES = b"""%PDF-1.4
1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj
2 0 obj <</Type /Pages /Kids [3 0 R] /Count 1>> endobj
3 0 obj <</Type /Page /Parent 2 0 R /MediaBox [0 0 300 300] /Contents 4 0 R /Resources <</Font <</F1 5 0 R>>>>>> endobj
4 0 obj <</Length 55>> stream
BT
/F1 12 Tf
100 100 Td
(Statistical Process Control) Tj
ET
endstream
endobj
5 0 obj <</Type /Font /Subtype /Type1 /BaseFont /Helvetica>> endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000236 00000 n 
0000000341 00000 n 
trailer <</Size 6 /Root 1 0 R>>
startxref
416
%%EOF"""


def make_test_pdf(target: Path, page_count: int = 2) -> Path:
    """Generate a test PDF file with the specified number of text pages."""
    base_reader = pypdf.PdfReader(io.BytesIO(SAMPLE_PDF_BYTES))
    writer = pypdf.PdfWriter()
    for _ in range(page_count):
        writer.add_page(base_reader.pages[0])
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "wb") as f:
        writer.write(f)
    return target


def test_slice_page_success(tmp_path: Path) -> None:
    """Verify slicing extracts a single page and writes a valid PDF."""
    src = make_test_pdf(tmp_path / "book.pdf", page_count=2)
    out = tmp_path / "page_002.pdf"

    slicer = PDFSlicer()
    result = slicer.slice_page(src, page_number=2, output_pdf=out)

    assert result == out
    assert out.exists()

    reader = pypdf.PdfReader(str(out))
    assert len(reader.pages) == 1
    assert "Statistical Process Control" in reader.pages[0].extract_text()


def test_slice_page_missing_source(tmp_path: Path) -> None:
    """Verify FileNotFoundError when source PDF is missing."""
    slicer = PDFSlicer()
    with pytest.raises(FileNotFoundError, match="Source PDF not found"):
        slicer.slice_page(tmp_path / "nonexistent.pdf", 1, tmp_path / "out.pdf")


def test_slice_page_out_of_range(tmp_path: Path) -> None:
    """Verify IndexError when page number is zero or exceeds page count."""
    src = make_test_pdf(tmp_path / "book.pdf", page_count=2)
    slicer = PDFSlicer()

    with pytest.raises(IndexError, match="out of range"):
        slicer.slice_page(src, page_number=0, output_pdf=tmp_path / "out.pdf")

    with pytest.raises(IndexError, match="out of range"):
        slicer.slice_page(src, page_number=3, output_pdf=tmp_path / "out.pdf")


def test_extract_page_text_success_and_errors(tmp_path: Path) -> None:
    """Verify text extraction and error handling for missing file or bad bounds."""
    src = make_test_pdf(tmp_path / "book.pdf", page_count=1)
    slicer = PDFSlicer()

    text = slicer.extract_page_text(src, page_number=1)
    assert "Statistical Process Control" in text

    with pytest.raises(FileNotFoundError):
        slicer.extract_page_text(tmp_path / "missing.pdf")

    with pytest.raises(IndexError):
        slicer.extract_page_text(src, page_number=2)


def test_extract_text_and_density(tmp_path: Path) -> None:
    """Verify word count computation from extracted text."""
    src = make_test_pdf(tmp_path / "book.pdf", page_count=1)
    slicer = PDFSlicer()

    text, count = slicer.extract_text_and_density(src, page_number=1)
    assert count == 3
    assert text == "Statistical Process Control"


def test_verify_text_density() -> None:
    """Verify text density boundaries."""
    slicer = PDFSlicer(min_words=50, max_words=1500)
    assert not slicer.verify_text_density(20)
    assert slicer.verify_text_density(50)
    assert slicer.verify_text_density(500)
    assert slicer.verify_text_density(1500)
    assert not slicer.verify_text_density(1501)


def test_slice_range_success(tmp_path: Path) -> None:
    """Verify slicing a multi-page range creates expected files."""
    src = make_test_pdf(tmp_path / "book.pdf", page_count=3)
    out_dir = tmp_path / "inputs"

    slicer = PDFSlicer()
    files = slicer.slice_range(src, start_page=1, end_page=3, output_dir=out_dir)

    assert len(files) == 3
    assert (out_dir / "page_001.pdf").exists()
    assert (out_dir / "page_002.pdf").exists()
    assert (out_dir / "page_003.pdf").exists()


def test_slice_range_invalid_bounds(tmp_path: Path) -> None:
    """Verify ValueError when start_page > end_page."""
    src = make_test_pdf(tmp_path / "book.pdf", page_count=2)
    slicer = PDFSlicer()

    with pytest.raises(ValueError, match="cannot exceed end_page"):
        slicer.slice_range(src, start_page=3, end_page=1, output_dir=tmp_path)


def test_slice_range_with_start_index(tmp_path: Path) -> None:
    """Verify slicing with start_index creates sequentially numbered files."""
    src = make_test_pdf(tmp_path / "book.pdf", page_count=5)
    out_dir = tmp_path / "inputs"

    slicer = PDFSlicer()
    # Slice pages 3 to 5 sequentially re-indexed starting from 1
    files = slicer.slice_range(
        src, start_page=3, end_page=5, output_dir=out_dir, start_index=1
    )

    assert len(files) == 3
    assert [f.name for f in files] == ["page_001.pdf", "page_002.pdf", "page_003.pdf"]
    assert (out_dir / "page_001.pdf").exists()
