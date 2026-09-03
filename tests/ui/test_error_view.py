"""Unit tests for error_view terminal rendering module."""

from rich.console import Console

from src.ui.error_view import render_api_error


class MockAPIError(Exception):
    def __init__(self, message: str, code: int | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def test_render_api_error_503() -> None:
    """Verify render_api_error formats 503 high-demand error correctly."""
    console = Console(record=True)
    err = MockAPIError(message="Model overloaded", code=503)

    render_api_error(err, console=console)
    output = console.export_text()
    assert "HTTP 503 — High Demand" in output
    assert "temporary high demand" in output
    assert "spc run" in output
    assert "Quota Protected" in output


def test_render_api_error_429() -> None:
    """Verify render_api_error formats 429 rate limit error correctly."""
    console = Console(record=True)
    err = MockAPIError(message="Rate limit exceeded", code=429)

    render_api_error(err, console=console)
    output = console.export_text()
    assert "HTTP 429" in output
    assert "Rate Limit Exceeded" in output
    assert "rate limit window" in output


def test_render_api_error_generic() -> None:
    """Verify render_api_error formats unexpected errors with and without status code."""
    console = Console(record=True)
    err_generic = RuntimeError("Connection dropped unexpectedly")

    render_api_error(err_generic, console=console)
    output_generic = console.export_text()
    assert "Gemini Engine Dispatch Failed" in output_generic
    assert "Connection dropped unexpectedly" in output_generic

    console_with_code = Console(record=True)
    err_coded = MockAPIError(message="Unauthorized", code=401)
    render_api_error(err_coded, console=console_with_code)
    output_coded = console_with_code.export_text()
    assert "HTTP 401" in output_coded
