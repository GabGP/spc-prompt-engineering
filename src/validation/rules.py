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


def detect_math_in_text(text: str) -> bool:
    """Detect analytical formulas, parameters, or equations in document text.

    Enforces deterministic quality gate routing: if math is detected, the LLM
    must extract equations into '## Analytical Formulations'; if no math exists,
    the LLM must provide the marker 'NONE RECORDED'.
    """
    patterns = (
        # 1. Equations/inequalities with Latin/Greek vars, subscripts & hats (e.g. Y = β0 + β1X, X1 ≤ t1)
        r"[A-Za-z0-9\u02c6\u0300-\u03ff]+\s*[=<>≤≥≈≠∼≡]\s*[-+−]?[0-9A-Za-z\u02c6\u0300-\u03ff\u23a7-\u23a9]+",
        # 2. Standard LaTeX math commands (e.g. \frac, \sum, \alpha, \beta, \lambda)
        r"\\(frac|sum|int|sqrt|alpha|beta|sigma|mu|lambda|theta|epsilon|gamma|bar)",
        # 3. Mathematical operators and set notation (e.g. ∑, ∫, ±, √, ∈, ∪, ∩, ∅)
        r"[∑∫±√∈∉∪∩∅∝∞]",
        # 4. Standalone Greek letters used as statistical parameters (e.g. α, β, σ², λ, Σ)
        r"[\u03b1-\u03c9\u0391-\u03a9]",
        # 5. SPC quality engineering metrics (e.g. UCL, LCL, C_p, C_pk)
        r"\b(UCL|LCL|C_p|C_pk)\b",
        # 6. Mathematical functions with optional hats/diacritics (e.g. f(X), ˆf(X), g(x))
        r"(?:\b|[^\w\s]|\u02c6)[fgh]\([a-zA-Z0-9_,\s\u02c6\u0300-\u03ff\-+−]+\)",
        # 7. Probability, expectation & optimization operators (e.g. Var(ε), Pr(Y=1|X), argmin)
        r"\b(Var|Cov|Corr|MSE|RSS|Pr|Prob|exp|argmin|argmax)\s*\(",
        # 8. Markdown LaTeX block delimiters ($$)
        r"\$\$",
        # 9. Standard textbook equation citations (e.g. (2.2), (3.14))
        r"\(\s*\d+\.\d+\s*\)",
        # 10. Composite not-equal expressions in extracted fonts (e.g. Σ1 ⁄= Σ2)
        r"[=<>]\s*⁄=\s*[=<>0-9A-Za-z\u0370-\u03ff]",
    )
    return bool(re.search("|".join(patterns), text, flags=re.IGNORECASE))
