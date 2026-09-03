"""Command handler implementations for spc CLI commands."""

import argparse
from pathlib import Path

from rich.console import Console

from src.config import Settings
from src.engine.executor import TransformationExecutor
from src.engine.gemini_client import GeminiClient
from src.ingestion.input_resolver import resolve_input_path, resolve_source_book
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
    render_inspection_gate,
    render_slice_summary,
    render_status_dashboard,
)


def handle_run(args: argparse.Namespace, console: Console | None = None) -> int:
    """Execute a transformation run for an input page."""
    c = console or default_console
    settings, tracker = Settings(), RunTracker()
    session_mgr, slicer = SessionManager(), PDFSlicer()

    run_id = args.run_id or tracker.get_next_run_id()
    res = resolve_phase(override_phase=args.phase)
    try:
        input_path = resolve_input_path(
            explicit_page=args.page,
            run_id=run_id,
            inputs_dir=settings.inputs_dir,
        )
    except (FileNotFoundError, IndexError) as err:
        c.print(f"[bold red]Error:[/bold red] {err}")
        return 1

    if not settings.gemini_api_key:
        c.print("[bold red]Error:[/bold red] GEMINI_API_KEY is not configured.")
        return 1

    if input_path.suffix.lower() == ".pdf":
        page_text, word_count = slicer.extract_text_and_density(input_path)
    else:
        page_text = input_path.read_text(encoding="utf-8")
        word_count = len(page_text.split())

    turn_count = session_mgr.get_history_turn_count()
    render_header(
        operator=settings.operator_name, phase=res.phase.value,
        run_id=run_id, input_file=input_path.name,
        factor_x1=res.factor_x1, factor_x2=res.factor_x2,
        turn_count=turn_count, console=c,
    )
    c.print(f"  [1/3] Slicing & Input Verification ... [green]OK[/green] ({word_count} words)")

    client = GeminiClient(api_key=settings.gemini_api_key, model_name=settings.gemini_model)
    executor = TransformationExecutor(
        gemini_client=client, session_manager=session_mgr,
        csv_logger=CSVLogger(), audit_logger=AuditLogger(),
        webhook_client=WebhookClient(webhook_url=settings.sheet_webhook_url),
    )

    result = executor.execute_run(
        run_id=run_id, page_text=page_text, input_filename=input_path.name,
        phase=res.phase.value, factor_x1=res.factor_x1, factor_x2=res.factor_x2,
        operator=settings.operator_name, max_reworks=args.reworks,
        assignable_cause=args.cause, has_math_in_input=args.math,
    )

    c.print(
        f"  [2/3] Dispatching to Gemini Engine ... [green]DONE[/green] "
        f"(Cycle Time: {result.record.cycle_time_sec:.2f}s)"
    )
    render_inspection_gate(result.defect_report, console=c)
    render_execution_summary(result, cloud_synced=bool(settings.sheet_webhook_url), console=c)
    return 0


def handle_status(args: argparse.Namespace, console: Console | None = None) -> int:
    """Display project progress, active phase, and session turns."""
    c = console or default_console
    tracker, session_mgr = RunTracker(), SessionManager()

    try:
        res = resolve_phase()
        phase_str, x1, x2 = res.phase.value, res.factor_x1, res.factor_x2
    except ValueError:
        phase_str, x1, x2 = "Outside Window", 0, 0

    render_status_dashboard(
        phase=phase_str, factor_x1=x1, factor_x2=x2,
        total_runs=tracker.get_total_runs(), next_run_id=tracker.get_next_run_id(),
        turn_count=session_mgr.get_history_turn_count(),
        last_run=tracker.get_last_run(), console=c,
    )
    return 0


def handle_slice(args: argparse.Namespace, console: Console | None = None) -> int:
    """Slice a range of pages from a source textbook PDF."""
    c = console or default_console
    settings, slicer = Settings(), PDFSlicer()

    try:
        src = resolve_source_book(
            explicit_book=args.book, raw_dir=settings.raw_dir, data_dir=settings.data_dir,
        )
    except (FileNotFoundError, ValueError) as err:
        c.print(f"[bold red]Error:[/bold red] {err}")
        return 1

    start_idx = 1 if getattr(args, "sequential", False) else getattr(args, "start_index", None)
    try:
        files = slicer.slice_range(
            src_pdf=src, start_page=args.start, end_page=args.end,
            output_dir=args.output_dir, start_index=start_idx,
        )
        render_slice_summary(
            src.name, args.start, args.end, args.output_dir, files, console=c
        )
        return 0
    except (FileNotFoundError, IndexError, ValueError) as err:
        c.print(f"[bold red]Error slicing PDF:[/bold red] {err}")
        return 1
