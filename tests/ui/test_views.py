"""Unit tests for Rich terminal views and rendering formatting."""

from datetime import UTC, datetime
from pathlib import Path

from rich.console import Console

from src.core.models import AuditPayload, DefectReport, ExecutionResult, RunRecord
from src.ui.views import (
    render_execution_summary,
    render_header,
    render_inspection_gate,
    render_slice_summary,
    render_status_dashboard,
)


def test_render_header() -> None:
    """Verify operational header renders key execution parameters."""
    console = Console(record=True)
    render_header(
        operator="analyst_test",
        phase="Phase_I",
        run_id=5,
        input_file="page_005.pdf",
        factor_x1=0,
        factor_x2=0,
        turn_count=4,
        context_tokens=1500,
        console=console,
    )
    output = console.export_text()
    assert "SPC TRANSFORMATION ENGINE" in output
    assert "analyst_test" in output
    assert "Phase_I" in output
    assert "#005" in output
    assert "page_005.pdf" in output
    assert "1,500 context tokens" in output


def test_render_inspection_gate_pass_and_fail() -> None:
    """Verify inspection gate breakdown renders for pass and defect states."""
    console = Console(record=True)

    report_pass = DefectReport(is_conforming=True)
    render_inspection_gate(report_pass, console=console)
    output_pass = console.export_text()
    assert "Quality Inspection Gate ... PASS" in output_pass
    assert "Structural Completeness: OK" in output_pass
    assert "LaTeX Syntactical Check: OK" in output_pass
    assert "Empty Handling Rule:     OK" in output_pass

    console_fail = Console(record=True)
    report_fail = DefectReport(
        is_conforming=False,
        missing_headers=["## Core Synthesis"],
        unclosed_latex=True,
        empty_rule_violated=True,
        defect_reasons=["Missing header", "Unclosed $$", "Missing empty rule"],
    )
    render_inspection_gate(report_fail, console=console_fail)
    output_fail = console_fail.export_text()
    assert "DEFECT DETECTED" in output_fail
    assert "Missing ## Core Synthesis" in output_fail
    assert "Unclosed $$ blocks" in output_fail
    assert "Missing 'NONE RECORDED'" in output_fail


def test_render_execution_summary() -> None:
    """Verify execution telemetry table renders metrics."""
    console = Console(record=True)
    record = RunRecord(
        timestamp=datetime.now(UTC),
        run_id=1,
        phase="Phase_I",
        factor_x1=0,
        factor_x2=0,
        cycle_time_sec=5.1234,
        prompt_tokens=350,
        output_tokens=210,
        conforming=1,
        rework_cycles=0,
        operator="op",
    )
    audit = AuditPayload(
        run_id=1,
        timestamp="2026-09-02T10:00:00Z",
        phase="Phase_I",
        operator="op",
        input_file="p1.pdf",
        final_output_markdown="Doc",
        total_cycle_time_sec=5.1234,
        rework_count=0,
        conforming=True,
    )
    result = ExecutionResult(
        record=record,
        defect_report=DefectReport(is_conforming=True),
        output_markdown="Doc",
        audit_payload=audit,
    )

    render_execution_summary(result, cloud_synced=True, console=console)
    output = console.export_text()
    assert "Execution Telemetry" in output
    assert "5.1234 s" in output
    assert "350" in output
    assert "PASS" in output
    assert "Updated" in output


def test_render_status_dashboard() -> None:
    """Verify status dashboard table with and without last_run record."""
    console = Console(record=True)
    render_status_dashboard(
        phase="Phase_I",
        factor_x1=0,
        factor_x2=0,
        total_runs=10,
        next_run_id=11,
        turn_count=10,
        last_run={
            "run_id": "10",
            "phase": "Phase_I",
            "cycle_time_sec": "6.2",
            "conforming": "1",
            "rework_cycles": "0",
        },
        console=console,
    )
    output = console.export_text()
    assert "SPC Project Operational Status" in output
    assert "Phase_I" in output
    assert "#011" in output
    assert "Run #10" in output

    console_no_last = Console(record=True)
    render_status_dashboard(
        phase="Phase_II",
        factor_x1=1,
        factor_x2=0,
        total_runs=0,
        next_run_id=1,
        turn_count=0,
        last_run=None,
        console=console_no_last,
    )
    output_no_last = console_no_last.export_text()
    assert "Phase_II" in output_no_last


def test_render_slice_summary(tmp_path: Path) -> None:
    """Verify render_slice_summary displays source PDF and output artifacts."""
    console = Console(record=True)
    files = [tmp_path / "page_001.pdf", tmp_path / "page_002.pdf"]
    render_slice_summary(
        src_pdf="book.pdf",
        start_page=1,
        end_page=2,
        output_dir="data/inputs",
        created_files=files,
        console=console,
    )
    output = console.export_text()
    assert "PDF Slicing Operation Complete" in output
    assert "book.pdf" in output
    assert "page_001.pdf" in output



