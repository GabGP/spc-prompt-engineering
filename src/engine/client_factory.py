"""Factory for creating live or mock LLM clients based on configuration."""

from typing import Any

from src.engine.gemini_client import GeminiClient
from src.engine.mock_client import MockGeminiClient


def create_engine_client(
    mock_mode: str | None = None,
    api_key: str = "",
    model_name: str = "gemini-3.8-flash",
) -> Any:
    """Instantiate appropriate LLM client for live or staged execution."""
    if mock_mode:
        return MockGeminiClient(scenario=mock_mode, model_name=model_name)

    if not api_key:
        raise ValueError("GEMINI_API_KEY is not configured.")

    return GeminiClient(api_key=api_key, model_name=model_name)
