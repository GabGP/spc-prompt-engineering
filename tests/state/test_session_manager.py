"""Unit tests for multi-turn session persistence manager."""

import json
from pathlib import Path

import pytest
from pydantic import BaseModel

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
    """Verify missing cache and backup files return empty list."""
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
    """Verify history items serialize to primary and backup targets."""
    cache_file = tmp_path / ".session_cache.json"
    backup_file = tmp_path / ".session_cache.bak"
    manager = SessionManager(cache_path=cache_file, backup_path=backup_file)

    items = [
        {"role": "user", "content": "Turn 1"},
        MockTurn(role="model", content="Turn 2"),
        "raw text item",
    ]
    manager.save_history(items, factor_x1=0)

    assert cache_file.exists()
    assert backup_file.exists()

    loaded = manager.load_history(factor_x1=0)
    assert len(loaded) == 3
    assert loaded[0]["content"] == "Turn 1"
    assert loaded[1]["content"] == "Turn 2"
    assert loaded[2]["content"] == "raw text item"
    assert manager.get_history_turn_count() == 3


def test_load_history_recovers_from_backup_file(tmp_path: Path) -> None:
    """Verify automatic recovery from .bak file if primary cache is missing."""
    cache_file = tmp_path / ".session_cache.json"
    backup_file = tmp_path / ".session_cache.bak"
    manager = SessionManager(cache_path=cache_file, backup_path=backup_file)

    backup_data = [{"role": "user", "content": "Recovered turn"}]
    backup_file.write_text(json.dumps(backup_data), encoding="utf-8")

    # Primary does not exist yet
    assert not cache_file.exists()

    loaded = manager.load_history(factor_x1=0)
    assert len(loaded) == 1
    assert loaded[0]["content"] == "Recovered turn"
    # Primary cache was restored
    assert cache_file.exists()


def test_save_history_clears_cache_when_factor_x1_is_one(tmp_path: Path) -> None:
    """Verify save_history unlinks primary cache but preserves backup when factor_x1 == 1."""
    cache_file = tmp_path / ".session_cache.json"
    backup_file = tmp_path / ".session_cache.bak"
    cache_file.write_text("[]", encoding="utf-8")
    backup_file.write_text("[]", encoding="utf-8")

    manager = SessionManager(cache_path=cache_file, backup_path=backup_file)
    manager.save_history([{"role": "user"}], factor_x1=1)
    assert not cache_file.exists()
    assert backup_file.exists()

    manager.clear_cache(clear_backup=True)
    assert not backup_file.exists()


def test_clear_cache_handles_existing_and_missing(tmp_path: Path) -> None:
    """Verify clear_cache deletes files if present and succeeds silently if absent."""
    cache_file = tmp_path / ".session_cache.json"
    cache_file.write_text("[]", encoding="utf-8")

    manager = SessionManager(cache_path=cache_file)
    manager.clear_cache()
    assert not cache_file.exists()
    manager.clear_cache()


def test_error_handling_suppresses_os_errors(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify clear_cache and save_history suppress OSError."""
    cache_file = tmp_path / ".session_cache.json"
    cache_file.write_text("[]", encoding="utf-8")
    manager = SessionManager(cache_path=cache_file)

    def mock_unlink(self: Path) -> None:
        raise OSError("Unlink failure")

    monkeypatch.setattr(Path, "unlink", mock_unlink)
    manager.clear_cache()

    def mock_write_text(self: Path, *args, **kwargs) -> None:
        raise OSError("Write failure")

    monkeypatch.setattr(Path, "write_text", mock_write_text)
    manager.save_history([{"role": "user"}], factor_x1=0)


def test_rebuild_from_audit_logs(tmp_path: Path) -> None:
    """Verify reconstruction of multi-turn session from audit JSON files."""
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir(parents=True)
    cache_file = tmp_path / ".session_cache.json"
    manager = SessionManager(cache_path=cache_file)

    # Empty dir returns empty
    assert manager.rebuild_from_audit_logs(tmp_path / "non_existent") == []
    assert manager.rebuild_from_audit_logs(logs_dir) == []

    # Write sample audit records
    audit_1 = {
        "run_id": 1,
        "phase": "Phase_I",
        "request_prompt": "Analyze page 1",
        "final_output_markdown": "Synthesis 1",
    }
    audit_2 = {
        "run_id": 2,
        "phase": "Phase_I",
        "input_file": "page_002.pdf",
        "request_prompt": "",
        "final_output_markdown": "Synthesis 2",
    }
    audit_3 = {
        "run_id": 3,
        "phase": "Phase_II",  # Should be filtered out
        "request_prompt": "Analyze page 3",
        "final_output_markdown": "Synthesis 3",
    }

    (logs_dir / "run_001_audit.json").write_text(json.dumps(audit_1), encoding="utf-8")
    (logs_dir / "run_002_audit.json").write_text(json.dumps(audit_2), encoding="utf-8")
    (logs_dir / "run_003_audit.json").write_text(json.dumps(audit_3), encoding="utf-8")
    (logs_dir / "run_corrupt_audit.json").write_text("{bad json", encoding="utf-8")

    history = manager.rebuild_from_audit_logs(logs_dir, phase="Phase_I")
    assert len(history) == 4
    assert history[0]["parts"][0]["text"] == "Analyze page 1"
    assert history[1]["parts"][0]["text"] == "Synthesis 1"
    assert "page_002.pdf" in history[2]["parts"][0]["text"]
    assert history[3]["parts"][0]["text"] == "Synthesis 2"

    # Verify cache file was created and contains the reconstructed history
    assert cache_file.exists()
    assert manager.get_history_turn_count() == 4


def test_load_history_recovers_from_audit_logs_fallback(tmp_path: Path) -> None:
    """Verify load_history automatically rebuilds from logs_dir if cache and backup missing."""
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir(parents=True)
    audit = {
        "run_id": 1,
        "phase": "Phase_I",
        "request_prompt": "Fallback Prompt",
        "final_output_markdown": "Fallback Output",
    }
    (logs_dir / "run_001_audit.json").write_text(json.dumps(audit), encoding="utf-8")
    manager = SessionManager(
        cache_path=tmp_path / "missing.json",
        backup_path=tmp_path / "missing.bak",
        logs_dir=logs_dir,
    )
    loaded = manager.load_history(factor_x1=0)
    assert len(loaded) == 2
    assert loaded[0]["parts"][0]["text"] == "Fallback Prompt"


def test_rebuild_from_audit_logs_with_iterations(tmp_path: Path) -> None:
    """Verify reconstruction of full multi-turn transcript when iterations are present."""
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir(parents=True)
    cache_file = tmp_path / ".session_cache.json"
    manager = SessionManager(cache_path=cache_file)

    audit = {
        "run_id": 1,
        "phase": "Phase_I",
        "iterations": [
            {"prompt_text": "Initial Prompt", "response_text": "Defective"},
            {"prompt_text": "Rework Prompt", "response_text": "Conforming"},
        ],
    }
    (logs_dir / "run_001_audit.json").write_text(json.dumps(audit), encoding="utf-8")

    history = manager.rebuild_from_audit_logs(logs_dir, phase="Phase_I")
    assert len(history) == 4
    assert history[0]["parts"][0]["text"] == "Initial Prompt"
    assert history[1]["parts"][0]["text"] == "Defective"
    assert history[2]["parts"][0]["text"] == "Rework Prompt"
    assert history[3]["parts"][0]["text"] == "Conforming"
