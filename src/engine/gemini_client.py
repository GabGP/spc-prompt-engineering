"""Google GenAI client wrapper and token metadata extraction."""

from typing import Any

from google import genai
from google.genai import types


def extract_token_metadata(response: Any) -> dict[str, Any]:
    """Extract prompt, candidate, total token usage counts, and finish reason from response."""
    usage = getattr(response, "usage_metadata", None)
    prompt = getattr(usage, "prompt_token_count", 0) or 0 if usage else 0
    output = getattr(usage, "candidates_token_count", 0) or 0 if usage else 0
    total = getattr(usage, "total_token_count", 0) or (prompt + output) if usage else 0

    finish_reason = "STOP"
    candidates = getattr(response, "candidates", None)
    if candidates and len(candidates) > 0:
        raw_reason = getattr(candidates[0], "finish_reason", "STOP")
        finish_reason = str(getattr(raw_reason, "name", raw_reason)) or "STOP"

    model_version = str(getattr(response, "model_version", "") or "")

    return {
        "prompt_tokens": prompt,
        "output_tokens": output,
        "total_tokens": total,
        "finish_reason": finish_reason,
        "model_version": model_version,
    }


class GeminiClient:
    """Wrapper around google.genai.Client for chat management and token extraction."""

    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash") -> None:
        self.api_key = api_key
        self.model_name = model_name
        self._client = genai.Client(api_key=api_key)

    def create_chat(self, raw_history: list[dict[str, Any]] | None = None) -> Any:
        """Create a new Chat session with optional restored history."""
        parsed_history: list[types.ContentOrDict] = []
        if raw_history:
            for item in raw_history:
                try:
                    if isinstance(item, types.Content):
                        parsed_history.append(item)
                    elif isinstance(item, dict):
                        parsed_history.append(types.Content.model_validate(item))
                except (ValueError, TypeError, KeyError, AttributeError):
                    pass

        history_arg: list[types.ContentOrDict] | None = (
            parsed_history if parsed_history else None
        )
        return self._client.chats.create(
            model=self.model_name,
            history=history_arg,
        )

    def send_prompt(self, chat: Any, prompt: str) -> tuple[str, dict[str, Any]]:
        """Send a prompt through an active chat session; return emitted text and tokens."""
        response = chat.send_message(prompt)
        text = getattr(response, "text", "") or ""
        tokens = extract_token_metadata(response)
        if not tokens.get("model_version"):
            tokens["model_version"] = self.model_name
        return text, tokens

    def count_tokens(self, contents: Any) -> int:
        """Count tokens for contents using Gemini API."""
        if not contents:
            return 0
        try:
            parsed = contents
            if isinstance(contents, list):
                parsed = []
                for item in contents:
                    if isinstance(item, types.Content):
                        parsed.append(item)
                    elif isinstance(item, dict):
                        parsed.append(types.Content.model_validate(item))
                    else:
                        parsed.append(str(item))
            res = self._client.models.count_tokens(
                model=self.model_name,
                contents=parsed,
            )
            return getattr(res, "total_tokens", 0) or 0
        except (TypeError, ValueError, KeyError, AttributeError, RuntimeError, OSError):
            return 0
