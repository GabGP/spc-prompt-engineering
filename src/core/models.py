"""Pydantic data models and schemas for SPC runs, inspection, and auditing."""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class DefectReport(BaseModel):
    """Evaluation output from the deterministic Go / No-Go quality gate."""

    is_conforming: bool
    missing_headers: list[str] = Field(default_factory=list)
    unclosed_latex: bool = False
    empty_rule_violated: bool = False
    defect_reasons: list[str] = Field(default_factory=list)

    @property
    def has_defects(self) -> bool:
        """Return True if any defect was detected."""
        return not self.is_conforming

    def format_diagnostic_bullets(self) -> str:
        """Format detected defect reasons into Markdown bullet points."""
        if not self.defect_reasons:
            return "- No defects recorded."
        return "\n".join(f"- {reason}" for reason in self.defect_reasons)


class RunRecord(BaseModel):
    """Schema for a single transformation run logged in main_event_log.csv."""

    run_id: int
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    phase: str
    operator: str
    model_version: str = "gemini-2.5-flash"
    input_file: str = "unknown"
    factor_x1: int = Field(ge=0, le=1)
    factor_x2: int = Field(ge=0, le=1)
    context_tokens: int = Field(default=0, ge=0)
    instruction_tokens: int = Field(default=0, ge=0)
    page_tokens: int = Field(default=0, ge=0)
    framing_tokens: int = Field(default=0, ge=0)
    prompt_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    total_tokens: int = Field(default=0, ge=0)
    conforming: int = Field(ge=0, le=1)
    rework_cycles: int = Field(ge=0)
    finish_reason: str = "STOP"
    cycle_time_sec: float = Field(gt=0.0)
    assignable_cause: str = "NONE"

    @field_validator("cycle_time_sec")
    @classmethod
    def round_cycle_time(cls, value: float) -> float:
        """Round cycle time duration to 4 decimal places for precision."""
        return round(value, 4)

    def to_csv_dict(self) -> dict[str, Any]:
        """Serialize record into an ordered dictionary matching CSV schema."""
        return {
            "run_id": self.run_id,
            "timestamp": self.timestamp.isoformat(),
            "phase": self.phase,
            "operator": self.operator,
            "model_version": self.model_version,
            "input_file": self.input_file,
            "factor_x1": self.factor_x1,
            "factor_x2": self.factor_x2,
            "context_tokens": self.context_tokens,
            "instruction_tokens": self.instruction_tokens,
            "page_tokens": self.page_tokens,
            "framing_tokens": self.framing_tokens,
            "prompt_tokens": self.prompt_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "conforming": self.conforming,
            "rework_cycles": self.rework_cycles,
            "finish_reason": self.finish_reason,
            "cycle_time_sec": self.cycle_time_sec,
            "assignable_cause": self.assignable_cause,
        }



class AuditPayload(BaseModel):
    """Full forensic audit data stored in data/logs/run_XXX_audit.json."""

    run_id: int
    timestamp: str
    phase: str
    operator: str
    model_version: str = ""
    input_file: str
    request_prompt: str = ""
    final_output_markdown: str
    total_cycle_time_sec: float
    rework_count: int
    conforming: bool
    inspection_events: list[dict[str, Any]] = Field(default_factory=list)
    raw_usage_metadata: dict[str, Any] = Field(default_factory=dict)


class ExecutionResult(BaseModel):
    """Container returned upon completion of an engine transformation run."""

    record: RunRecord
    defect_report: DefectReport
    output_markdown: str
    audit_payload: AuditPayload
