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


def test_handle_slice_success_and_errors(tmp_path: Path, monkeypatch) -> None:
    """Verify handle_slice processes valid slicing, auto-detection, and handles errors."""
    monkeypatch.chdir(tmp_path)
    from tests.ingestion.test_pdf_slicer import make_test_pdf

    parser = build_parser()

    # Error: missing file explicitly passed
    args_fail = parser.parse_args(
        ["slice", "-b", str(tmp_path / "missing.pdf"), "-s", "1", "-e", "2"]
    )
    assert handle_slice(args_fail) == 1

    # Error: no -b and no PDFs in data/raw
    raw_dir = tmp_path / "data" / "raw"
    raw_dir.mkdir(parents=True)
    args_no_b = parser.parse_args(["slice", "-s", "1", "-e", "2"])
    assert handle_slice(args_no_b) == 1

    # Error: no -b and multiple PDFs in data/raw
    make_test_pdf(raw_dir / "b1.pdf", page_count=1)
    make_test_pdf(raw_dir / "b2.pdf", page_count=1)
    assert handle_slice(args_no_b) == 1

    # Success: auto-detect single PDF in data/raw
    (raw_dir / "b2.pdf").unlink()
    out_dir = tmp_path / "out"
    args_auto = parser.parse_args(["slice", "-s", "1", "-e", "1", "-o", str(out_dir)])
    assert handle_slice(args_auto) == 0

    # Success: explicit -b
    pdf_path = make_test_pdf(tmp_path / "textbook.pdf", page_count=2)
    args_ok = parser.parse_args(
        ["slice", "-b", str(pdf_path), "-s", "1", "-e", "2", "-o", str(out_dir)]
    )
    assert handle_slice(args_ok) == 0

    # Error: invalid page range
    args_range_err = parser.parse_args(
        ["slice", "-b", str(pdf_path), "-s", "10", "-e", "20", "-o", str(out_dir)]
    )
    assert handle_slice(args_range_err) == 1


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
    """Verify successful handle_run execution with PDF input."""
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


def test_handle_run_with_text_file(tmp_path: Path, monkeypatch) -> None:
    """Verify successful handle_run execution with text input."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    txt_input = tmp_path / "input.txt"
    txt_input.write_text("Plain text page content", encoding="utf-8")

    parser = build_parser()
    args = parser.parse_args(["run", "--page", str(txt_input), "--phase", "Phase_I"])

    mock_record = RunRecord(
        timestamp=datetime.now(UTC),
        run_id=2,
        phase="Phase_I",
        factor_x1=0,
        factor_x2=0,
        cycle_time_sec=2.1,
        prompt_tokens=50,
        output_tokens=40,
        conforming=1,
        rework_cycles=0,
        operator="op",
    )
    mock_audit = AuditPayload(
        run_id=2,
        timestamp="2026-09-02T10:00:00Z",
        phase="Phase_I",
        operator="op",
        input_file=txt_input.name,
        final_output_markdown="Doc",
        total_cycle_time_sec=2.1,
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


def test_handle_run_auto_discovers_in_order(tmp_path: Path, monkeypatch) -> None:
    """Verify handle_run picks input by natural order when --page is not provided."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    in_dir = tmp_path / "data" / "inputs"
    in_dir.mkdir(parents=True)
    # Sliced files starting at page 002
    (in_dir / "page_002.txt").write_text("Page 2 text content", encoding="utf-8")

    parser = build_parser()
    args = parser.parse_args(["run", "--phase", "Phase_I"])

    mock_record = RunRecord(
        timestamp=datetime.now(UTC),
        run_id=1,
        phase="Phase_I",
        factor_x1=0,
        factor_x2=0,
        cycle_time_sec=1.0,
        prompt_tokens=100,
        output_tokens=80,
        conforming=1,
        rework_cycles=0,
        operator="op",
    )
    mock_audit = AuditPayload(
        run_id=1,
        timestamp="2026-09-02T10:00:00Z",
        phase="Phase_I",
        operator="op",
        input_file="page_002.txt",
        final_output_markdown="Doc",
        total_cycle_time_sec=1.0,
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
        ) as mock_exec,
    ):
        assert handle_run(args) == 0
        assert mock_exec.call_args.kwargs["input_filename"] == "page_002.txt"


def test_handle_run_with_mock_rework(tmp_path: Path, monkeypatch) -> None:
    """Verify handle_run executes offline with staged mock rework scenario."""
    monkeypatch.chdir(tmp_path)
    in_dir = tmp_path / "data" / "inputs"
    in_dir.mkdir(parents=True)
    (in_dir / "page_001.txt").write_text("Test content for transformation", encoding="utf-8")

    parser = build_parser()
    args = parser.parse_args(["run", "--mock", "rework", "--phase", "Phase_I"])
    assert handle_run(args) == 0
    assert (tmp_path / "data" / "main_event_log.csv").exists()
    assert (tmp_path / "data" / "logs" / "run_001_audit.json").exists()
    assert (tmp_path / "data" / "outputs" / "run_001.md").exists()


def test_handle_run_api_error_returns_one(tmp_path: Path, monkeypatch) -> None:
    """Verify handle_run catches execution errors, renders error card, and returns 1."""
    monkeypatch.chdir(tmp_path)
    in_dir = tmp_path / "data" / "inputs"
    in_dir.mkdir(parents=True)
    (in_dir / "page_001.txt").write_text("Sample input text", encoding="utf-8")

    parser = build_parser()
    args = parser.parse_args(["run", "--mock", "pass", "--phase", "Phase_I"])

    with patch(
        "src.ui.handlers.TransformationExecutor.execute_run",
        side_effect=RuntimeError("503 UNAVAILABLE: Model overloaded"),
    ):
        assert handle_run(args) == 1


