"""Unit tests for webhook dispatcher client."""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
import requests

from src.core.models import RunRecord
from src.persistence.webhook_client import WebhookClient


def make_record() -> RunRecord:
    return RunRecord(
        timestamp=datetime.now(UTC),
        run_id=1,
        phase="Phase_I",
        factor_x1=0,
        factor_x2=0,
        cycle_time_sec=4.5,
        prompt_tokens=300,
        output_tokens=150,
        conforming=1,
        rework_cycles=0,
        operator="op",
    )


def test_webhook_disabled_when_url_empty() -> None:
    """Verify dispatch returns False immediately when no webhook URL is configured."""
    client_none = WebhookClient(webhook_url=None)
    assert not client_none.dispatch(make_record())

    client_empty = WebhookClient(webhook_url="   ")
    assert not client_empty.dispatch(make_record())


def test_webhook_dispatch_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify dispatch returns True on HTTP 200/201/204 response."""
    client = WebhookClient(webhook_url="https://example.com/webhook")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    monkeypatch.setattr(requests, "post", lambda *args, **kwargs: mock_resp)

    assert client.dispatch(make_record())


def test_webhook_dispatch_server_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify dispatch returns False on HTTP 500 error."""
    client = WebhookClient(webhook_url="https://example.com/webhook")

    mock_resp = MagicMock()
    mock_resp.status_code = 500
    monkeypatch.setattr(requests, "post", lambda *args, **kwargs: mock_resp)

    assert not client.dispatch(make_record())


def test_webhook_dispatch_request_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify dispatch returns False when requests raises a connection error."""
    client = WebhookClient(webhook_url="https://example.com/webhook")

    def mock_post(*args, **kwargs):
        raise requests.ConnectionError("Network unreachable")

    monkeypatch.setattr(requests, "post", mock_post)
    assert not client.dispatch(make_record())
