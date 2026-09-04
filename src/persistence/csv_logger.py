"""Appends experimental transformation records to the primary CSV ledger."""

import csv
from pathlib import Path

from src.core.models import RunRecord

CSV_FIELDNAMES: tuple[str, ...] = (
    "run_id",
    "timestamp",
    "phase",
    "operator",
    "model_version",
    "input_file",
    "factor_x1",
    "factor_x2",
    "context_tokens",
    "instruction_tokens",
    "page_tokens",
    "framing_tokens",
    "rework_tokens",
    "prompt_tokens",
    "output_tokens",
    "thinking_tokens",
    "total_tokens",
    "conforming",
    "rework_cycles",
    "finish_reason",
    "cycle_time_sec",
    "assignable_cause",
)


class CSVLogger:
    """Appends structured RunRecord telemetry to data/main_event_log.csv."""

    def __init__(self, log_path: Path | str = Path("data/main_event_log.csv")) -> None:
        self.log_path = Path(log_path)

    def log_run(self, record: RunRecord) -> Path:
        """Append a RunRecord to the CSV ledger, creating headers if file is new."""
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        file_exists = self.log_path.exists() and self.log_path.stat().st_size > 0

        with open(self.log_path, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
            if not file_exists:
                writer.writeheader()
            writer.writerow(record.to_csv_dict())

        return self.log_path
