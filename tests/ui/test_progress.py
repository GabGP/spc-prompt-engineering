"""Unit tests for UI progress bar factory."""

import io

from rich.console import Console

from src.ui.progress import create_slice_progress


def test_create_slice_progress_default_console() -> None:
    """Verify create_slice_progress instantiates a valid Progress object."""
    progress = create_slice_progress()
    assert progress is not None
    assert len(progress.columns) > 0


def test_create_slice_progress_custom_console_and_execution() -> None:
    """Verify progress updates tasks correctly to custom console stream."""
    buf = io.StringIO()
    custom_console = Console(file=buf, force_terminal=True, width=120)
    progress = create_slice_progress(console=custom_console)

    with progress:
        task_id = progress.add_task("Test task", total=5)
        for _ in range(5):
            progress.advance(task_id, 1)

    output = buf.getvalue()
    assert "Test task" in output
    assert "5/5" in output
