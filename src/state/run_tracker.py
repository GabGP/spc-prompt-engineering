"""Discovers sequential run identifiers and historical run depth from CSV."""

import csv
from pathlib import Path


class RunTracker:
    """Tracks experimental run sequence numbers against the primary CSV ledger."""

    def __init__(self, log_path: Path | str = Path("data/main_event_log.csv")) -> None:
        self.log_path = Path(log_path)

    def get_next_run_id(self) -> int:
        """Inspect the CSV ledger and return the next sequential run ID (1-indexed)."""
        if not self.log_path.exists():
            return 1

        run_ids: list[int] = []
        try:
            with open(self.log_path, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    raw_id = row.get("run_id")
                    if raw_id is not None and raw_id.strip().isdigit():
                        run_ids.append(int(raw_id.strip()))
        except (OSError, csv.Error):
            return 1

        return max(run_ids) + 1 if run_ids else 1

    def get_total_runs(self) -> int:
        """Count the total number of executed runs logged in the ledger."""
        if not self.log_path.exists():
            return 0

        count = 0
        try:
            with open(self.log_path, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("run_id"):
                        count += 1
        except (OSError, csv.Error):
            return 0

        return count

    def get_last_run(self) -> dict[str, str] | None:
        """Retrieve the last recorded run row from the ledger, if any exists."""
        if not self.log_path.exists():
            return None

        last_row: dict[str, str] | None = None
        try:
            with open(self.log_path, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row:
                        last_row = row
        except (OSError, csv.Error):
            return None

        return last_row
