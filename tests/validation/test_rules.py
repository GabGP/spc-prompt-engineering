"""Unit tests for spc.validation.rules."""

from spc.validation.rules import (
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
