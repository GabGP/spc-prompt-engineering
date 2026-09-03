"""UI package: Rich terminal presentation views, CLI handlers, and routing."""

from src.ui.cli import app
from src.ui.handlers import handle_run, handle_slice, handle_status
from src.ui.views import (
    render_execution_summary,
    render_header,
    render_inspection_gate,
    render_slice_summary,
    render_status_dashboard,
)

__all__ = [
    "app",
    "handle_run",
    "handle_slice",
    "handle_status",
    "render_execution_summary",
    "render_header",
    "render_inspection_gate",
    "render_slice_summary",
    "render_status_dashboard",
]
