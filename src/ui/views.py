"""Standardized Rich terminal layout views, status cards, and inspection badges."""

from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from src.core.models import DefectReport, ExecutionResult

default_console = Console()

PHASE_DESCRIPTIONS: dict[str, str] = {
    "Phase_I": "Phase_I (Baseline Observation)",
    "Phase_II": "Phase_II (Context Reset Isolation)",
    "Phase_III": "Phase_III (SOP Schema Scaffolding)",
    "Phase_IV": "Phase_IV (Capability & Control Limits)",
}


def render_header(
    operator: str, phase: str, run_id: int, input_file: str,
    factor_x1: int, factor_x2: int, turn_count: int = 0,
    context_tokens: int = 0, console: Console | None = None,
) -> None:
    """Render standardized SPC operational banner and parameters."""
    c = console or default_console
    x1_desc = "1 (Daily Reset)" if factor_x1 else "0 (Accumulating Buffer)"
    x2_desc = "1 (SOP Schema Injection)" if factor_x2 else "0 (Bare / Ad-Hoc Prompt)"
    content = (
        f"[bold]Operator:[/bold]   {operator:<20} [bold]Phase:[/bold] {PHASE_DESCRIPTIONS.get(phase, phase)}\n"
        f"[bold]Target Run:[/bold] #{run_id:03d}{'':<16} [bold]Input:[/bold] {input_file}\n"
        f"[bold]Factor X1:[/bold]  {x1_desc:<20} [bold]Factor X2:[/bold] {x2_desc}\n"
        f"[bold]WIP Buffer:[/bold] {turn_count} turns in cache ({context_tokens:,} context tokens)"
    )
    c.print(Panel(content, title=Text("SPC TRANSFORMATION ENGINE", style="bold cyan"), border_style="cyan"))


def render_inspection_gate(
    defect_report: DefectReport, console: Console | None = None
) -> None:
    """Display standardized 3-gate deterministic inspection breakdown."""
    c = console or default_console
    st = "[bold green]PASS[/bold green]" if defect_report.is_conforming else "[bold red]DEFECT DETECTED[/bold red]"
    c.print(f"  [3/3] Quality Inspection Gate ... {st}")
    h_msg = "[green]OK[/green]" if not defect_report.missing_headers else f"[red]FAIL (Missing {', '.join(defect_report.missing_headers)})[/red]"
    l_msg = "[green]OK[/green]" if not defect_report.unclosed_latex else "[red]FAIL (Unclosed $$ blocks)[/red]"
    e_msg = "[green]OK[/green]" if not defect_report.empty_rule_violated else "[red]FAIL (Missing 'NONE RECORDED')[/red]"
    c.print(f"        * Structural Completeness: {h_msg}")
    c.print(f"        * LaTeX Syntactical Check: {l_msg}")
    c.print(f"        * Empty Handling Rule:     {e_msg}")


def render_execution_summary(
    result: ExecutionResult, cloud_synced: bool = False, console: Console | None = None,
) -> None:
    """Display standardized execution telemetry and ledger destinations."""
    c = console or default_console
    table = Table(title="Execution Telemetry & Artifact Ledger", border_style="cyan")
    table.add_column("Parameter", style="bold")
    table.add_column("Value", style="green")

    r = result.record
    table.add_row("Primary Metric (Y: Cycle Time T)", f"{r.cycle_time_sec:.4f} s")
    table.add_row("Context Tokens (WIP X1)", f"{r.context_tokens:,}")
    table.add_row("Instruction Tokens (Schema X2)", f"{r.instruction_tokens:,}")
    table.add_row("Page Tokens (Raw Input I)", f"{r.page_tokens:,}")
    table.add_row("Framing Tokens (API Protocol)", f"{r.framing_tokens:,}")
    table.add_row("Prompt Tokens (Total API Input W)", f"{r.prompt_tokens:,}")
    table.add_row("Output Tokens (Response O)", f"{r.output_tokens:,}")
    table.add_row("Total Tokens Processed", f"{r.total_tokens:,}")
    table.add_row("Rework Iterations (P)", str(r.rework_cycles))
    st_style = "bold green" if r.conforming else "bold red"
    st_text = "PASS (Conforming)" if r.conforming else "DEFECT (Non-conforming)"
    table.add_row("Quality Status", Text(st_text, style=st_style))
    table.add_row("API Finish Reason", r.finish_reason)
    table.add_row("Model Version", r.model_version)
    table.add_row("CSV Ledger", f"data/main_event_log.csv [Row #{r.run_id}]")
    table.add_row("Audit Log", f"data/logs/run_{r.run_id:03d}_audit.json")
    table.add_row("Output Document", f"data/outputs/run_{r.run_id:03d}.md")
    sync_txt = Text("Updated" if cloud_synced else "Skipped / Offline", style="cyan" if cloud_synced else "dim")
    table.add_row("Cloud Webhook", sync_txt)
    c.print(table)


def render_status_dashboard(
    phase: str, factor_x1: int, factor_x2: int, total_runs: int,
    next_run_id: int, turn_count: int, last_run: dict[str, str] | None = None,
    context_tokens: int = 0, console: Console | None = None,
) -> None:
    """Render standardized project status overview dashboard."""
    c = console or default_console
    table = Table(title="SPC Project Operational Status", border_style="cyan")
    table.add_column("Parameter", style="bold")
    table.add_column("Current State", style="yellow")

    x1_desc = "1 (Daily Reset)" if factor_x1 else "0 (Accumulating Buffer)"
    x2_desc = "1 (SOP Schema Injection)" if factor_x2 else "0 (Bare / Ad-Hoc Prompt)"
    table.add_row("Active Calendar Phase", PHASE_DESCRIPTIONS.get(phase, phase))
    table.add_row("Factor X1 (Context Buffer)", x1_desc)
    table.add_row("Factor X2 (Prompt Schema)", x2_desc)
    table.add_row("Total Runs Completed", str(total_runs))
    table.add_row("Next Target Run ID", f"#{next_run_id:03d}")
    table.add_row("Active Cache Turns", f"{turn_count} turns ({context_tokens:,} tokens)")

    if last_run:
        f_name = f" ({last_run.get('input_file')})" if last_run.get("input_file") else ""
        summary = (
            f"Run #{last_run.get('run_id')}{f_name} | {last_run.get('phase')} | "
            f"T={last_run.get('cycle_time_sec')}s | "
            f"Conforming={last_run.get('conforming')} | P={last_run.get('rework_cycles')}"
        )
        table.add_row("Last Logged Run", summary)
    c.print(table)


def render_slice_summary(
    src_pdf: str,
    start_page: int,
    end_page: int,
    output_dir: str,
    created_files: list[Path],
    console: Console | None = None,
) -> None:
    """Render standardized completion table for PDF slicing operations."""
    c = console or default_console
    table = Table(title="PDF Slicing Operation Complete", border_style="cyan")
    table.add_column("Parameter", style="bold")
    table.add_column("Value", style="green")

    table.add_row("Source PDF", src_pdf)
    table.add_row("Page Range", f"Page {start_page} to {end_page} ({len(created_files)} pages)")
    table.add_row("Destination", output_dir)
    if created_files:
        sample = f"{created_files[0].name} ... {created_files[-1].name}"
        table.add_row("Sliced Artifacts", f"{sample} ({len(created_files)} files)")
    c.print(table)
