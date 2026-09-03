"""Command handler implementations for spc CLI commands."""

import argparse
from pathlib import Path

from rich.console import Console

from src.config import Settings
from src.engine.executor import TransformationExecutor
from src.engine.gemini_client import GeminiClient
from src.ingestion.pdf_slicer import PDFSlicer
from src.persistence.audit_logger import AuditLogger
from src.persistence.csv_logger import CSVLogger
from src.persistence.webhook_client import WebhookClient
from src.state.phase_resolver import resolve_phase
from src.state.run_tracker import RunTracker
from src.state.session_manager import SessionManager
from src.ui.views import (
    default_console,
    render_execution_summary,
    render_header,
    render_inspection_results,
    render_status_dashboard,
)


def handle_run(args: argparse.Namespace, console: Console | None = None) -> int:
    """Execute a transformation run for an input page."""
    c = console or default_console
    settings = Settings()
    tracker = RunTracker()
    session_mgr = SessionManager()
    slicer = PDFSlicer()

    run_id = args.run_id or tracker.get_next_run_id()
    resolution = resolve_phase(override_phase=args.phase)

    input_path = (
        Path(args.page)
        if args.page
        else Path(f"data/inputs/page_{run_id:03d}.pdf")
    )
    if not input_path.exists():
        c.print(f"[bold red]Error:[/bold red] Input file not found: {input_path}")
        return 1

    if input_path.suffix.lower() == ".pdf":
        page_text, _ = slicer.extract_text_and_density(input_path)
    else:
        page_text = input_path.read_text(encoding="utf-8")

    turn_count = session_mgr.get_history_turn_count()
    render_header(
        operator=settings.operator_name,
        phase=resolution.phase.value,
        run_id=run_id,
        input_file=input_path.name,
        factor_x1=resolution.factor_x1,
        factor_x2=resolution.factor_x2,
        turn_count=turn_count,
        console=c,
    )

    if not settings.gemini_api_key:
        c.print("[bold red]Error:[/bold red] GEMINI_API_KEY is not configured.")
        return 1

    client = GeminiClient(
        api_key=settings.gemini_api_key, model_name=settings.gemini_model
    )
    executor = TransformationExecutor(
        gemini_client=client,
        session_manager=session_mgr,
        csv_logger=CSVLogger(),
        audit_logger=AuditLogger(),
        webhook_client=WebhookClient(webhook_url=settings.sheet_webhook_url),
    )

    result = executor.execute_run(
        run_id=run_id,
        page_text=page_text,
        input_filename=input_path.name,
        phase=resolution.phase.value,
        factor_x1=resolution.factor_x1,
        factor_x2=resolution.factor_x2,
        operator=settings.operator_name,
        max_reworks=args.reworks,
        assignable_cause=args.cause,
        has_math_in_input=args.math,
    )

    render_inspection_results(result.defect_report, console=c)
    render_execution_summary(result, console=c)
    return 0


def handle_status(args: argparse.Namespace, console: Console | None = None) -> int:
    """Display project progress, active phase, and session turns."""
    c = console or default_console
    tracker = RunTracker()
    session_mgr = SessionManager()

    try:
        resolution = resolve_phase()
        phase_str, x1, x2 = (
            resolution.phase.value,
            resolution.factor_x1,
            resolution.factor_x2,
        )
    except ValueError:
        phase_str, x1, x2 = "Outside Window", 0, 0

    render_status_dashboard(
        phase=phase_str,
        factor_x1=x1,
        factor_x2=x2,
        total_runs=tracker.get_total_runs(),
        next_run_id=tracker.get_next_run_id(),
        turn_count=session_mgr.get_history_turn_count(),
        last_run=tracker.get_last_run(),
        console=c,
    )
    return 0


def handle_slice(args: argparse.Namespace, console: Console | None = None) -> int:
    """Slice a range of pages from a source textbook PDF."""
    c = console or default_console
    slicer = PDFSlicer()
    try:
        files = slicer.slice_range(
            src_pdf=args.book,
            start_page=args.start,
            end_page=args.end,
            output_dir=args.output_dir,
        )
        c.print(
            f"[bold green]✔ Sliced {len(files)} pages into {args.output_dir}[/bold green]"
        )
        return 0
    except (FileNotFoundError, IndexError, ValueError) as err:
        c.print(f"[bold red]Error slicing PDF:[/bold red] {err}")
        return 1
