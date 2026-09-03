"""Rich terminal layout views, status cards, and inspection badges."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from src.core.models import DefectReport, ExecutionResult

default_console = Console()


def render_header(
    operator: str,
    phase: str,
    run_id: int,
    input_file: str,
    factor_x1: int,
    factor_x2: int,
    turn_count: int = 0,
    console: Console | None = None,
) -> None:
    """Render the main SPC operational execution banner and parameters."""
    c = console or default_console
    title = Text("SPC TRANSFORMATION ENGINE", style="bold cyan")
    content = (
        f"[bold]Operator:[/bold] {operator:<18} [bold]Phase:[/bold] {phase}\n"
        f"[bold]Target Run:[/bold] #{run_id:03d}{'':<14} [bold]Input:[/bold] {input_file}\n"
        f"[bold]Factor X1 (Buffer):[/bold] {factor_x1} ({'Reset' if factor_x1 else 'Accumulating'})  "
        f"[bold]Factor X2 (Schema):[/bold] {factor_x2} ({'SOP Schema' if factor_x2 else 'Bare'})\n"
        f"[bold]Cached Turns in Buffer:[/bold] {turn_count}"
    )
    c.print(Panel(content, title=title, border_style="cyan"))


def render_inspection_results(
    defect_report: DefectReport, console: Console | None = None
) -> None:
    """Display the deterministic Go / No-Go quality gate inspection badge."""
    c = console or default_console
    if defect_report.is_conforming:
        c.print(
            "[bold green][PASS] Quality Gate PASS[/bold green] - All criteria"
            " satisfied."
        )
    else:
        c.print("[bold red][FAIL] Quality Gate FAIL (Defects Detected):[/bold red]")
        for reason in defect_report.defect_reasons:
            c.print(f"  [red]* {reason}[/red]")


def render_execution_summary(
    result: ExecutionResult, console: Console | None = None
) -> None:
    """Display final execution telemetry, cycle time, and output destinations."""
    c = console or default_console
    table = Table(title="Execution Telemetry", border_style="dim")
    table.add_column("Metric", style="bold")
    table.add_column("Value", style="green")

    table.add_row("Cycle Time (T)", f"{result.record.cycle_time_sec:.4f} s")
    table.add_row("Prompt Tokens", str(result.record.prompt_tokens))
    table.add_row("Output Tokens", str(result.record.output_tokens))
    table.add_row("Rework Iterations (P)", str(result.record.rework_cycles))
    status_style = "bold green" if result.record.conforming else "bold red"
    table.add_row("Conforming Status", Text("PASS" if result.record.conforming else "DEFECT", style=status_style))
    table.add_row("CSV Ledger", "data/main_event_log.csv")
    table.add_row("Audit Log", f"data/logs/run_{result.record.run_id:03d}_audit.json")
    table.add_row("Output Document", f"data/outputs/run_{result.record.run_id:03d}.md")

    c.print(table)


def render_status_dashboard(
    phase: str,
    factor_x1: int,
    factor_x2: int,
    total_runs: int,
    next_run_id: int,
    turn_count: int,
    last_run: dict[str, str] | None = None,
    console: Console | None = None,
) -> None:
    """Render the project status overview dashboard."""
    c = console or default_console
    table = Table(title="SPC Project Operational Status", border_style="cyan")
    table.add_column("Parameter", style="bold")
    table.add_column("Current State", style="yellow")

    table.add_row("Active Phase", phase)
    table.add_row("Factor X1 (Context Buffer)", f"{factor_x1} ({'Reset' if factor_x1 else 'Accumulating'})")
    table.add_row("Factor X2 (Prompt Schema)", f"{factor_x2} ({'SOP Scaffolding' if factor_x2 else 'Bare Prompt'})")
    table.add_row("Total Runs Logged", str(total_runs))
    table.add_row("Next Target Run ID", f"#{next_run_id:03d}")
    table.add_row("Active Cache Turns", str(turn_count))

    if last_run:
        summary = (
            f"Run #{last_run.get('run_id')} | {last_run.get('phase')} | "
            f"T={last_run.get('cycle_time_sec')}s | "
            f"Conforming={last_run.get('conforming')} | P={last_run.get('rework_cycles')}"
        )
        table.add_row("Last Logged Run", summary)

    c.print(table)
