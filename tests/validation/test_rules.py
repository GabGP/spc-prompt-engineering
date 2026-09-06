"""Unit tests for spc.validation.rules."""

from src.validation.rules import (
    check_empty_formula_rule,
    check_latex_closure,
    check_mandatory_headers,
    extract_section_content,
)


def test_check_mandatory_headers_all_present() -> None:
    """Verify check_mandatory_headers returns empty list when all headers exist."""
    text = (
        "## Core Synthesis\n"
        "Summary text here.\n\n"
        "## Technical Taxonomy\n"
        "- Term 1\n\n"
        "## Analytical Formulations\n"
        "NONE RECORDED\n"
    )
    missing = check_mandatory_headers(text)
    assert missing == []


def test_check_mandatory_headers_missing() -> None:
    """Verify check_mandatory_headers identifies missing headers."""
    text = (
        "## Core Synthesis\n"
        "Summary text here.\n\n"
        "## Analytical Formulations\n"
        "NONE RECORDED\n"
    )
    missing = check_mandatory_headers(text)
    assert missing == ["## Technical Taxonomy"]

    # All missing
    assert len(check_mandatory_headers("Just arbitrary text.")) == 3


def test_check_latex_closure() -> None:
    """Verify block LaTeX delimiter parity checking."""
    # Paired block formulas
    valid_text = "Formula: $$ E = mc^2 $$ and another: $$ F = ma $$"
    assert check_latex_closure(valid_text)

    # No math tags
    assert check_latex_closure("No formulas here.")

    # Unclosed formula (odd number of $$)
    invalid_text = "Formula: $$ E = mc^2 without closure"
    assert not check_latex_closure(invalid_text)

    three_delimiters = "Formula: $$ E = mc^2 $$ and bad $$ broken"
    assert not check_latex_closure(three_delimiters)


def test_extract_section_content() -> None:
    """Verify extracting content bounded by Markdown headers."""
    doc = (
        "## Header A\n"
        "Content A line 1\n"
        "Content A line 2\n\n"
        "## Header B\n"
        "Content B\n"
    )
    content_a = extract_section_content(doc, "## Header A")
    assert "Content A line 1" in content_a
    assert "Content B" not in content_a

    # Non-existent header
    assert extract_section_content(doc, "## NonExistent") == ""


def test_check_empty_formula_rule() -> None:
    """Verify empty formula rule logic."""
    valid_empty = (
        "## Analytical Formulations\n"
        "NONE RECORDED\n"
    )
    # When input has no math and output has NONE RECORDED -> True
    assert check_empty_formula_rule(valid_empty, has_math_in_input=False)

    # When input has no math and output misses NONE RECORDED -> False
    invalid_empty = (
        "## Analytical Formulations\n"
        "No equations were identified.\n"
    )
    assert not check_empty_formula_rule(invalid_empty, has_math_in_input=False)

    # When input has math -> always True (does not require NONE RECORDED)
    assert check_empty_formula_rule(invalid_empty, has_math_in_input=True)


def test_detect_math_in_text() -> None:
    """Verify regex patterns accurately classify math versus qualitative text."""
    from src.validation.rules import detect_math_in_text

    qualitative = "An overview of statistical learning. Tools for understanding data."
    assert not detect_math_in_text(qualitative)
    assert not detect_math_in_text("refer to (Section 2.2) or (see Figure 2.2)")
    assert not detect_math_in_text("This chapter is about linear regression, a very simple approach.")

    # Basic algebra & LaTeX
    assert detect_math_in_text("Given Y = f(X) + e, we estimate f.")
    assert detect_math_in_text("The sum is \\sum_{i=1}^n X_i.")
    assert detect_math_in_text("Control limits: UCL = X_bar + 3*sigma.")
    assert detect_math_in_text("Variance is Var(X) = E(X^2) - mu^2.")
    assert detect_math_in_text("Equation: $$ x = 42 $$")

    # Unicode circumflex hat notation (ISLR Page 32 / Eq 2.2)
    assert detect_math_in_text("predict Y using \u02c6Y = \u02c6f(X), (2.2)")
    assert detect_math_in_text("we define \u02c6f(X) as the estimator")
    assert detect_math_in_text("see formulation (3.14) for derivation")

    # Greek parameter estimators (ISLR Page 216 / Page 356)
    assert detect_math_in_text("i. Y = \u03b20 +\u03b21X +\u03f5")
    assert detect_math_in_text("f(x\u2217)= \u03b20 +\u03b21x\u22171")

    # Subscripts before inequality operators (ISLR Page 323 / Page 68)
    assert detect_math_in_text("X1 \u2264 t1 and X2 \u2264 t2")
    assert detect_math_in_text("X1 = X2 = X3 = 0 using K-nearest neighbors")

    # Set theory & Matrix notation (ISLR Page 401 / Page 165)
    assert detect_math_in_text("C1 \u222a C2 = {1,...,n}")
    assert detect_math_in_text("\u03a31 \u2044= \u03a32")

    # Piecewise functions with bracket hooks (ISLR Page 144)
    assert detect_math_in_text("Y = \n\u23a7 1 if stroke")

    # Probability and optimization operators
    assert detect_math_in_text("compute Pr(default = Yes | balance)")
    assert detect_math_in_text("solve argmin \u2211 (y_i - f(x_i))^2")
