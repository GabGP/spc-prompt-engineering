"""Unit tests for run sequence tracking against the main CSV ledger."""

from pathlib import Path

from src.state.run_tracker import RunTracker


def test_run_tracker_non_existent_file(tmp_path: Path) -> None:
    """Verify default behavior when CSV file does not exist."""
    tracker = RunTracker(log_path=tmp_path / "non_existent.csv")
    assert tracker.get_next_run_id() == 1
    assert tracker.get_total_runs() == 0
    assert tracker.get_last_run() is None


def test_run_tracker_empty_csv(tmp_path: Path) -> None:
    """Verify behavior on a CSV containing only headers."""
    csv_file = tmp_path / "empty.csv"
    csv_file.write_text("timestamp,run_id,phase\n", encoding="utf-8")

    tracker = RunTracker(log_path=csv_file)
    assert tracker.get_next_run_id() == 1
    assert tracker.get_total_runs() == 0
    assert tracker.get_last_run() is None


def test_run_tracker_with_records(tmp_path: Path) -> None:
    """Verify run_id increment, total count, and last row retrieval."""
    csv_file = tmp_path / "log.csv"
    csv_content = (
        "timestamp,run_id,phase\n"
        "2026-09-02T10:00:00,1,Phase_I\n"
        "2026-09-02T11:00:00,2,Phase_I\n"
        "2026-09-03T09:00:00,5,Phase_I\n"
    )
    csv_file.write_text(csv_content, encoding="utf-8")

    tracker = RunTracker(log_path=csv_file)
    assert tracker.get_next_run_id() == 6
    assert tracker.get_total_runs() == 3

    last_run = tracker.get_last_run()
    assert last_run is not None
    assert last_run["run_id"] == "5"
    assert last_run["phase"] == "Phase_I"


def test_run_tracker_handles_corrupted_rows(tmp_path: Path) -> None:
    """Verify non-integer or malformed run_id values are safely skipped."""
    csv_file = tmp_path / "corrupt.csv"
    csv_content = (
        "timestamp,run_id,phase\n"
        "2026-09-02T10:00:00,abc,Phase_I\n"
        "2026-09-02T11:00:00,3,Phase_I\n"
    )
    csv_file.write_text(csv_content, encoding="utf-8")

    tracker = RunTracker(log_path=csv_file)
    assert tracker.get_next_run_id() == 4
    assert tracker.get_total_runs() == 2


def test_run_tracker_handles_os_errors(tmp_path: Path, monkeypatch) -> None:
    """Verify OSError during CSV read defaults safely."""
    csv_file = tmp_path / "log.csv"
    csv_file.write_text("timestamp,run_id\n1,2\n", encoding="utf-8")
    tracker = RunTracker(log_path=csv_file)

    def mock_open(*args, **kwargs):
        raise OSError("Disk failure")

    monkeypatch.setattr("builtins.open", mock_open)
    assert tracker.get_next_run_id() == 1
    assert tracker.get_total_runs() == 0
    assert tracker.get_last_run() is None
