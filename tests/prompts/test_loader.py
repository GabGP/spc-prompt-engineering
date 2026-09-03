"""Unit tests for spc.prompts.loader."""

from src.prompts.loader import (
    build_prompt,
    format_rework_prompt,
    load_bare_prompt,
    load_memory_context,
    load_rework_template,
)


def test_load_bare_prompt() -> None:
    """Verify loading the unconstrained bare prompt."""
    prompt = load_bare_prompt()
    assert isinstance(prompt, str)
    assert len(prompt) > 0
    assert "Extract" in prompt


def test_load_memory_context() -> None:
    """Verify loading the structured SOP schema prompt."""
    sop = load_memory_context()
    assert isinstance(sop, str)
    assert "## Core Synthesis" in sop
    assert "## Technical Taxonomy" in sop
    assert "## Analytical Formulations" in sop
    assert "NONE RECORDED" in sop


def test_load_rework_template() -> None:
    """Verify loading the dynamic rework reflection template."""
    template = load_rework_template()
    assert "{rework_count}" in template
    assert "{defect_bullets}" in template


def test_format_rework_prompt() -> None:
    """Verify dynamic substitution of rework counter and defect reasons."""
    bullets = "- Missing header: ## Core Synthesis\n- Unclosed $$ tags"
    rendered = format_rework_prompt(rework_count=2, defect_bullets=bullets)
    assert "Iteration 2" in rendered
    assert "- Missing header: ## Core Synthesis" in rendered
    assert "- Unclosed $$ tags" in rendered


def test_build_prompt_factor_x2_levels() -> None:
    """Verify prompt payload construction for X2=0 (bare) and X2=1 (SOP)."""
    input_text = "Sample textbook page content."

    # Level X2 = 0 (Bare)
    prompt_0 = build_prompt(factor_x2=0, input_text=input_text)
    assert "Extract" in prompt_0
    assert input_text in prompt_0
    assert "Role & Operational Standard" not in prompt_0

    # Level X2 = 1 (SOP Injected)
    prompt_1 = build_prompt(factor_x2=1, input_text=input_text)
    assert "Role & Operational Standard" in prompt_1
    assert "## Core Synthesis" in prompt_1
    assert input_text in prompt_1
