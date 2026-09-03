"""Writes forensic audit JSON payloads and accepted markdown outputs to disk."""

from pathlib import Path

from src.core.models import AuditPayload


class AuditLogger:
    """Persists detailed run execution forensic logs and output artifacts."""

    def __init__(
        self,
        logs_dir: Path | str = Path("data/logs"),
        outputs_dir: Path | str = Path("data/outputs"),
    ) -> None:
        self.logs_dir = Path(logs_dir)
        self.outputs_dir = Path(outputs_dir)

    def save_audit(self, payload: AuditPayload) -> Path:
        """Write forensic AuditPayload to data/logs/run_{run_id:03d}_audit.json."""
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        target = self.logs_dir / f"run_{payload.run_id:03d}_audit.json"
        target.write_text(payload.model_dump_json(indent=2), encoding="utf-8")
        return target

    def save_output_markdown(self, run_id: int, markdown_content: str) -> Path:
        """Write accepted markdown documentation to data/outputs/run_{run_id:03d}.md."""
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        target = self.outputs_dir / f"run_{run_id:03d}.md"
        target.write_text(markdown_content, encoding="utf-8")
        return target
