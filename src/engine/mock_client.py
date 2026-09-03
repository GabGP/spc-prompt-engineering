"""Deterministic mock Gemini client for staged validation and edge-case testing."""

from typing import Any

CONFORMING_MARKDOWN = """## Core Synthesis
Statistical Process Control (SPC) leverages Shewhart control charts to distinguish
between common-cause variation and assignable causes, stabilizing operational latency.

## Technical Taxonomy
- **Common Cause:** Natural, random, inherent variation in an established system.
- **Assignable Cause:** Specific, identifiable disturbance requiring root-cause intervention.
- **Cycle Time (T):** Elapsed real-time latency required to process an operational unit.

## Analytical Formulations
$$ \\bar{X} = \\frac{1}{n} \\sum_{i=1}^{n} X_i $$
$$ \\text{UCL} = \\bar{X} + A_2 \\bar{R} $$
$$ \\text{LCL} = \\bar{X} - A_2 \\bar{R} $$
"""

MISSING_HEADER_MARKDOWN = """## Core Synthesis
Defective output missing Technical Taxonomy section.

## Analytical Formulations
$$ \\bar{X} = \\frac{1}{n} \\sum_{i=1}^{n} X_i $$
"""

UNCLOSED_LATEX_MARKDOWN = """## Core Synthesis
LaTeX syntax error demonstration.

## Technical Taxonomy
- **Defect:** Unclosed LaTeX formula block.

## Analytical Formulations
$$ \\bar{X} = \\frac{1}{n} \\sum_{i=1}^{n} X_i
"""

MISSING_EMPTY_RULE_MARKDOWN = """## Core Synthesis
No mathematical expressions in this input unit.

## Technical Taxonomy
- **Qualitative Content:** Pure narrative without mathematical formulations.

## Analytical Formulations
No formulas were present in this excerpt.
"""

EMPTY_RULE_CONFORMING_MARKDOWN = """## Core Synthesis
No mathematical expressions in this input unit.

## Technical Taxonomy
- **Qualitative Content:** Pure narrative without mathematical formulations.

## Analytical Formulations
NONE RECORDED
"""


class MockUsageMetadata:
    """Mock usage metadata container matching Google GenAI SDK interface."""

    def __init__(self, prompt_tokens: int, output_tokens: int) -> None:
        self.prompt_token_count = prompt_tokens
        self.candidates_token_count = output_tokens
        self.total_token_count = prompt_tokens + output_tokens


class MockResponse:
    """Mock LLM response payload."""

    def __init__(self, text: str, prompt_tokens: int, output_tokens: int) -> None:
        self.text = text
        self.usage_metadata = MockUsageMetadata(prompt_tokens, output_tokens)


class MockGeminiChat:
    """Mock chat session simulating multi-turn state and rework iterations."""

    def __init__(
        self,
        scenario: str = "rework",
        raw_history: list[dict[str, Any]] | None = None,
    ) -> None:
        self.scenario = scenario
        self.history: list[dict[str, Any]] = list(raw_history) if raw_history else []
        self.turn_count = 0

    def send_message(self, prompt: str) -> MockResponse:
        """Emits staged response depending on scenario and retry iteration."""
        self.turn_count += 1
        is_rework = "QUALITY GATE" in prompt

        if is_rework:
            if self.scenario == "fail":
                resp_text = MISSING_HEADER_MARKDOWN
            elif self.scenario == "latex" and "NONE RECORDED" not in prompt:
                resp_text = CONFORMING_MARKDOWN
            else:
                resp_text = EMPTY_RULE_CONFORMING_MARKDOWN
        elif self.scenario == "pass":
            resp_text = EMPTY_RULE_CONFORMING_MARKDOWN
        elif self.scenario == "fail":
            resp_text = MISSING_HEADER_MARKDOWN
        elif self.scenario == "latex":
            resp_text = UNCLOSED_LATEX_MARKDOWN
        elif self.scenario == "empty_math":
            resp_text = MISSING_EMPTY_RULE_MARKDOWN
        else:  # default 'rework'
            resp_text = MISSING_HEADER_MARKDOWN

        p_tokens = 550 + (self.turn_count * 280)
        o_tokens = 220 + (self.turn_count * 40)
        self.history.append({"role": "user", "parts": [{"text": prompt}]})
        self.history.append({"role": "model", "parts": [{"text": resp_text}]})
        return MockResponse(resp_text, p_tokens, o_tokens)

    def get_history(self) -> list[dict[str, Any]]:
        """Return serialized session history turns."""
        return self.history


class MockGeminiClient:
    """Mock LLM client for offline verification of inspection gates and rework loops."""

    def __init__(
        self,
        scenario: str = "rework",
        api_key: str = "mock-key",
        model_name: str = "mock-model",
    ) -> None:
        self.scenario = scenario
        self.api_key = api_key
        self.model_name = model_name

    def create_chat(
        self, raw_history: list[dict[str, Any]] | None = None
    ) -> MockGeminiChat:
        """Create mock chat instance with simulated history."""
        return MockGeminiChat(scenario=self.scenario, raw_history=raw_history)

    def send_prompt(self, chat: Any, prompt: str) -> tuple[str, dict[str, int]]:
        """Dispatch prompt through mock chat session and extract simulated tokens."""
        response = chat.send_message(prompt)
        tokens = {
            "prompt_tokens": response.usage_metadata.prompt_token_count,
            "output_tokens": response.usage_metadata.candidates_token_count,
            "total_tokens": response.usage_metadata.total_token_count,
        }
        return response.text, tokens
