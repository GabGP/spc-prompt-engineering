"""Google GenAI client wrapper and token metadata extraction."""

from typing import Any

from google import genai
from google.genai import types


def extract_token_metadata(response: Any) -> dict[str, int]:
    """Extract prompt, candidate, and total token usage counts from response."""
    usage = getattr(response, "usage_metadata", None)
    if usage is None:
        return {"prompt_tokens": 0, "output_tokens": 0, "total_tokens": 0}

    prompt = getattr(usage, "prompt_token_count", 0) or 0
    output = getattr(usage, "candidates_token_count", 0) or 0
    total = getattr(usage, "total_token_count", 0) or (prompt + output)

    return {
        "prompt_tokens": prompt,
        "output_tokens": output,
        "total_tokens": total,
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

    def send_prompt(self, chat: Any, prompt: str) -> tuple[str, dict[str, int]]:
        """Send a prompt through an active chat session; return emitted text and tokens."""
        response = chat.send_message(prompt)
        text = getattr(response, "text", "") or ""
        tokens = extract_token_metadata(response)
        return text, tokens
