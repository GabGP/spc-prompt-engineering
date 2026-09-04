"""Deterministic mock Gemini client for staged validation and edge-case testing."""

from typing import Any

from src.engine.mock_responses import (
    CONFORMING_MARKDOWN,
    EMPTY_RULE_CONFORMING_MARKDOWN,
    MISSING_EMPTY_RULE_MARKDOWN,
    MISSING_HEADER_MARKDOWN,
    UNCLOSED_LATEX_MARKDOWN,
)


def _extract_text(item: Any) -> str:
    """Extract plain text from turn dictionary, Content, or part structure."""
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        parts = item.get("parts")
        if isinstance(parts, list):
            return " ".join(str(p.get("text", "") if isinstance(p, dict) else getattr(p, "text", p)) for p in parts)
        return str(item.get("text", ""))
    return str(getattr(item, "text", item or ""))


def _estimate_tokens(text: str) -> int:
    """Estimate token count based on standard word-to-token ratio (~4/3)."""
    words = len(text.split())
    return max(1, words * 4 // 3) if words > 0 else 0


def _count_turn_tokens(turn: Any) -> int:
    """Calculate token count for a turn, including request framing for user turns."""
    text = _extract_text(turn)
    t = _estimate_tokens(text)
    if t == 0:
        return 0
    role = turn.get("role", "") if isinstance(turn, dict) else ""
    return t + 18 if role == "user" else t


class MockUsageMetadata:
    """Mock usage metadata container matching Google GenAI SDK interface."""

    def __init__(self, prompt_tokens: int, output_tokens: int) -> None:
        self.prompt_token_count = prompt_tokens
        self.candidates_token_count = output_tokens
        self.total_token_count = prompt_tokens + output_tokens


class MockResponse:
    """Mock LLM response payload."""

    def __init__(self, text: str, prompt_tokens: int, output_tokens: int, finish_reason: str = "STOP", model_version: str = "gemini-2.5-flash-mock") -> None:
        self.text = text
        self.usage_metadata = MockUsageMetadata(prompt_tokens, output_tokens)
        self.finish_reason = finish_reason
        self.model_version = model_version


class MockGeminiChat:
    """Mock chat session simulating multi-turn state and rework iterations."""

    def __init__(self, scenario: str = "rework", raw_history: list[dict[str, Any]] | None = None, model_name: str = "gemini-2.5-flash-mock") -> None:
        self.scenario = scenario
        self.history: list[dict[str, Any]] = list(raw_history) if raw_history else []
        self.turn_count = 0
        self.model_name = model_name

    def send_message(self, prompt: str) -> MockResponse:
        """Emits staged response depending on scenario and retry iteration."""
        self.turn_count += 1
        if "QUALITY GATE" in prompt:
            if self.scenario == "fail":
                resp_text = MISSING_HEADER_MARKDOWN
            elif self.scenario == "latex" and "NONE RECORDED" not in prompt:
                resp_text = CONFORMING_MARKDOWN
            else:
                resp_text = EMPTY_RULE_CONFORMING_MARKDOWN
        else:
            scenario_map = {
                "pass": EMPTY_RULE_CONFORMING_MARKDOWN,
                "fail": MISSING_HEADER_MARKDOWN,
                "latex": UNCLOSED_LATEX_MARKDOWN,
                "empty_math": MISSING_EMPTY_RULE_MARKDOWN,
            }
            resp_text = scenario_map.get(self.scenario, MISSING_HEADER_MARKDOWN)

        hist_tokens = sum(_count_turn_tokens(i) for i in self.history)
        new_prompt_tokens = _estimate_tokens(prompt) + 18
        p_tokens = hist_tokens + new_prompt_tokens
        o_tokens = max(1, _estimate_tokens(resp_text))

        self.history.append({"role": "user", "parts": [{"text": prompt}]})
        self.history.append({"role": "model", "parts": [{"text": resp_text}]})
        return MockResponse(resp_text, p_tokens, o_tokens, model_version=self.model_name)

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
        return MockGeminiChat(
            scenario=self.scenario, raw_history=raw_history, model_name=self.model_name
        )

    def send_prompt(self, chat: Any, prompt: str) -> tuple[str, dict[str, Any]]:
        """Dispatch prompt through mock chat session and extract simulated tokens."""
        response = chat.send_message(prompt)
        tokens = {
            "prompt_tokens": response.usage_metadata.prompt_token_count,
            "output_tokens": response.usage_metadata.candidates_token_count,
            "total_tokens": response.usage_metadata.total_token_count,
            "finish_reason": getattr(response, "finish_reason", "STOP"),
            "model_version": getattr(response, "model_version", self.model_name),
        }
        return response.text, tokens

    def count_tokens(self, contents: Any) -> int:
        """Deterministic token counter matching text density and turn structure."""
        if not contents:
            return 0
        if isinstance(contents, list):
            return sum(_count_turn_tokens(item) for item in contents)
        return _estimate_tokens(_extract_text(contents))
