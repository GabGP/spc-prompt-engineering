"""Transformation execution engine orchestrating LLM dispatch, inspection, and rework."""

import time
from collections.abc import Callable
from datetime import datetime
from typing import Any

from src.core.models import AuditPayload, DefectReport, ExecutionResult, RunRecord
from src.engine.gemini_client import GeminiClient
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
        p_tokens, o_tokens = tokens["prompt_tokens"], tokens["output_tokens"]
        finish_reason = str(tokens.get("finish_reason", "STOP"))
        model_ver = str(tokens.get("model_version", getattr(self.gemini_client, "model_name", "gemini-2.5-flash")))

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
            finish_reason = str(r_tokens.get("finish_reason", finish_reason))
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

        framing_tokens = max(0, p_tokens - (ctx_tokens + instruction_tokens + page_tokens))
        total_tokens = p_tokens + o_tokens
        cause = f"API_{finish_reason}" if finish_reason != "STOP" and assignable_cause == "NONE" else assignable_cause

        record = RunRecord(
            run_id=run_id, timestamp=datetime.now().astimezone(), phase=phase,
            operator=operator, model_version=model_ver, input_file=input_filename,
            factor_x1=factor_x1, factor_x2=factor_x2, context_tokens=ctx_tokens,
            instruction_tokens=instruction_tokens, page_tokens=page_tokens,
            framing_tokens=framing_tokens, prompt_tokens=p_tokens,
            output_tokens=o_tokens, total_tokens=total_tokens,
            conforming=1 if defect_report.is_conforming else 0,
            rework_cycles=rework_count, finish_reason=finish_reason,
            cycle_time_sec=cycle_time, assignable_cause=cause,
        )

        audit = AuditPayload(
            run_id=run_id, timestamp=record.timestamp.isoformat(), phase=phase,
            operator=operator, model_version=model_ver, input_file=input_filename,
            request_prompt=prompt, final_output_markdown=current_text,
            total_cycle_time_sec=record.cycle_time_sec, rework_count=rework_count,
            conforming=defect_report.is_conforming, inspection_events=events,
            raw_usage_metadata={
                "context_tokens": ctx_tokens, "instruction_tokens": instruction_tokens,
                "page_tokens": page_tokens, "framing_tokens": framing_tokens,
                "prompt_tokens": p_tokens, "output_tokens": o_tokens,
                "total_tokens": total_tokens, "finish_reason": finish_reason,
                "model_version": model_ver,
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
