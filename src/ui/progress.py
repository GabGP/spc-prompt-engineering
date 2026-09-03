"""Progress bar utilities and configurations for CLI operations."""

from collections.abc import Callable
from pathlib import Path

from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

from src.ui.views import default_console

ProgressCallback = Callable[[int, int, Path], None]


def create_slice_progress(console: Console | None = None) -> Progress:
    """Create a standardized Rich Progress bar instance for slicing tasks."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]{task.description}"),
        BarColumn(bar_width=25),
        TaskProgressColumn(),
        MofNCompleteColumn(),
        TextColumn("|"),
        TimeElapsedColumn(),
        TextColumn("| ETA:"),
        TimeRemainingColumn(),
        console=console or default_console,
        transient=False,
    )
