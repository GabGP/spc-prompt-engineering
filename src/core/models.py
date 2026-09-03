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

    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    run_id: int
    phase: str
    factor_x1: int = Field(ge=0, le=1)
    factor_x2: int = Field(ge=0, le=1)
    cycle_time_sec: float = Field(gt=0.0)
    prompt_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    conforming: int = Field(ge=0, le=1)
    rework_cycles: int = Field(ge=0)
    assignable_cause: str = "NONE"
    operator: str

    @field_validator("cycle_time_sec")
    @classmethod
    def round_cycle_time(cls, value: float) -> float:
        """Round cycle time duration to 4 decimal places for precision."""
        return round(value, 4)

    def to_csv_dict(self) -> dict[str, Any]:
        """Serialize record into an ordered dictionary matching CSV schema."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "run_id": self.run_id,
            "phase": self.phase,
            "factor_x1": self.factor_x1,
            "factor_x2": self.factor_x2,
            "cycle_time_sec": self.cycle_time_sec,
            "prompt_tokens": self.prompt_tokens,
            "output_tokens": self.output_tokens,
            "conforming": self.conforming,
            "rework_cycles": self.rework_cycles,
            "assignable_cause": self.assignable_cause,
            "operator": self.operator,
        }


class AuditPayload(BaseModel):
    """Full forensic audit data stored in data/logs/run_XXX_audit.json."""

    run_id: int
    timestamp: str
    phase: str
    operator: str
    input_file: str
    request_prompt: str = ""
    final_output_markdown: str
    total_cycle_time_sec: float
    rework_count: int
    conforming: bool
    inspection_events: list[dict[str, Any]] = Field(default_factory=list)
    raw_usage_metadata: dict[str, int] = Field(default_factory=dict)


class ExecutionResult(BaseModel):
    """Container returned upon completion of an engine transformation run."""

    record: RunRecord
    defect_report: DefectReport
    output_markdown: str
    audit_payload: AuditPayload
