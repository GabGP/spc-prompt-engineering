"""Unit tests for multi-turn session persistence manager."""

from pathlib import Path
from pydantic import BaseModel
import pytest

from src.state.session_manager import SessionManager


class MockTurn(BaseModel):
    role: str
    content: str


def test_load_history_resets_when_factor_x1_is_one(tmp_path: Path) -> None:
    """Verify load_history always returns [] when factor_x1 == 1."""
    cache_file = tmp_path / ".session_cache.json"
    cache_file.write_text('[{"role": "user", "text": "hello"}]', encoding="utf-8")

    manager = SessionManager(cache_path=cache_file)
    assert manager.load_history(factor_x1=1) == []


def test_load_history_returns_empty_on_missing_file(tmp_path: Path) -> None:
    """Verify missing cache file returns empty list."""
    manager = SessionManager(cache_path=tmp_path / "non_existent.json")
    assert manager.load_history(factor_x1=0) == []


def test_load_history_handles_corrupt_and_invalid_json(tmp_path: Path) -> None:
    """Verify corrupt JSON or non-list root returns empty list."""
    cache_file = tmp_path / "corrupt.json"
    cache_file.write_text("{invalid json", encoding="utf-8")

    manager = SessionManager(cache_path=cache_file)
    assert manager.load_history(factor_x1=0) == []

    cache_file.write_text('{"key": "value"}', encoding="utf-8")
    assert manager.load_history(factor_x1=0) == []


def test_save_and_load_accumulating_history(tmp_path: Path) -> None:
    """Verify history items serialize and restore correctly when factor_x1 == 0."""
    cache_file = tmp_path / ".session_cache.json"
    manager = SessionManager(cache_path=cache_file)

    items = [
        {"role": "user", "content": "Turn 1"},
        MockTurn(role="model", content="Turn 2"),
        "raw text item",
    ]
    manager.save_history(items, factor_x1=0)

    loaded = manager.load_history(factor_x1=0)
    assert len(loaded) == 3
    assert loaded[0]["content"] == "Turn 1"
    assert loaded[1]["content"] == "Turn 2"
    assert loaded[2]["content"] == "raw text item"
    assert manager.get_history_turn_count() == 3


def test_save_history_clears_cache_when_factor_x1_is_one(tmp_path: Path) -> None:
    """Verify save_history unlinks cache when factor_x1 == 1."""
    cache_file = tmp_path / ".session_cache.json"
    cache_file.write_text("[]", encoding="utf-8")
    assert cache_file.exists()

    manager = SessionManager(cache_path=cache_file)
    manager.save_history([{"role": "user"}], factor_x1=1)
    assert not cache_file.exists()


def test_clear_cache_handles_existing_and_missing(tmp_path: Path) -> None:
    """Verify clear_cache deletes file if present and succeeds silently if absent."""
    cache_file = tmp_path / ".session_cache.json"
    cache_file.write_text("[]", encoding="utf-8")

    manager = SessionManager(cache_path=cache_file)
    manager.clear_cache()
    assert not cache_file.exists()

    # Second call should not raise
    manager.clear_cache()


def test_clear_cache_handles_os_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify clear_cache suppresses OSError if file cannot be unlinked."""
    cache_file = tmp_path / ".session_cache.json"
    cache_file.write_text("[]", encoding="utf-8")
    manager = SessionManager(cache_path=cache_file)

    def mock_unlink(self: Path) -> None:
        raise OSError("Permission denied")

    monkeypatch.setattr(Path, "unlink", mock_unlink)
    manager.clear_cache()
