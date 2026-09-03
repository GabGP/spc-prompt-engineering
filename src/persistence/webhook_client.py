"""Dispatches real-time transformation telemetry to cloud endpoints."""

from typing import Any

import requests

from src.core.models import RunRecord


class WebhookClient:
    """Sends run telemetry payloads to Google Apps Script or external webhook."""

    def __init__(
        self, webhook_url: str | None = None, timeout_sec: float = 5.0
    ) -> None:
        self.webhook_url = (
            webhook_url.strip() if webhook_url and webhook_url.strip() else None
        )
        self.timeout_sec = timeout_sec

    def dispatch(self, record: RunRecord) -> bool:
        """Dispatch record dictionary to configured webhook. Returns True on success."""
        if not self.webhook_url:
            return False

        try:
            payload: dict[str, Any] = record.to_csv_dict()
            response = requests.post(
                self.webhook_url, json=payload, timeout=self.timeout_sec
            )
            return response.status_code in (200, 201, 204)
        except requests.RequestException:
            return False
