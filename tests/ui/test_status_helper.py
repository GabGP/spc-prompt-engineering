"""Unit tests for status context token resolution helper."""

from unittest.mock import MagicMock, patch

from src.config import Settings
from src.state.session_manager import SessionManager
from src.ui.status_helper import resolve_status_context_tokens


def test_resolve_status_context_tokens_reset_factor() -> None:
    """Verify context tokens is strictly 0 when factor_x1==1 (daily reset)."""
    mgr = MagicMock(spec=SessionManager)
    settings = Settings(gemini_api_key="test-key")
    result = resolve_status_context_tokens(mgr, factor_x1=1, settings=settings)
    assert result == 0
    mgr.load_history.assert_not_called()


def test_resolve_status_context_tokens_empty_history() -> None:
    """Verify context tokens is 0 when history is empty."""
    mgr = MagicMock(spec=SessionManager)
    mgr.load_history.return_value = []
    settings = Settings(gemini_api_key="test-key")
    result = resolve_status_context_tokens(mgr, factor_x1=0, settings=settings)
    assert result == 0


def test_resolve_status_context_tokens_with_injected_client() -> None:
    """Verify exact token count returned when client is provided directly."""
    mgr = MagicMock(spec=SessionManager)
    mgr.load_history.return_value = [{"role": "user", "parts": [{"text": "hello"}]}]
    settings = Settings(gemini_api_key="")
    mock_client = MagicMock()
    mock_client.count_tokens.return_value = 878

    result = resolve_status_context_tokens(
        mgr, factor_x1=0, settings=settings, client=mock_client
    )
    assert result == 878
    mock_client.count_tokens.assert_called_once()


def test_resolve_status_context_tokens_with_settings_api_key() -> None:
    """Verify client created from settings and exact count returned."""
    mgr = MagicMock(spec=SessionManager)
    mgr.load_history.return_value = [
        {"role": "user", "parts": [{"text": "turn1"}]},
        {"role": "model", "parts": [{"text": "turn2"}]},
    ]
    settings = Settings(gemini_api_key="valid-key", gemini_model="gemma-4-31b-it")
    mock_client = MagicMock()
    mock_client.count_tokens.return_value = 512

    with patch("src.ui.status_helper.create_engine_client", return_value=mock_client) as mock_factory:
        result = resolve_status_context_tokens(mgr, factor_x1=0, settings=settings)
        assert result == 512
        mock_factory.assert_called_once_with(
            api_key="valid-key", model_name="gemma-4-31b-it"
        )


def test_resolve_status_context_tokens_api_error_fallback() -> None:
    """Verify heuristic fallback when tokenizer raises error or returns non-positive."""
    mgr = MagicMock(spec=SessionManager)
    mgr.load_history.return_value = [
        {"role": "user", "parts": [{"text": "turn1"}]},
        {"role": "model", "parts": [{"text": "turn2"}]},
    ]
    settings = Settings(gemini_api_key="key")
    mock_client = MagicMock()
    mock_client.count_tokens.side_effect = RuntimeError("API unavailable")

    with patch("src.ui.status_helper.create_engine_client", return_value=mock_client):
        result = resolve_status_context_tokens(mgr, factor_x1=0, settings=settings)
        assert result == 2 * 260


def test_resolve_status_context_tokens_client_factory_error() -> None:
    """Verify heuristic fallback when client creation raises ValueError."""
    mgr = MagicMock(spec=SessionManager)
    mgr.load_history.return_value = [{"role": "user", "parts": [{"text": "turn1"}]}]
    settings = Settings(gemini_api_key="bad-key")

    with patch(
        "src.ui.status_helper.create_engine_client",
        side_effect=ValueError("Invalid key"),
    ):
        result = resolve_status_context_tokens(mgr, factor_x1=0, settings=settings)
        assert result == 260


def test_resolve_status_context_tokens_no_api_key() -> None:
    """Verify heuristic fallback when gemini_api_key is empty."""
    mgr = MagicMock(spec=SessionManager)
    mgr.load_history.return_value = [
        {"role": "user", "parts": [{"text": "turn1"}]},
        {"role": "model", "parts": [{"text": "turn2"}]},
        {"role": "user", "parts": [{"text": "turn3"}]},
    ]
    settings = Settings(gemini_api_key="")
    result = resolve_status_context_tokens(mgr, factor_x1=0, settings=settings)
    assert result == 3 * 260
