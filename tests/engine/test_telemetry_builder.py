"""Unit tests for TelemetryBuilder token arithmetic and payload assembly."""

from src.core.models import DefectReport, IterationRecord
from src.engine.telemetry_builder import TelemetryBuilder


def test_calculate_framing_tokens() -> None:
    """Verify framing tokens calculation subtracts base inputs and floors at zero."""
    framing = TelemetryBuilder.calculate_framing_tokens(
        initial_prompt_tokens=440,
        context_tokens=100,
        instruction_tokens=30,
        page_tokens=300,
    )
    assert framing == 10

    # Floors at zero if initial prompt is smaller than base inputs
    zero_framing = TelemetryBuilder.calculate_framing_tokens(
        initial_prompt_tokens=200,
        context_tokens=100,
        instruction_tokens=50,
        page_tokens=100,
    )
    assert zero_framing == 0


def test_build_run_record_first_pass() -> None:
    """Verify run record assembly when run succeeds on initial pass (rework=0)."""
    defect_report = DefectReport(is_conforming=True)
    record = TelemetryBuilder.build_run_record(
        run_id=1,
        phase="Phase_I",
        operator="analyst",
        model_ver="gemini-3.8-flash",
        input_filename="page_001.pdf",
        factor_x1=0,
        factor_x2=0,
        context_tokens=0,
        instruction_tokens=20,
        page_tokens=400,
        initial_prompt_tokens=438,
        final_prompt_tokens=438,
        final_output_tokens=250,
        defect_report=defect_report,
        rework_count=0,
        finish_reason="STOP",
        cycle_time=5.2345,
        assignable_cause="NONE",
    )

    assert record.run_id == 1
    assert record.framing_tokens == 18
    assert record.rework_tokens == 0
    assert record.prompt_tokens == 438
    assert record.output_tokens == 250
    assert record.total_tokens == 688
    assert record.conforming == 1
    assert record.rework_cycles == 0
    assert record.assignable_cause == "NONE"

    csv_dict = record.to_csv_dict()
    assert "rework_tokens" in csv_dict
    assert csv_dict["rework_tokens"] == 0


def test_build_run_record_with_rework() -> None:
    """Verify rework_tokens calculation and assignable cause mapping for non-STOP finish."""
    defect_report = DefectReport(is_conforming=True)
    record = TelemetryBuilder.build_run_record(
        run_id=2,
        phase="Phase_I",
        operator="analyst",
        model_ver="gemini-3.8-flash",
        input_filename="page_002.pdf",
        factor_x1=0,
        factor_x2=0,
        context_tokens=0,
        instruction_tokens=20,
        page_tokens=400,
        initial_prompt_tokens=438,
        final_prompt_tokens=1950,
        final_output_tokens=300,
        defect_report=defect_report,
        rework_count=1,
        finish_reason="MAX_TOKENS",
        cycle_time=12.5,
        assignable_cause="NONE",
    )

    assert record.framing_tokens == 18
    assert record.rework_tokens == 1512  # 1950 - 438
    assert record.prompt_tokens == 1950
    assert record.output_tokens == 300
    assert record.total_tokens == 2250
    assert record.assignable_cause == "API_MAX_TOKENS"


def test_build_audit_payload_cumulative_accounting() -> None:
    """Verify audit payload accurately records iterations and cumulative API usage."""
    defect_report = DefectReport(is_conforming=True)
    record = TelemetryBuilder.build_run_record(
        run_id=5,
        phase="Phase_I",
        operator="tester",
        model_ver="gemini-3.8-flash",
        input_filename="page_005.pdf",
        factor_x1=0,
        factor_x2=0,
        context_tokens=0,
        instruction_tokens=20,
        page_tokens=400,
        initial_prompt_tokens=438,
        final_prompt_tokens=1950,
        final_output_tokens=300,
        defect_report=defect_report,
        rework_count=1,
        finish_reason="STOP",
        cycle_time=8.0,
        assignable_cause="NONE",
    )

    iterations = [
        IterationRecord(
            iteration=0,
            prompt_text="Initial Prompt",
            response_text="Defective Output",
            prompt_tokens=438,
            output_tokens=450,
            conforming=False,
            defects=["Missing header"],
        ),
        IterationRecord(
            iteration=1,
            prompt_text="Rework Prompt",
            response_text="Conforming Output",
            prompt_tokens=1950,
            output_tokens=300,
            conforming=True,
            defects=[],
        ),
    ]

    payload = TelemetryBuilder.build_audit_payload(
        record=record,
        request_prompt="Initial Prompt",
        final_markdown="Conforming Output",
        inspection_events=[{"iteration": 0, "conforming": False}, {"iteration": 1, "conforming": True}],
        iterations=iterations,
    )

    assert len(payload.iterations) == 2
    assert payload.cumulative_tokens["total_api_prompt_tokens"] == 2388  # 438 + 1950
    assert payload.cumulative_tokens["total_api_output_tokens"] == 750   # 450 + 300
    assert payload.cumulative_tokens["total_api_tokens"] == 3138
    assert payload.raw_usage_metadata["rework_tokens"] == 1512
