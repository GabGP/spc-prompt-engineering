"""Extracts individual pages from textbook PDFs and evaluates text density."""

import logging
from pathlib import Path

import pypdf

logging.getLogger("pypdf").setLevel(logging.ERROR)


class PDFSlicer:
    """Extracts single PDF pages and verifies textual content bounds."""

    def __init__(self, min_words: int = 50, max_words: int = 1500) -> None:
        self.min_words = min_words
        self.max_words = max_words

    def slice_page(
        self, src_pdf: Path | str, page_number: int, output_pdf: Path | str
    ) -> Path:
        """Extract a single 1-indexed page from a source PDF and save to disk."""
        src_path = Path(src_pdf)
        if not src_path.exists():
            raise FileNotFoundError(f"Source PDF not found: {src_path}")

        reader = pypdf.PdfReader(str(src_path))
        total_pages = len(reader.pages)

        if page_number < 1 or page_number > total_pages:
            raise IndexError(
                f"Page {page_number} out of range (PDF contains {total_pages} pages)"
            )

        writer = pypdf.PdfWriter()
        writer.add_page(reader.pages[page_number - 1])

        out_path = Path(output_pdf)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        with open(out_path, "wb") as f:
            writer.write(f)

        return out_path

    def extract_page_text(self, pdf_path: Path | str, page_number: int = 1) -> str:
        """Extract all textual content from a specific 1-indexed page."""
        path = Path(pdf_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {path}")

        reader = pypdf.PdfReader(str(path))
        total_pages = len(reader.pages)
        if page_number < 1 or page_number > total_pages:
            raise IndexError(
                f"Page {page_number} out of range (PDF contains {total_pages} pages)"
            )

        return reader.pages[page_number - 1].extract_text() or ""

    def extract_text_and_density(
        self, pdf_path: Path | str, page_number: int = 1
    ) -> tuple[str, int]:
        """Extract text and compute word density count for a page."""
        text = self.extract_page_text(pdf_path, page_number)
        word_count = len(text.split())
        return text, word_count

    def verify_text_density(self, word_count: int) -> bool:
        """Check if page word count satisfies experimental density limits."""
        return self.min_words <= word_count <= self.max_words

    def slice_range(
        self,
        src_pdf: Path | str,
        start_page: int,
        end_page: int,
        output_dir: Path | str,
        start_index: int | None = None,
    ) -> list[Path]:
        """Slice a range of pages [start_page, end_page] into individual files."""
        if start_page > end_page:
            raise ValueError(
                f"start_page ({start_page}) cannot exceed end_page ({end_page})"
            )

        out_dir = Path(output_dir)
        sliced_files: list[Path] = []

        for offset, page in enumerate(range(start_page, end_page + 1)):
            idx = (start_index + offset) if start_index is not None else page
            target = out_dir / f"page_{idx:03d}.pdf"
            self.slice_page(src_pdf, page, target)
            sliced_files.append(target)

        return sliced_files
