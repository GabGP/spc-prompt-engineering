"""Configuration settings loaded from environment variables and .env file."""

from pathlib import Path

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
    sheet_webhook_url: str | None = None

    # Base directory path (relative to active project root)
    base_dir: Path = Path(".")

    @property
    def data_dir(self) -> Path:
        """Root data directory."""
        return self.base_dir / "data"

    @property
    def raw_dir(self) -> Path:
        """Directory containing raw textbook source PDFs."""
        return self.data_dir / "raw"

    @property
    def inputs_dir(self) -> Path:
        """Directory containing sliced 1-indexed page PDFs."""
        return self.data_dir / "inputs"

    @property
    def outputs_dir(self) -> Path:
        """Directory containing generated transformation markdowns."""
        return self.data_dir / "outputs"

    @property
    def logs_dir(self) -> Path:
        """Directory containing run telemetry and audit logs."""
        return self.data_dir / "logs"

    @property
    def prompts_dir(self) -> Path:
        """Directory containing prompt templates."""
        return Path(__file__).resolve().parent / "prompts"

    @property
    def main_log_file(self) -> Path:
        """Primary SPC event ledger CSV."""
        return self.data_dir / "main_event_log.csv"

    @property
    def cache_dir(self) -> Path:
        """Root directory for caches."""
        return self.base_dir / ".cache"

    @property
    def session_cache_file(self) -> Path:
        """Multi-turn conversation session cache file."""
        return self.cache_dir / "session_cache.json"

    def ensure_directories(self) -> None:
        """Ensure all required runtime directories exist."""
        for directory in [
            self.data_dir,
            self.raw_dir,
            self.inputs_dir,
            self.outputs_dir,
            self.logs_dir,
            self.cache_dir,
        ]:
            directory.mkdir(parents=True, exist_ok=True)


settings = Settings()
