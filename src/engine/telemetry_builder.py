"""Telemetry and persistence record builder for SPC transformation runs."""

from datetime import datetime
from typing import Any

from src.core.models import AuditPayload, DefectReport, IterationRecord, RunRecord


class TelemetryBuilder:
    """Computes invariant token metrics and constructs persistence payloads."""

    @staticmethod
    def calculate_framing_tokens(
        initial_prompt_tokens: int,
        context_tokens: int,
        instruction_tokens: int,
        page_tokens: int,
    ) -> int:
        """Calculate pure protocol framing overhead from initial turn."""
        base_input = context_tokens + instruction_tokens + page_tokens
        return max(0, initial_prompt_tokens - base_input)

    @classmethod
    def build_run_record(
        cls,
        run_id: int,
        phase: str,
        operator: str,
        model_ver: str,
        input_filename: str,
        factor_x1: int,
        factor_x2: int,
        context_tokens: int,
        instruction_tokens: int,
        page_tokens: int,
        initial_prompt_tokens: int,
        final_prompt_tokens: int,
        final_output_tokens: int,
        defect_report: DefectReport,
        rework_count: int,
        finish_reason: str,
        cycle_time: float,
        assignable_cause: str,
    ) -> RunRecord:
        """Build standardized 21-column RunRecord."""
        framing = cls.calculate_framing_tokens(
            initial_prompt_tokens, context_tokens, instruction_tokens, page_tokens
        )
        rework = max(0, final_prompt_tokens - initial_prompt_tokens) if rework_count > 0 else 0
        total = final_prompt_tokens + final_output_tokens
        cause = (
            f"API_{finish_reason}"
            if finish_reason != "STOP" and assignable_cause == "NONE"
            else assignable_cause
        )

        return RunRecord(
            run_id=run_id,
            timestamp=datetime.now().astimezone(),
            phase=phase,
            operator=operator,
            model_version=model_ver,
            input_file=input_filename,
            factor_x1=factor_x1,
            factor_x2=factor_x2,
            context_tokens=context_tokens,
            instruction_tokens=instruction_tokens,
            page_tokens=page_tokens,
            framing_tokens=framing,
            rework_tokens=rework,
            prompt_tokens=final_prompt_tokens,
            output_tokens=final_output_tokens,
            total_tokens=total,
            conforming=1 if defect_report.is_conforming else 0,
            rework_cycles=rework_count,
            finish_reason=finish_reason,
            cycle_time_sec=cycle_time,
            assignable_cause=cause,
        )

    @staticmethod
    def build_audit_payload(
        record: RunRecord,
        request_prompt: str,
        final_markdown: str,
        inspection_events: list[dict[str, Any]],
        iterations: list[IterationRecord],
    ) -> AuditPayload:
        """Build full forensic AuditPayload including all iteration attempts."""
        cum_prompt = sum(it.prompt_tokens for it in iterations)
        cum_output = sum(it.output_tokens for it in iterations)
        cumulative = {
            "total_api_prompt_tokens": cum_prompt,
            "total_api_output_tokens": cum_output,
            "total_api_tokens": cum_prompt + cum_output,
        }

        return AuditPayload(
            run_id=record.run_id,
            timestamp=record.timestamp.isoformat(),
            phase=record.phase,
            operator=record.operator,
            model_version=record.model_version,
            input_file=record.input_file,
            request_prompt=request_prompt,
            final_output_markdown=final_markdown,
            total_cycle_time_sec=record.cycle_time_sec,
            rework_count=record.rework_cycles,
            conforming=record.conforming == 1,
            inspection_events=inspection_events,
            iterations=iterations,
            cumulative_tokens=cumulative,
            raw_usage_metadata={
                "context_tokens": record.context_tokens,
                "instruction_tokens": record.instruction_tokens,
                "page_tokens": record.page_tokens,
                "framing_tokens": record.framing_tokens,
                "rework_tokens": record.rework_tokens,
                "prompt_tokens": record.prompt_tokens,
                "output_tokens": record.output_tokens,
                "total_tokens": record.total_tokens,
                "finish_reason": record.finish_reason,
                "model_version": record.model_version,
            },
        )
