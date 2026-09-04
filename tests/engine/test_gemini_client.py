"""Unit tests for Gemini client wrapper and token extraction."""

from types import SimpleNamespace
from unittest.mock import MagicMock

from google.genai import types

from src.engine.gemini_client import GeminiClient, extract_token_metadata


def test_extract_token_metadata_missing_usage() -> None:
    """Verify missing usage_metadata yields zeroed token counts."""
    assert extract_token_metadata(None) == {
        "prompt_tokens": 0,
        "output_tokens": 0,
        "thinking_tokens": 0,
        "total_tokens": 0,
        "finish_reason": "STOP",
        "model_version": "",
    }
    assert extract_token_metadata(SimpleNamespace()) == {
        "prompt_tokens": 0,
        "output_tokens": 0,
        "thinking_tokens": 0,
        "total_tokens": 0,
        "finish_reason": "STOP",
        "model_version": "",
    }


def test_extract_token_metadata_present() -> None:
    """Verify extraction from standard usage_metadata object."""
    usage = SimpleNamespace(
        prompt_token_count=250,
        candidates_token_count=120,
        thoughts_token_count=50,
        total_token_count=420,
    )
    resp = SimpleNamespace(usage_metadata=usage)
    tokens = extract_token_metadata(resp)
    assert tokens["prompt_tokens"] == 250
    assert tokens["output_tokens"] == 120
    assert tokens["thinking_tokens"] == 50
    assert tokens["total_tokens"] == 420


def test_extract_token_metadata_with_candidates_and_model_version() -> None:
    """Verify extraction of finish_reason and model_version when candidates present."""
    usage = SimpleNamespace(
        prompt_token_count=100,
        candidates_token_count=50,
        total_token_count=150,
    )
    candidate = SimpleNamespace(finish_reason="MAX_TOKENS")
    resp = SimpleNamespace(
        usage_metadata=usage,
        candidates=[candidate],
        model_version="gemini-2.5-flash-001",
    )
    tokens = extract_token_metadata(resp)
    assert tokens["finish_reason"] == "MAX_TOKENS"
    assert tokens["model_version"] == "gemini-2.5-flash-001"

    enum_reason = SimpleNamespace(name="SAFETY")
    resp_enum = SimpleNamespace(
        usage_metadata=usage,
        candidates=[SimpleNamespace(finish_reason=enum_reason)],
    )
    assert extract_token_metadata(resp_enum)["finish_reason"] == "SAFETY"


def test_extract_token_metadata_computes_total_if_zero() -> None:
    """Verify fallback sum when total_token_count is missing/zero."""
    usage = SimpleNamespace(
        prompt_token_count=150,
        candidates_token_count=50,
        total_token_count=0,
    )
    resp = SimpleNamespace(usage_metadata=usage)
    tokens = extract_token_metadata(resp)
    assert tokens["total_tokens"] == 200


def test_gemini_client_create_chat_and_send_prompt() -> None:
    """Verify chat creation and prompt sending through client."""
    client = GeminiClient(api_key="fake-key", model_name="gemini-test-model")
    client._client = MagicMock()

    mock_chat = MagicMock()
    client._client.chats.create.return_value = mock_chat

    # Test create_chat without history
    chat = client.create_chat()
    assert chat == mock_chat
    client._client.chats.create.assert_called_with(
        model="gemini-test-model", history=None
    )

    # Test create_chat with mixed history (Content, valid dict, invalid item)
    content_obj = types.Content(
        role="user", parts=[types.Part.from_text(text="turn1")]
    )
    history = [
        content_obj,
        {"role": "model", "parts": [{"text": "turn2"}]},
        {"invalid": "unparseable"},
    ]
    client.create_chat(raw_history=history)
    call_args = client._client.chats.create.call_args[1]
    passed_history = call_args["history"]
    assert len(passed_history) == 2

    # Test send_prompt
    mock_resp = SimpleNamespace(
        text="Sample output text",
        usage_metadata=SimpleNamespace(
            prompt_token_count=80,
            candidates_token_count=40,
            total_token_count=120,
        ),
    )
    mock_chat.send_message.return_value = mock_resp

    text, tokens = client.send_prompt(mock_chat, "Process this")
    assert text == "Sample output text"
    assert tokens["prompt_tokens"] == 80
    assert tokens["output_tokens"] == 40


def test_gemini_client_count_tokens() -> None:
    """Verify count_tokens handles empty, text, lists, and API exceptions."""
    client = GeminiClient(api_key="fake-key", model_name="gemini-test-model")
    client._client = MagicMock()

    # Empty contents return 0 immediately without calling client
    assert client.count_tokens("") == 0
    assert client.count_tokens([]) == 0

    # Successful call with text
    client._client.models.count_tokens.return_value = SimpleNamespace(total_tokens=42)
    assert client.count_tokens("Test prompt") == 42

    # Successful call with list of contents
    history = [
        types.Content(role="user", parts=[types.Part.from_text(text="turn1")]),
        {"role": "model", "parts": [{"text": "turn2"}]},
        "raw text item",
    ]
    assert client.count_tokens(history) == 42

    # Error handling returns 0
    client._client.models.count_tokens.side_effect = RuntimeError("API unavailable")
    assert client.count_tokens("Error prone") == 0
