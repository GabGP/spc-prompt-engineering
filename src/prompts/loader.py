"""Utilities for loading and rendering prompt templates."""

from pathlib import Path

PROMPTS_DIR: Path = Path(__file__).resolve().parent


def load_bare_prompt() -> str:
    """Load the baseline unconstrained prompt (X2=0)."""
    file_path = PROMPTS_DIR / "bare_prompt.md"
    return file_path.read_text(encoding="utf-8").strip()


def load_memory_context() -> str:
    """Load the structured SOP schema prompt (X2=1)."""
    file_path = PROMPTS_DIR / "memory_context.md"
    return file_path.read_text(encoding="utf-8").strip()


def load_rework_template() -> str:
    """Load the reflection rework prompt template."""
    file_path = PROMPTS_DIR / "rework_template.md"
    return file_path.read_text(encoding="utf-8").strip()


def format_rework_prompt(rework_count: int, defect_bullets: str) -> str:
    """Render the dynamic reflection rework prompt with detected defects."""
    template = load_rework_template()
    return template.format(
        rework_count=rework_count,
        defect_bullets=defect_bullets,
    )


def build_prompt(factor_x2: int, input_text: str) -> str:
    """Construct the full prompt payload based on Factor X2 level.

    Args:
        factor_x2: 0 for bare prompt, 1 for SOP schema memory injection.
        input_text: Extracted page text to transform.
    """
    bare = load_bare_prompt()
    if factor_x2 == 1:
        sop = load_memory_context()
        return f"{sop}\n\n---\n\n{bare}\n\n---\n\n# Input Document Page:\n{input_text}"

    return f"{bare}\n\n---\n\n# Input Document Page:\n{input_text}"
