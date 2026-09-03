"""Quality inspector orchestrating deterministic Go / No-Go gates."""

from spc.core.models import DefectReport
from spc.validation.rules import (
    check_empty_formula_rule,
    check_latex_closure,
    check_mandatory_headers,
)


class QualityInspector:
    """Deterministic Go / No-Go quality gate evaluator."""

    def inspect(
        self,
        output_text: str,
        has_math_in_input: bool = False,
    ) -> DefectReport:
        """Run all deterministic validation rules against transformed output.

        Args:
            output_text: Generated Markdown artifact text.
            has_math_in_input: True if the source page contained math formulas.

        Returns:
            DefectReport detailing conformance status and specific defects.
        """
        reasons: list[str] = []

        # Gate 1: Structural Completeness
        missing_headers = check_mandatory_headers(output_text)
        for header in missing_headers:
            reasons.append(f"Missing mandatory section header: '{header}'")

        # Gate 2: Syntactical Validity (LaTeX Closure)
        latex_closed = check_latex_closure(output_text)
        unclosed_latex = not latex_closed
        if unclosed_latex:
            reasons.append("Unclosed block LaTeX formula tags detected ($$)")

        # Gate 3: Empty Formula Rule
        empty_valid = check_empty_formula_rule(output_text, has_math_in_input)
        empty_violated = not empty_valid
        if empty_violated:
            reasons.append(
                "Empty formula violation: '## Analytical Formulations' must "
                "state 'NONE RECORDED' when no equations exist"
            )

        is_conforming = len(reasons) == 0

        return DefectReport(
            is_conforming=is_conforming,
            missing_headers=missing_headers,
            unclosed_latex=unclosed_latex,
            empty_rule_violated=empty_violated,
            defect_reasons=reasons,
        )
