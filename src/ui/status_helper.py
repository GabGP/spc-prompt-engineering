"""Helper for calculating context tokens for status dashboard."""

from typing import Any

from src.config import Settings
from src.engine.client_factory import create_engine_client
from src.state.session_manager import SessionManager


def resolve_status_context_tokens(
    session_mgr: SessionManager,
    factor_x1: int,
    settings: Settings,
    client: Any | None = None,
) -> int:
    """Resolve exact tokenizer context token count with heuristic fallback.

    Args:
        session_mgr: SessionManager instance managing session cache.
        factor_x1: Context buffer factor (0: accumulating, 1: daily reset).
        settings: Application settings containing API key and model name.
        client: Optional pre-instantiated LLM client with count_tokens method.

    Returns:
        Exact token count from Gemini tokenizer if available, otherwise heuristic estimate.
    """
    if factor_x1 != 0:
        return 0

    history = session_mgr.load_history(factor_x1=0)
    if not history:
        return 0

    engine_client = client
    if engine_client is None and settings.gemini_api_key:
        try:
            engine_client = create_engine_client(
                api_key=settings.gemini_api_key,
                model_name=settings.gemini_model,
            )
        except (ValueError, Exception):
            engine_client = None

    if engine_client is not None:
        count_fn = getattr(engine_client, "count_tokens", None)
        if callable(count_fn):
            try:
                counted = count_fn(history)
                if isinstance(counted, (int, float)) and counted > 0:
                    return int(counted)
            except Exception:
                pass

    return len(history) * 260
