"""Unit tests for UI command handlers."""

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.core.models import AuditPayload, DefectReport, ExecutionResult, RunRecord
from src.ui.cli import build_parser
from src.ui.handlers import handle_run, handle_slice, handle_status


def test_handle_status_inside_and_outside_window(tmp_path: Path, monkeypatch) -> None:
    """Verify handle_status works for inside and outside calendar window."""
    monkeypatch.chdir(tmp_path)
    parser = build_parser()
    args = parser.parse_args(["status"])

    assert handle_status(args) == 0

    with patch(
        "src.ui.handlers.resolve_phase",
        side_effect=ValueError("Outside window"),
    ):
        assert handle_status(args) == 0


def test_handle_slice_success_and_errors(tmp_path: Path) -> None:
    """Verify handle_slice processes valid slicing and handles errors."""
    parser = build_parser()

    # Error case
    args_fail = parser.parse_args(
        ["slice", "-b", str(tmp_path / "missing.pdf"), "-s", "1", "-e", "2"]
    )
    assert handle_slice(args_fail) == 1

    # Success case
    from tests.ingestion.test_pdf_slicer import make_test_pdf

    pdf_path = make_test_pdf(tmp_path / "textbook.pdf", page_count=2)
    out_dir = tmp_path / "out"
    args_ok = parser.parse_args(
        ["slice", "-b", str(pdf_path), "-s", "1", "-e", "2", "-o", str(out_dir)]
    )
    assert handle_slice(args_ok) == 0


def test_handle_run_missing_file_and_missing_key(
    tmp_path: Path, monkeypatch
) -> None:
    """Verify error returns for missing input file and unconfigured API key."""
    monkeypatch.chdir(tmp_path)
    parser = build_parser()

    # Missing input file
    args_missing_file = parser.parse_args(
        ["run", "--page", str(tmp_path / "none.pdf"), "--phase", "Phase_I"]
    )
    assert handle_run(args_missing_file) == 1

    # Missing API key
    input_file = tmp_path / "in.txt"
    input_file.write_text("Hello text", encoding="utf-8")
    monkeypatch.setenv("GEMINI_API_KEY", "")

    args_no_key = parser.parse_args(
        ["run", "--page", str(input_file), "--phase", "Phase_I"]
    )
    assert handle_run(args_no_key) == 1


def test_handle_run_success(tmp_path: Path, monkeypatch) -> None:
    """Verify successful handle_run execution and view rendering."""
    from tests.ingestion.test_pdf_slicer import make_test_pdf

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    pdf_input = make_test_pdf(tmp_path / "page_001.pdf", page_count=1)

    parser = build_parser()
    args = parser.parse_args(
        ["run", "--page", str(pdf_input), "--phase", "Phase_I", "--run-id", "1"]
    )

    mock_record = RunRecord(
        timestamp=datetime.now(UTC),
        run_id=1,
        phase="Phase_I",
        factor_x1=0,
        factor_x2=0,
        cycle_time_sec=3.5,
        prompt_tokens=100,
        output_tokens=80,
        conforming=1,
        rework_cycles=0,
        operator="analyst_test",
    )
    mock_audit = AuditPayload(
        run_id=1,
        timestamp="2026-09-02T10:00:00Z",
        phase="Phase_I",
        operator="analyst_test",
        input_file=pdf_input.name,
        final_output_markdown="Doc",
        total_cycle_time_sec=3.5,
        rework_count=0,
        conforming=True,
    )
    mock_result = ExecutionResult(
        record=mock_record,
        defect_report=DefectReport(is_conforming=True),
        output_markdown="Doc",
        audit_payload=mock_audit,
    )

    with (
        patch("src.ui.handlers.GeminiClient", return_value=MagicMock()),
        patch(
            "src.ui.handlers.TransformationExecutor.execute_run",
            return_value=mock_result,
        ),
    ):
        assert handle_run(args) == 0
