"""Core domain constants and data models for SPC and prompt engineering."""

from spc.core.constants import (
    Phase,
    PHASE_WINDOWS,
    SPCConstants,
    QualityGateRules,
)
from spc.core.models import (
    RunRecord,
    DefectReport,
    AuditPayload,
    ExecutionResult,
)

__all__ = [
    "Phase",
    "PHASE_WINDOWS",
    "SPCConstants",
    "QualityGateRules",
    "RunRecord",
    "DefectReport",
    "AuditPayload",
    "ExecutionResult",
]
