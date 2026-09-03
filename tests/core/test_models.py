"""Unit tests for spc.core.models."""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError
from src.core.models import (
    AuditPayload,
    DefectReport,
    ExecutionResult,
    RunRecord,
)


def test_defect_report_conforming() -> None:
    """Verify conforming DefectReport behavior."""
    report = DefectReport(is_conforming=True)
    assert not report.has_defects
    assert report.format_diagnostic_bullets() == "- No defects recorded."


def test_defect_report_with_defects() -> None:
    """Verify non-conforming DefectReport diagnostics formatting."""
    report = DefectReport(
        is_conforming=False,
        missing_headers=["## Core Synthesis"],
        unclosed_latex=True,
        defect_reasons=[
            "Missing header: ## Core Synthesis",
            "Unclosed LaTeX formula block ($$)",
        ],
    )
    assert report.has_defects
    bullets = report.format_diagnostic_bullets()
    assert "- Missing header: ## Core Synthesis" in bullets
    assert "- Unclosed LaTeX formula block ($$)" in bullets


def test_run_record_valid_and_csv_dict() -> None:
    """Verify RunRecord serialization to CSV-compatible dictionary."""
    now = datetime.now(timezone.utc)
    record = RunRecord(
        timestamp=now,
        run_id=1,
        phase="Phase_I",
        factor_x1=0,
        factor_x2=0,
        cycle_time_sec=6.123456,
        prompt_tokens=520,
        output_tokens=310,
        conforming=1,
        rework_cycles=0,
        assignable_cause="NONE",
        operator="test_analyst",
    )
    # Verify precision rounding
    assert record.cycle_time_sec == 6.1235

    row = record.to_csv_dict()
    assert row["run_id"] == 1
    assert row["phase"] == "Phase_I"
    assert row["factor_x1"] == 0
    assert row["factor_x2"] == 0
    assert row["cycle_time_sec"] == 6.1235
    assert row["conforming"] == 1
    assert row["operator"] == "test_analyst"


def test_run_record_validation_errors() -> None:
    """Verify invalid factor values and negative cycle times raise ValidationError."""
    with pytest.raises(ValidationError):
        RunRecord(
            run_id=1,
            phase="Phase_I",
            factor_x1=2,  # Invalid: must be 0 or 1
            factor_x2=0,
            cycle_time_sec=5.0,
            prompt_tokens=100,
            output_tokens=100,
            conforming=1,
            rework_cycles=0,
            operator="op",
        )

    with pytest.raises(ValidationError):
        RunRecord(
            run_id=1,
            phase="Phase_I",
            factor_x1=0,
            factor_x2=0,
            cycle_time_sec=-1.0,  # Invalid: must be > 0
            prompt_tokens=100,
            output_tokens=100,
            conforming=1,
            rework_cycles=0,
            operator="op",
        )


def test_audit_payload_and_execution_result() -> None:
    """Verify AuditPayload and ExecutionResult assembly."""
    record = RunRecord(
        run_id=5,
        phase="Phase_II",
        factor_x1=1,
        factor_x2=0,
        cycle_time_sec=4.25,
        prompt_tokens=400,
        output_tokens=250,
        conforming=1,
        rework_cycles=0,
        operator="analyst_2",
    )
    report = DefectReport(is_conforming=True)
    audit = AuditPayload(
        run_id=5,
        timestamp="2026-09-24T12:00:00Z",
        phase="Phase_II",
        operator="analyst_2",
        input_file="page_005.pdf",
        final_output_markdown="## Conforming Markdown",
        total_cycle_time_sec=4.25,
        rework_count=0,
        conforming=True,
    )
    result = ExecutionResult(
        record=record,
        defect_report=report,
        output_markdown="## Conforming Markdown",
        audit_payload=audit,
    )
    assert result.record.run_id == 5
    assert result.defect_report.is_conforming
    assert result.audit_payload.conforming
