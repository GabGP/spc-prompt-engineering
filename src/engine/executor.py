"""Transformation execution engine orchestrating LLM dispatch, inspection, and rework."""

import time
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from src.core.models import AuditPayload, DefectReport, ExecutionResult, RunRecord
from src.engine.gemini_client import GeminiClient
from src.persistence.audit_logger import AuditLogger
from src.persistence.csv_logger import CSVLogger
from src.persistence.webhook_client import WebhookClient
from src.prompts.loader import build_prompt, format_rework_prompt
from src.state.session_manager import SessionManager
from src.validation.inspector import QualityInspector


class TransformationExecutor:
    """Orchestrates transformation, timing, quality gates, and persistence."""

    def __init__(
        self,
        gemini_client: GeminiClient,
        inspector: QualityInspector | None = None,
        session_manager: SessionManager | None = None,
        csv_logger: CSVLogger | None = None,
        audit_logger: AuditLogger | None = None,
        webhook_client: WebhookClient | None = None,
    ) -> None:
        self.gemini_client = gemini_client
        self.inspector = inspector or QualityInspector()
        self.session_manager = session_manager or SessionManager()
        self.csv_logger = csv_logger or CSVLogger()
        self.audit_logger = audit_logger or AuditLogger()
        self.webhook_client = webhook_client or WebhookClient()

    def execute_run(
        self,
        run_id: int,
        page_text: str,
        input_filename: str,
        phase: str,
        factor_x1: int,
        factor_x2: int,
        operator: str,
        max_reworks: int = 3,
        assignable_cause: str = "NONE",
        has_math_in_input: bool = False,
        on_rework: Callable[[int, DefectReport, str], None] | None = None,
    ) -> ExecutionResult:
        """Execute a full experimental transformation run with timing and rework."""
        history = self.session_manager.load_history(factor_x1)
        chat = self.gemini_client.create_chat(raw_history=history)
        prompt = build_prompt(factor_x2, page_text)

        cnt_fn = getattr(self.gemini_client, "count_tokens", None)
        ctx_tokens = int(cnt_fn(history)) if callable(cnt_fn) and history else 0
        page_tokens = int(cnt_fn(prompt)) if callable(cnt_fn) else 0

        start_time = time.perf_counter()
        current_text, tokens = self.gemini_client.send_prompt(chat, prompt)
        p_tokens, o_tokens = tokens["prompt_tokens"], tokens["output_tokens"]
        if ctx_tokens == 0 and factor_x1 == 0 and history:
            ctx_tokens = max(0, p_tokens - page_tokens)
        if page_tokens == 0:
            page_tokens = max(0, p_tokens - ctx_tokens)

        defect_report = self.inspector.inspect(
            current_text, has_math_in_input=has_math_in_input
        )
        rework_count = 0
        events: list[dict[str, Any]] = [{
            "iteration": 0, "conforming": defect_report.is_conforming, "defects": defect_report.defect_reasons,
        }]

        while defect_report.has_defects and rework_count < max_reworks:
            rework_count += 1
            bullets = defect_report.format_diagnostic_bullets()
            rework_prompt = format_rework_prompt(rework_count, bullets)
            if on_rework:
                on_rework(rework_count, defect_report, rework_prompt)
            current_text, r_tokens = self.gemini_client.send_prompt(
                chat, rework_prompt
            )
            p_tokens = r_tokens["prompt_tokens"]
            o_tokens += r_tokens["output_tokens"]
            defect_report = self.inspector.inspect(
                current_text, has_math_in_input=has_math_in_input
            )
            events.append({
                "iteration": rework_count, "conforming": defect_report.is_conforming, "defects": defect_report.defect_reasons,
            })

        cycle_time = time.perf_counter() - start_time
        clean_turn = [
            {"role": "user", "parts": [{"text": prompt}]},
            {"role": "model", "parts": [{"text": current_text}]},
        ]
        self.session_manager.save_history(history + clean_turn, factor_x1)

        total_tokens = p_tokens + o_tokens
        record = RunRecord(
            timestamp=datetime.now(UTC), run_id=run_id, input_file=input_filename,
            phase=phase, factor_x1=factor_x1, factor_x2=factor_x2,
            cycle_time_sec=cycle_time, context_tokens=ctx_tokens,
            page_tokens=page_tokens, prompt_tokens=p_tokens,
            output_tokens=o_tokens, total_tokens=total_tokens,
            conforming=1 if defect_report.is_conforming else 0,
            rework_cycles=rework_count, assignable_cause=assignable_cause,
            operator=operator,
        )

        audit = AuditPayload(
            run_id=run_id, timestamp=record.timestamp.isoformat(), phase=phase,
            operator=operator, input_file=input_filename, request_prompt=prompt,
            final_output_markdown=current_text, total_cycle_time_sec=record.cycle_time_sec,
            rework_count=rework_count, conforming=defect_report.is_conforming,
            inspection_events=events,
            raw_usage_metadata={
                "context_tokens": ctx_tokens, "page_tokens": page_tokens,
                "prompt_tokens": p_tokens, "output_tokens": o_tokens,
                "total_tokens": total_tokens,
            },
        )

        self.csv_logger.log_run(record)
        self.audit_logger.save_audit(audit)
        self.audit_logger.save_output_markdown(run_id, current_text)
        self.webhook_client.dispatch(record)

        return ExecutionResult(
            record=record, defect_report=defect_report,
            output_markdown=current_text, audit_payload=audit,
        )
