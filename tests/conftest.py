"""Shared pytest fixtures for the SPC project test suite."""

import pytest
from pathlib import Path
from spc.config import Settings


@pytest.fixture
def temp_workspace(tmp_path: Path) -> Path:
    """Provide an isolated temporary workspace directory."""
    return tmp_path


@pytest.fixture
def mock_settings(tmp_path: Path) -> Settings:
    """Provide a Settings instance pointing to temporary isolated paths."""
    data_dir = tmp_path / "data"
    return Settings(
        gemini_api_key="test_api_key_mock",
        gemini_model="gemini-3.8-flash",
        operator_name="test_operator",
        base_dir=tmp_path,
        data_dir=data_dir,
        raw_dir=data_dir / "raw",
        inputs_dir=data_dir / "inputs",
        outputs_dir=data_dir / "outputs",
        logs_dir=data_dir / "logs",
        main_log_file=data_dir / "main_event_log.csv",
        session_cache_file=tmp_path / ".session_cache.json",
    )
