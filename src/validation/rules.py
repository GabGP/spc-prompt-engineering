"""Pure deterministic inspection rules for output validation."""

import re

from src.core.constants import QualityGateRules


def check_mandatory_headers(text: str) -> list[str]:
    """Check for presence of all required Markdown level-2 headers.

    Returns:
        List of missing header names. Empty if all are present.
    """
    missing: list[str] = []
    for header in QualityGateRules.REQUIRED_HEADERS:
        # Match header at start of line with optional trailing whitespace
        pattern = rf"^{re.escape(header)}\s*$"
        if not re.search(pattern, text, flags=re.MULTILINE):
            missing.append(header)
    return missing


def check_latex_closure(text: str) -> bool:
    """Verify that all block LaTeX delimiters ($$) are properly closed.

    Returns:
        True if all $$ blocks are paired and closed, False otherwise.
    """
    delimiter_count = text.count("$$")
    return delimiter_count % 2 == 0


def extract_section_content(text: str, section_header: str) -> str:
    """Extract text content under a specific level-2 header up to the next header."""
    pattern = rf"^{re.escape(section_header)}\s*$(.*?)(?=^## |\Z)"
    match = re.search(pattern, text, flags=re.MULTILINE | re.DOTALL)
    if not match:
        return ""
    return match.group(1).strip()


def check_empty_formula_rule(text: str, has_math_in_input: bool = False) -> bool:
    """Validate empty formula handling under '## Analytical Formulations'.

    If input has no math formulas, the section must explicitly contain
    the string 'NONE RECORDED'.

    Args:
        text: Transformed markdown output text.
        has_math_in_input: True if input document page contained math equations.

    Returns:
        True if conforming to empty handling rule, False if violated.
    """
    if has_math_in_input:
        return True

    content = extract_section_content(text, "## Analytical Formulations")
    return QualityGateRules.EMPTY_FORMULA_MARKER in content
