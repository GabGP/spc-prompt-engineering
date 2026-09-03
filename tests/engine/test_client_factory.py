"""Unit tests for client factory."""

import pytest

from src.engine.client_factory import create_engine_client
from src.engine.gemini_client import GeminiClient
from src.engine.mock_client import MockGeminiClient


def test_create_engine_client_mock_mode() -> None:
    """Verify mock mode instantiates MockGeminiClient without API key and with model_name."""
    client = create_engine_client(mock_mode="rework", model_name="custom-model")
    assert isinstance(client, MockGeminiClient)
    assert client.scenario == "rework"
    assert client.model_name == "custom-model"


def test_create_engine_client_missing_api_key_raises() -> None:
    """Verify ValueError is raised when live client requested without API key."""
    with pytest.raises(ValueError, match="GEMINI_API_KEY is not configured"):
        create_engine_client(mock_mode=None, api_key="")


def test_create_engine_client_live_client(monkeypatch) -> None:
    """Verify live GeminiClient is created when API key is provided."""
    client = create_engine_client(
        mock_mode=None, api_key="valid-key", model_name="gemini-3.8-flash"
    )
    assert isinstance(client, GeminiClient)
    assert client.api_key == "valid-key"
