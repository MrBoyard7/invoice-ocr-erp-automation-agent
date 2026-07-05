"""Client for triggering Zapier workflows via webhooks.

Zapier's "Webhooks by Zapier" trigger accepts an HTTP POST with a JSON body
and fans that event out to any number of connected apps (email, Slack,
spreadsheets, the ERP's own Zapier app, etc). This client is intentionally
thin: its only responsibility is delivering a well-formed event payload.
"""

from __future__ import annotations

import logging
from typing import Any

import requests

from invoice_automation.config import ZapierSettings
from invoice_automation.exceptions import AutomationError

logger = logging.getLogger(__name__)


class ZapierClient:
    """Sends invoice-processing events to a configured Zapier webhook."""

    def __init__(self, settings: ZapierSettings, session: requests.Session | None = None) -> None:
        self._settings = settings
        self._session = session or requests.Session()

    def send_event(self, event_name: str, payload: dict[str, Any]) -> None:
        """Post an event to the configured Zapier webhook.

        Args:
            event_name: Short machine-readable event identifier, e.g.
                ``"invoice_processed"`` or ``"invoice_failed"``.
            payload: JSON-serializable event data.

        Raises:
            AutomationError: If the webhook URL is not configured, or the
                request fails.
        """
        if not self._settings.webhook_url:
            raise AutomationError("ZAPIER_WEBHOOK_URL is not configured")

        body = {"event": event_name, **payload}

        try:
            response = self._session.post(self._settings.webhook_url, json=body, timeout=15)
        except requests.RequestException as exc:
            raise AutomationError(f"Failed to reach Zapier webhook: {exc}") from exc

        if response.status_code >= 400:
            raise AutomationError(
                f"Zapier webhook returned status {response.status_code}: {response.text}"
            )

        logger.info("Sent '%s' event to Zapier webhook", event_name)
