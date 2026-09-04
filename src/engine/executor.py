"""Transformation execution engine orchestrating LLM dispatch, inspection, and rework."""

import time
from collections.abc import Callable
from typing import Any

from src.core.models import DefectReport, ExecutionResult, IterationRecord
from src.engine.gemini_client import GeminiClient
from src.engine.telemetry_builder import TelemetryBuilder
from src.persistence.audit_logger import AuditLogger
from src.persistence.csv_logger import CSVLogger
from src.persistence.webhook_client import WebhookClient
from src.prompts.loader import (
    build_prompt,
    format_rework_prompt,
    load_bare_prompt,
    load_memory_context,
)
from src.state.session_manager import SessionManager
from src.validation.inspector import QualityInspector


class TransformationExecutor:
    """Orchestrates transformation, timing, quality gates, and persistence."""

    def __init__(
        self, gemini_client: GeminiClient, inspector: QualityInspector | None = None,
        session_manager: SessionManager | None = None, csv_logger: CSVLogger | None = None,
        audit_logger: AuditLogger | None = None, webhook_client: WebhookClient | None = None,
    ) -> None:
        self.gemini_client = gemini_client
        self.inspector = inspector or QualityInspector()
        self.session_manager = session_manager or SessionManager()
        self.csv_logger = csv_logger or CSVLogger()
        self.audit_logger = audit_logger or AuditLogger()
        self.webhook_client = webhook_client or WebhookClient()

    def _count_tokens(self, contents: Any) -> int:
        fn = getattr(self.gemini_client, "count_tokens", None)
        if callable(fn):
            res = fn(contents)
            if isinstance(res, (int, float, str)):
                return int(res)
        return 0

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
        tpl = f"{load_memory_context()}\n\n---\n\n{load_bare_prompt()}" if factor_x2 == 1 else load_bare_prompt()

        ctx_tokens = self._count_tokens(history) if history and factor_x1 == 0 else 0
        instruction_tokens = self._count_tokens(tpl)
        page_tokens = self._count_tokens(page_text)

        start_time = time.perf_counter()
        current_text, tokens = self.gemini_client.send_prompt(chat, prompt)
        init_p, init_o = tokens["prompt_tokens"], tokens["output_tokens"]
        final_p, final_o = init_p, init_o
        finish_reason = str(tokens.get("finish_reason", "STOP"))
        model_ver = str(tokens.get("model_version", getattr(self.gemini_client, "model_name", "gemini-2.5-flash")))

        defect_report = self.inspector.inspect(current_text, has_math_in_input=has_math_in_input)
        rework_count = 0
        events: list[dict[str, Any]] = [{
            "iteration": 0, "conforming": defect_report.is_conforming, "defects": defect_report.defect_reasons,
        }]
        iterations: list[IterationRecord] = [IterationRecord(
            iteration=0, prompt_text=prompt, response_text=current_text,
            prompt_tokens=init_p, output_tokens=init_o, thinking_tokens=tokens.get("thinking_tokens", 0),
            conforming=defect_report.is_conforming, defects=defect_report.defect_reasons,
        )]
        turns: list[dict[str, Any]] = [
            {"role": "user", "parts": [{"text": prompt}]},
            {"role": "model", "parts": [{"text": current_text}]},
        ]

        while defect_report.has_defects and rework_count < max_reworks:
            rework_count += 1
            bullets = defect_report.format_diagnostic_bullets()
            rework_prompt = format_rework_prompt(rework_count, bullets)
            if on_rework:
                on_rework(rework_count, defect_report, rework_prompt)
            current_text, r_tokens = self.gemini_client.send_prompt(chat, rework_prompt)
            final_p, final_o = r_tokens["prompt_tokens"], r_tokens["output_tokens"]
            finish_reason = str(r_tokens.get("finish_reason", finish_reason))
            defect_report = self.inspector.inspect(current_text, has_math_in_input=has_math_in_input)
            events.append({
                "iteration": rework_count, "conforming": defect_report.is_conforming, "defects": defect_report.defect_reasons,
            })
            iterations.append(IterationRecord(
                iteration=rework_count, prompt_text=rework_prompt, response_text=current_text,
                prompt_tokens=final_p, output_tokens=final_o,
                thinking_tokens=r_tokens.get("thinking_tokens", 0),
                conforming=defect_report.is_conforming, defects=defect_report.defect_reasons,
            ))
            turns.extend([
                {"role": "user", "parts": [{"text": rework_prompt}]},
                {"role": "model", "parts": [{"text": current_text}]},
            ])

        cycle_time = time.perf_counter() - start_time
        if defect_report.is_conforming:
            self.session_manager.save_history(history + turns, factor_x1)
        elif assignable_cause == "NONE":
            assignable_cause = "REWORK_LIMIT_EXCEEDED"

        record = TelemetryBuilder.build_run_record(
            run_id=run_id, phase=phase, operator=operator, model_ver=model_ver,
            input_filename=input_filename, factor_x1=factor_x1, factor_x2=factor_x2,
            context_tokens=ctx_tokens, instruction_tokens=instruction_tokens, page_tokens=page_tokens,
            initial_prompt_tokens=init_p, final_prompt_tokens=final_p,
            final_output_tokens=final_o, thinking_tokens=sum(it.thinking_tokens for it in iterations),
            defect_report=defect_report, rework_count=rework_count, finish_reason=finish_reason,
            cycle_time=cycle_time, assignable_cause=assignable_cause,
        )

        audit = TelemetryBuilder.build_audit_payload(
            record=record, request_prompt=prompt, final_markdown=current_text,
            inspection_events=events, iterations=iterations,
        )

        self.csv_logger.log_run(record)
        self.audit_logger.save_audit(audit)
        self.audit_logger.save_output_markdown(run_id, current_text)
        self.webhook_client.dispatch(record)

        return ExecutionResult(
            record=record, defect_report=defect_report,
            output_markdown=current_text, audit_payload=audit,
        )
