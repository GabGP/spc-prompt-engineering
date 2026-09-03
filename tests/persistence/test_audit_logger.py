"""Unit tests for forensic audit logger and markdown output storage."""

import json
from pathlib import Path

from src.core.models import AuditPayload
from src.persistence.audit_logger import AuditLogger


def test_save_audit_payload(tmp_path: Path) -> None:
    """Verify forensic JSON payload is persisted with standard formatting."""
    logs_dir = tmp_path / "logs"
    outputs_dir = tmp_path / "outputs"
    logger = AuditLogger(logs_dir=logs_dir, outputs_dir=outputs_dir)

    payload = AuditPayload(
        run_id=7,
        timestamp="2026-09-03T12:00:00Z",
        phase="Phase_I",
        operator="analyst_test",
        input_file="page_007.pdf",
        request_prompt="Prompt content",
        final_output_markdown="## Conforming Markdown",
        total_cycle_time_sec=6.234,
        rework_count=0,
        conforming=True,
        inspection_events=[{"iteration": 0, "conforming": True}],
        raw_usage_metadata={"prompt_tokens": 500, "output_tokens": 200},
    )

    saved_file = logger.save_audit(payload)
    assert saved_file == logs_dir / "run_007_audit.json"
    assert saved_file.exists()

    loaded = json.loads(saved_file.read_text(encoding="utf-8"))
    assert loaded["run_id"] == 7
    assert loaded["request_prompt"] == "Prompt content"
    assert loaded["conforming"] is True


def test_save_output_markdown(tmp_path: Path) -> None:
    """Verify accepted markdown is written to run_{id:03d}.md."""
    logs_dir = tmp_path / "logs"
    outputs_dir = tmp_path / "outputs"
    logger = AuditLogger(logs_dir=logs_dir, outputs_dir=outputs_dir)

    saved_file = logger.save_output_markdown(3, "# Analysis\n\nContent")
    assert saved_file == outputs_dir / "run_003.md"
    assert saved_file.exists()
    assert saved_file.read_text(encoding="utf-8") == "# Analysis\n\nContent"
