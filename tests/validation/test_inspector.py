"""Unit tests for spc.validation.inspector."""

from spc.validation.inspector import QualityInspector


def test_quality_inspector_conforming() -> None:
    """Verify inspection of a fully compliant Markdown output."""
    inspector = QualityInspector()
    valid_doc = (
        "## Core Synthesis\n"
        "This is a compliant summary of the digital page.\n\n"
        "## Technical Taxonomy\n"
        "- Quality Control: Monitoring method.\n\n"
        "## Analytical Formulations\n"
        "NONE RECORDED\n"
    )
    report = inspector.inspect(valid_doc, has_math_in_input=False)
    assert report.is_conforming
    assert not report.has_defects
    assert len(report.defect_reasons) == 0


def test_quality_inspector_missing_headers() -> None:
    """Verify inspection flags missing mandatory headers."""
    inspector = QualityInspector()
    incomplete_doc = (
        "## Core Synthesis\n"
        "Only one header provided.\n"
    )
    report = inspector.inspect(incomplete_doc, has_math_in_input=False)
    assert not report.is_conforming
    assert report.has_defects
    assert "## Technical Taxonomy" in report.missing_headers
    assert "## Analytical Formulations" in report.missing_headers
    assert any("Missing mandatory section" in r for r in report.defect_reasons)


def test_quality_inspector_unclosed_latex() -> None:
    """Verify inspection flags unclosed LaTeX tags."""
    inspector = QualityInspector()
    latex_bad = (
        "## Core Synthesis\nText.\n\n"
        "## Technical Taxonomy\nText.\n\n"
        "## Analytical Formulations\n"
        "$$ y = mx + b\n"  # Missing closing $$
    )
    report = inspector.inspect(latex_bad, has_math_in_input=True)
    assert not report.is_conforming
    assert report.unclosed_latex
    assert any("Unclosed block LaTeX" in r for r in report.defect_reasons)


def test_quality_inspector_empty_formula_defect() -> None:
    """Verify inspection flags missing 'NONE RECORDED' when input has no math."""
    inspector = QualityInspector()
    doc_without_marker = (
        "## Core Synthesis\nText.\n\n"
        "## Technical Taxonomy\nText.\n\n"
        "## Analytical Formulations\n"
        "No formulas were located in this text.\n"
    )
    report = inspector.inspect(doc_without_marker, has_math_in_input=False)
    assert not report.is_conforming
    assert report.empty_rule_violated
    assert any("Empty formula violation" in r for r in report.defect_reasons)


def test_quality_inspector_multiple_simultaneous_defects() -> None:
    """Verify aggregation of multiple defects in a single inspection pass."""
    inspector = QualityInspector()
    bad_doc = "Just raw unformatted text with unclosed $$ tag."
    report = inspector.inspect(bad_doc, has_math_in_input=False)

    assert not report.is_conforming
    assert len(report.missing_headers) == 3
    assert report.unclosed_latex
    assert report.empty_rule_violated
    assert len(report.defect_reasons) >= 5
