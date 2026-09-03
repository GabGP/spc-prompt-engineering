"""Unit tests for mock response template constants."""

from src.engine.mock_responses import (
    CONFORMING_MARKDOWN,
    EMPTY_RULE_CONFORMING_MARKDOWN,
    MISSING_EMPTY_RULE_MARKDOWN,
    MISSING_HEADER_MARKDOWN,
    UNCLOSED_LATEX_MARKDOWN,
)


def test_mock_responses_presence() -> None:
    """Verify all mock responses have content and mandatory headers where expected."""
    assert "## Core Synthesis" in CONFORMING_MARKDOWN
    assert "## Technical Taxonomy" in CONFORMING_MARKDOWN
    assert "## Analytical Formulations" in CONFORMING_MARKDOWN
    assert "NONE RECORDED" in EMPTY_RULE_CONFORMING_MARKDOWN
    assert "## Technical Taxonomy" not in MISSING_HEADER_MARKDOWN
    assert UNCLOSED_LATEX_MARKDOWN.count("$$") % 2 != 0
    assert "NONE RECORDED" not in MISSING_EMPTY_RULE_MARKDOWN
