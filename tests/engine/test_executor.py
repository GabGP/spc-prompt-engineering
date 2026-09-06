"""Unit tests for TransformationExecutor orchestration and rework loop."""

from pathlib import Path
from unittest.mock import MagicMock

from src.core.models import ExecutionResult
from src.engine.executor import TransformationExecutor
from src.engine.gemini_client import GeminiClient
from src.persistence.audit_logger import AuditLogger
from src.persistence.csv_logger import CSVLogger
from src.persistence.webhook_client import WebhookClient
from src.state.session_manager import SessionManager
from src.validation.inspector import QualityInspector

CONFORMING_OUTPUT = """
## Core Synthesis
Process summary here.

## Technical Taxonomy
- Term 1: Definition

## Analytical Formulations
$$Y = \\alpha_0 + \\alpha_1 X_1$$
"""

NON_CONFORMING_OUTPUT = """
## Core Synthesis
Missing other mandatory headers.
"""


def test_executor_conforming_run_first_try(tmp_path: Path) -> None:
    """Verify execution succeeds on first iteration when output is conforming."""
    mock_gemini = MagicMock(spec=GeminiClient)
    mock_chat = MagicMock()
    mock_chat.get_history.return_value = [{"role": "user"}]
    mock_gemini.create_chat.return_value = mock_chat
    mock_gemini.send_prompt.return_value = (
        CONFORMING_OUTPUT,
        {"prompt_tokens": 400, "output_tokens": 200, "total_tokens": 600},
    )

    csv_log = tmp_path / "main_event_log.csv"
    logs_dir = tmp_path / "logs"
    outputs_dir = tmp_path / "outputs"
    session_cache = tmp_path / ".session_cache.json"

    executor = TransformationExecutor(
        gemini_client=mock_gemini,
        inspector=QualityInspector(),
        session_manager=SessionManager(cache_path=session_cache),
        csv_logger=CSVLogger(log_path=csv_log),
        audit_logger=AuditLogger(logs_dir=logs_dir, outputs_dir=outputs_dir),
        webhook_client=WebhookClient(webhook_url=None),
    )

    result = executor.execute_run(
        run_id=1,
        page_text="Sample raw textbook page text.",
        input_filename="page_001.pdf",
        phase="Phase_I",
        factor_x1=0,
        factor_x2=0,
        operator="analyst_test",
        has_math_in_input=True,
    )

    assert isinstance(result, ExecutionResult)
    assert result.record.run_id == 1
    assert result.record.conforming == 1
    assert result.record.rework_cycles == 0
    assert result.record.cycle_time_sec > 0
    assert result.record.timestamp.tzinfo is not None
    assert result.defect_report.is_conforming
    assert result.audit_payload.conforming

    # Verify persistence occurred
    assert csv_log.exists()
    assert (logs_dir / "run_001_audit.json").exists()
    assert (outputs_dir / "run_001.md").exists()
    assert session_cache.exists()


def test_executor_rework_reflection_loop_recovery(tmp_path: Path) -> None:
    """Verify defect detection triggers rework prompt and succeeds on rework."""
    mock_gemini = MagicMock(spec=GeminiClient)
    mock_chat = MagicMock()
    mock_chat.get_history.return_value = []
    mock_gemini.create_chat.return_value = mock_chat

    # First attempt fails (non-conforming); second attempt succeeds
    mock_gemini.send_prompt.side_effect = [
        (NON_CONFORMING_OUTPUT, {"prompt_tokens": 400, "output_tokens": 100, "thinking_tokens": 50}),
        (CONFORMING_OUTPUT, {"prompt_tokens": 600, "output_tokens": 250, "thinking_tokens": 75}),
    ]

    csv_log = tmp_path / "main_event_log.csv"
    executor = TransformationExecutor(
        gemini_client=mock_gemini,
        csv_logger=CSVLogger(log_path=csv_log),
        audit_logger=AuditLogger(
            logs_dir=tmp_path / "logs", outputs_dir=tmp_path / "outputs"
        ),
        session_manager=SessionManager(cache_path=tmp_path / ".cache.json"),
    )

    result = executor.execute_run(
        run_id=2,
        page_text="Math section with formulas.",
        input_filename="page_002.pdf",
        phase="Phase_I",
        factor_x1=0,
        factor_x2=1,  # SOP schema enabled
        operator="analyst_test",
        has_math_in_input=True,
    )

    assert result.record.rework_cycles == 1
    assert result.record.conforming == 1
    assert result.record.prompt_tokens == 600  # prompt tokens of final accepted iteration
    assert result.record.thinking_tokens == 125  # 50 + 75 cumulative
    assert result.record.rework_tokens == 200  # 600 - 400
    assert result.record.total_tokens == 975   # 600 + 250 + 125
    assert len(result.audit_payload.inspection_events) == 2
    assert len(result.audit_payload.iterations) == 2
    assert result.audit_payload.iterations[0].thinking_tokens == 50
    assert result.audit_payload.iterations[1].thinking_tokens == 75
    assert result.audit_payload.cumulative_tokens["total_api_prompt_tokens"] == 1000
    assert result.audit_payload.cumulative_tokens["total_api_output_tokens"] == 350
    assert result.audit_payload.cumulative_tokens["total_api_thinking_tokens"] == 125
    assert result.audit_payload.cumulative_tokens["total_api_tokens"] == 1475


def test_executor_exceeding_max_reworks(tmp_path: Path) -> None:
    """Verify run terminates non-conforming when max rework limit is exhausted."""
    mock_gemini = MagicMock(spec=GeminiClient)
    mock_chat = MagicMock()
    mock_gemini.create_chat.return_value = mock_chat

    # Always return defective output
    mock_gemini.send_prompt.return_value = (
        NON_CONFORMING_OUTPUT,
        {"prompt_tokens": 200, "output_tokens": 50},
    )

    session_cache = tmp_path / ".cache.json"
    executor = TransformationExecutor(
        gemini_client=mock_gemini,
        csv_logger=CSVLogger(log_path=tmp_path / "log.csv"),
        audit_logger=AuditLogger(
            logs_dir=tmp_path / "logs", outputs_dir=tmp_path / "outputs"
        ),
        session_manager=SessionManager(cache_path=session_cache),
    )

    result = executor.execute_run(
        run_id=3,
        page_text="Content",
        input_filename="page_003.pdf",
        phase="Phase_II",
        factor_x1=1,
        factor_x2=0,
        operator="op",
        max_reworks=2,
    )

    assert result.record.conforming == 0
    assert result.record.rework_cycles == 2
    assert not result.defect_report.is_conforming
    assert result.record.assignable_cause == "REWORK_LIMIT_EXCEEDED"
    assert not session_cache.exists()


def test_executor_exceeding_max_reworks_accumulates_history(tmp_path: Path) -> None:
    """Verify non-conforming run persists turns in session cache when factor_x1==0."""
    mock_gemini = MagicMock(spec=GeminiClient)
    mock_chat = MagicMock()
    mock_gemini.create_chat.return_value = mock_chat

    mock_gemini.send_prompt.return_value = (
        NON_CONFORMING_OUTPUT,
        {"prompt_tokens": 200, "output_tokens": 50},
    )

    session_cache = tmp_path / ".cache.json"
    session_mgr = SessionManager(cache_path=session_cache)
    executor = TransformationExecutor(
        gemini_client=mock_gemini,
        csv_logger=CSVLogger(log_path=tmp_path / "log.csv"),
        audit_logger=AuditLogger(
            logs_dir=tmp_path / "logs", outputs_dir=tmp_path / "outputs"
        ),
        session_manager=session_mgr,
    )

    result = executor.execute_run(
        run_id=4,
        page_text="Content",
        input_filename="page_004.pdf",
        phase="Phase_I",
        factor_x1=0,
        factor_x2=0,
        operator="op",
        max_reworks=2,
    )

    assert result.record.conforming == 0
    assert result.record.rework_cycles == 2
    assert session_cache.exists()
    history = session_mgr.load_history(factor_x1=0)
    # Initial attempt (user + model) + 2 reworks (2 * (user + model)) = 6 turns
    assert len(history) == 6


def test_executor_token_fallback_calculation(tmp_path: Path) -> None:
    """Verify fallback token calculation when client has no count_tokens."""
    mock_gemini = MagicMock(spec=[])
    mock_chat = MagicMock()
    mock_gemini.create_chat = MagicMock(return_value=mock_chat)
    mock_gemini.send_prompt = MagicMock(
        return_value=(
            CONFORMING_OUTPUT,
            {"prompt_tokens": 500, "output_tokens": 150},
        )
    )

    session_mgr = SessionManager(cache_path=tmp_path / ".cache.json")
    session_mgr.save_history([{"role": "user", "parts": [{"text": "Prior"}]}], factor_x1=0)

    executor = TransformationExecutor(
        gemini_client=mock_gemini,
        session_manager=session_mgr,
        csv_logger=CSVLogger(log_path=tmp_path / "log.csv"),
        audit_logger=AuditLogger(logs_dir=tmp_path / "logs", outputs_dir=tmp_path / "outputs"),
    )

    result = executor.execute_run(
        run_id=10,
        page_text="Some text",
        input_filename="page_010.pdf",
        phase="Phase_I",
        factor_x1=0,
        factor_x2=0,
        operator="analyst",
        has_math_in_input=True,
    )

    assert result.record.prompt_tokens == 500
    assert result.record.context_tokens == 0
    assert result.record.page_tokens == 0
    assert result.record.framing_tokens == 500
    assert result.record.instruction_tokens == 0
    assert result.record.total_tokens == 650
