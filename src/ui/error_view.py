"""Terminal presentation for external API errors, rate limit cards, and service status."""

from rich.console import Console
from rich.panel import Panel

default_console = Console()


def render_api_error(
    error: Exception, console: Console | None = None
) -> None:
    """Render standardized error card when external LLM API dispatch fails."""
    c = console or default_console
    status_code = getattr(error, "code", None)
    raw_message = getattr(error, "message", str(error)) or str(error)

    if status_code == 503 or "503" in str(error) or "UNAVAILABLE" in str(error):
        title = "[bold red]Gemini Engine Unavailable (HTTP 503 — High Demand)[/bold red]"
        explanation = (
            "The model is currently experiencing temporary high demand upstream on Google's servers."
        )
        suggestions = [
            "Wait 30–60 seconds for the spike to clear, then rerun: [cyan]spc run[/cyan]",
            "Keep the same model to maintain statistical process control (SPC) validity.",
            "Test offline without API usage or quota impact: [cyan]spc run --mock rework[/cyan]",
        ]
    elif status_code == 429 or "429" in str(error) or "RESOURCE_EXHAUSTED" in str(error):
        title = "[bold red]Gemini API Rate Limit Exceeded (HTTP 429)[/bold red]"
        explanation = (
            "The request quota (RPM or RPD) for this model was exceeded."
        )
        suggestions = [
            "Wait for your rate limit window or daily quota to reset.",
            "Verify pipeline offline (zero quota consumed): [cyan]spc run --mock rework[/cyan]",
        ]
    else:
        code_str = f" (HTTP {status_code})" if status_code else ""
        title = f"[bold red]Gemini Engine Dispatch Failed{code_str}[/bold red]"
        explanation = f"An unexpected API error occurred:\n[yellow]{raw_message}[/yellow]"
        suggestions = [
            "Check your internet connection and API key configuration in [cyan].env[/cyan].",
            "Verify pipeline offline: [cyan]spc run --mock rework[/cyan]",
        ]

    bullets = "\n".join(f"  • {s}" for s in suggestions)
    content = (
        f"[bold white]{explanation}[/bold white]\n\n"
        f"[dim]Upstream response: {raw_message}[/dim]\n\n"
        f"[bold cyan]Process Control & Quota Stewardship:[/bold cyan]\n"
        f"  • [green]Safe State:[/green] Zero runs recorded to CSV; session cache uncontaminated.\n"
        f"  • [green]Quota Protected:[/green] Automatic retry loop bypassed to conserve your RPD quota.\n\n"
        f"[bold white]Recommended Actions:[/bold white]\n{bullets}"
    )
    c.print()
    c.print(Panel(content, title=title, border_style="red"))
