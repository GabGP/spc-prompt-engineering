"""Appends experimental transformation records to the primary CSV ledger."""

import csv
from pathlib import Path

from src.core.models import RunRecord

CSV_FIELDNAMES: tuple[str, ...] = (
    "timestamp",
    "run_id",
    "phase",
    "factor_x1",
    "factor_x2",
    "cycle_time_sec",
    "prompt_tokens",
    "output_tokens",
    "conforming",
    "rework_cycles",
    "assignable_cause",
    "operator",
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
