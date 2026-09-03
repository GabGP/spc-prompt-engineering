"""Unit tests for spc.config module."""

from pathlib import Path

from src.config import Settings


def test_default_settings() -> None:
    """Verify default settings instantiation and types."""
    settings = Settings()
    assert isinstance(settings.gemini_model, str)
    assert settings.gemini_model == "gemini-3.8-flash"
    assert isinstance(settings.base_dir, Path)
    assert isinstance(settings.data_dir, Path)
    assert settings.main_log_file.name == "main_event_log.csv"
    assert settings.prompts_dir.name == "prompts"
    assert settings.session_cache_file.name == "session_cache.json"
    assert settings.cache_dir.name == ".cache"


def test_ensure_directories(mock_settings: Settings) -> None:
    """Verify that ensure_directories creates all required data paths."""
    assert not mock_settings.data_dir.exists()
    assert not mock_settings.inputs_dir.exists()
    assert not mock_settings.cache_dir.exists()

    mock_settings.ensure_directories()

    assert mock_settings.data_dir.exists()
    assert mock_settings.raw_dir.exists()
    assert mock_settings.inputs_dir.exists()
    assert mock_settings.outputs_dir.exists()
    assert mock_settings.logs_dir.exists()
    assert mock_settings.cache_dir.exists()


def test_custom_settings(tmp_path: Path) -> None:
    """Verify overriding settings parameters."""
    custom = Settings(
        gemini_model="gemini-custom",
        operator_name="custom_analyst",
        base_dir=tmp_path,
    )
    assert custom.gemini_model == "gemini-custom"
    assert custom.operator_name == "custom_analyst"
