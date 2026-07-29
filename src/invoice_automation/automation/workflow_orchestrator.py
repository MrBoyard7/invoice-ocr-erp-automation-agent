"""Thin orchestration layer for downstream workflow notifications.

This module decouples the core pipeline from any specific automation
platform. Today it only talks to Zapier, but additional notifiers (e.g. a
Slack webhook, or a second automation platform) could be added here without
touching the pipeline itself.
"""

from __future__ import annotations

import logging
from typing import Optional

from invoice_automation.automation.zapier_client import ZapierClient
from invoice_automation.exceptions import AutomationError
from invoice_automation.extraction.schemas import InvoiceData

logger = logging.getLogger(__name__)


class WorkflowOrchestrator:
    """Notifies downstream automations about invoice processing outcomes."""

    def __init__(self, zapier_client: Optional[ZapierClient] = None) -> None:
        self._zapier_client = zapier_client

    def notify_invoice_processed(self, invoice: InvoiceData) -> None:
        """Notify downstream automations that an invoice was posted successfully."""
        if self._zapier_client is None:
            logger.debug("No Zapier client configured; skipping notification")
            return

        try:
            self._zapier_client.send_event(
                "invoice_processed",
                {
                    "invoice_number": invoice.invoice_number,
                    "ncf": invoice.ncf,
                    "invoice_type": invoice.invoice_type.value,
                    "counterparty_name": invoice.counterparty_name,
                    "total_amount": str(invoice.total_amount),
                    "currency": invoice.currency,
                },
            )
        except AutomationError as exc:
            # A notification failure should not roll back an already-posted
            # ERP transaction; it is logged so it can be retried or audited.
            logger.error("Failed to notify Zapier for invoice %s: %s", invoice.invoice_number, exc)

    def notify_invoice_failed(self, source_filename: str, reason: str) -> None:
        """Notify downstream automations that a document failed processing."""
        if self._zapier_client is None:
            logger.debug("No Zapier client configured; skipping failure notification")
            return

        try:
            self._zapier_client.send_event(
                "invoice_failed",
                {"source_filename": source_filename, "reason": reason},
            )
        except AutomationError as exc:
            logger.error("Failed to notify Zapier about failure for %s: %s", source_filename, exc)
