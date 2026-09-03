"""Unit tests for primary CSV event logger."""

import csv
from datetime import UTC, datetime
from pathlib import Path

from src.core.models import RunRecord
from src.persistence.csv_logger import CSV_FIELDNAMES, CSVLogger


def make_record(run_id: int, phase: str = "Phase_I") -> RunRecord:
    return RunRecord(
        timestamp=datetime.now(UTC),
        run_id=run_id,
        input_file="page_001.pdf",
        phase=phase,
        factor_x1=0,
        factor_x2=0,
        cycle_time_sec=5.234,
        prompt_tokens=450,
        output_tokens=320,
        conforming=1,
        rework_cycles=0,
        assignable_cause="NONE",
        operator="analyst_test",
    )


def test_csv_logger_creates_file_and_header(tmp_path: Path) -> None:
    """Verify logger creates CSV with correct header on first run."""
    csv_path = tmp_path / "data" / "main_event_log.csv"
    logger = CSVLogger(log_path=csv_path)

    record = make_record(1)
    logger.log_run(record)

    assert csv_path.exists()
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        row = next(reader)

    assert tuple(header) == CSV_FIELDNAMES
    assert row[1] == "1"
    assert row[2] == "page_001.pdf"
    assert row[3] == "Phase_I"
    assert row[12] == "analyst_test"


def test_csv_logger_appends_without_duplicate_header(tmp_path: Path) -> None:
    """Verify successive writes append rows without writing headers again."""
    csv_path = tmp_path / "main_event_log.csv"
    logger = CSVLogger(log_path=csv_path)

    logger.log_run(make_record(1))
    logger.log_run(make_record(2))

    with open(csv_path, mode="r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    # 1 header line + 2 data rows = 3 lines
    assert len(lines) == 3
    assert lines[0].startswith("timestamp,run_id,input_file")
    assert ",1,page_001.pdf,Phase_I," in lines[1]
    assert ",2,page_001.pdf,Phase_I," in lines[2]
