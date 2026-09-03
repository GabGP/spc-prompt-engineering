"""Handler for textbook PDF page slicing command."""

import argparse
from rich.console import Console

from src.config import Settings
from src.ingestion.input_resolver import resolve_source_book
from src.ingestion.pdf_slicer import PDFSlicer
from src.ui.progress import create_slice_progress
from src.ui.views import default_console, render_slice_summary


def handle_slice(args: argparse.Namespace, console: Console | None = None) -> int:
    """Slice a range of pages from a source textbook PDF."""
    c = console or default_console
    settings, slicer = Settings(), PDFSlicer()

    try:
        src = resolve_source_book(
            explicit_book=args.book,
            raw_dir=settings.raw_dir,
            data_dir=settings.data_dir,
        )
    except (FileNotFoundError, ValueError) as err:
        c.print(f"[bold red]Error:[/bold red] {err}")
        return 1

    start_idx = 1 if getattr(args, "sequential", False) else getattr(args, "start_index", None)
    total_pages = max(0, args.end - args.start + 1)
    try:
        with create_slice_progress(console=c) as progress:
            task = progress.add_task(
                f"Slicing {src.name} [p.{args.start}-{args.end}]",
                total=total_pages,
            )
            files = slicer.slice_range(
                src_pdf=src,
                start_page=args.start,
                end_page=args.end,
                output_dir=args.output_dir,
                start_index=start_idx,
                on_progress=lambda cur, tot, _: progress.update(task, completed=cur),
            )
        render_slice_summary(
            src.name, args.start, args.end, args.output_dir, files, console=c
        )
        return 0
    except (FileNotFoundError, IndexError, ValueError) as err:
        c.print(f"[bold red]Error slicing PDF:[/bold red] {err}")
        return 1
