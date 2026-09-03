"""Unit tests for CLI parser and dispatch entrypoint."""

from pathlib import Path
from unittest.mock import patch

from src.ui.cli import app, build_parser


def test_build_parser() -> None:
    """Verify subcommands and argument flags are configured."""
    parser = build_parser()
    assert parser.prog == "spc"

    # Test run arguments
    run_args = parser.parse_args(["run", "--page", "p1.pdf", "--phase", "Phase_I", "--math"])
    assert run_args.page == "p1.pdf"
    assert run_args.phase == "Phase_I"
    assert run_args.math is True

    # Test slice arguments
    slice_args = parser.parse_args(
        ["slice", "-b", "book.pdf", "-s", "1", "-e", "10", "-o", "data/inputs", "--sequential", "--start-index", "1"]
    )
    assert slice_args.book == "book.pdf"
    assert slice_args.start == 1
    assert slice_args.end == 10
    assert slice_args.sequential is True
    assert slice_args.start_index == 1

    # Test status arguments
    status_args = parser.parse_args(["status"])
    assert status_args.command == "status"


def test_app_without_subcommand() -> None:
    """Verify app prints help and returns 0 when called without subcommands."""
    assert app([]) == 0


def test_app_dispatches_to_handlers() -> None:
    """Verify app routes to the corresponding handler functions."""
    with patch("src.ui.cli.handle_status", return_value=0) as mock_status:
        assert app(["status"]) == 0
        mock_status.assert_called_once()

    with patch("src.ui.cli.handle_slice", return_value=0) as mock_slice:
        assert app(["slice", "-b", "b.pdf", "-s", "1", "-e", "2"]) == 0
        mock_slice.assert_called_once()

    with patch("src.ui.cli.handle_run", return_value=0) as mock_run:
        assert app(["run", "--page", "p.pdf"]) == 0
        mock_run.assert_called_once()

    with patch("src.ui.cli.handle_rebuild_cache", return_value=0) as mock_rebuild:
        assert app(["rebuild-cache"]) == 0
        mock_rebuild.assert_called_once()


def test_rebuild_cache_subcommand(tmp_path: Path) -> None:
    """Verify rebuild-cache command parses arguments."""
    parser = build_parser()
    args = parser.parse_args(["rebuild-cache", "--phase", "Phase_I", "--logs-dir", str(tmp_path)])
    assert args.command == "rebuild-cache"
    assert args.phase == "Phase_I"
    assert args.logs_dir == str(tmp_path)


def test_handle_rebuild_cache_execution(tmp_path: Path, monkeypatch) -> None:
    """Verify handle_rebuild_cache executes and outputs success."""
    import argparse
    import json

    from src.ui.handlers import handle_rebuild_cache

    monkeypatch.chdir(tmp_path)
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir(parents=True)
    audit = {"run_id": 1, "phase": "Phase_I", "request_prompt": "P", "final_output_markdown": "O"}
    (logs_dir / "run_001_audit.json").write_text(json.dumps(audit), encoding="utf-8")

    args = argparse.Namespace(phase="Phase_I", logs_dir=str(logs_dir))
    assert handle_rebuild_cache(args) == 0
