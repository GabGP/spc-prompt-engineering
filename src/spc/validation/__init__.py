"""Deterministic Go / No-Go quality gate and inspection rules."""

from spc.validation.inspector import QualityInspector
from spc.validation.rules import (
    check_empty_formula_rule,
    check_latex_closure,
    check_mandatory_headers,
)

__all__ = [
    "QualityInspector",
    "check_empty_formula_rule",
    "check_latex_closure",
    "check_mandatory_headers",
]
