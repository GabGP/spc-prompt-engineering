"""Configuration settings loaded from environment variables and .env file."""

from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable validation."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API Configuration
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.8-flash"

    # Operator Configuration
    operator_name: str = "operator"

    # Cloud Webhook (Optional)
    sheet_webhook_url: Optional[str] = None

    # Base directory paths
    base_dir: Path = Path(__file__).resolve().parent.parent.parent
    data_dir: Path = base_dir / "data"
    raw_dir: Path = data_dir / "raw"
    inputs_dir: Path = data_dir / "inputs"
    outputs_dir: Path = data_dir / "outputs"
    logs_dir: Path = data_dir / "logs"
    prompts_dir: Path = Path(__file__).resolve().parent / "prompts"

    # File paths
    main_log_file: Path = data_dir / "main_event_log.csv"
    session_cache_file: Path = base_dir / ".session_cache.json"

    def ensure_directories(self) -> None:
        """Ensure all required runtime directories exist."""
        for directory in [
            self.data_dir,
            self.raw_dir,
            self.inputs_dir,
            self.outputs_dir,
            self.logs_dir,
        ]:
            directory.mkdir(parents=True, exist_ok=True)


settings = Settings()
