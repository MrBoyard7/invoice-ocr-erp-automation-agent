"""Tests for the Zapier automation client and workflow orchestrator."""

from unittest.mock import MagicMock

import pytest
import requests

from invoice_automation.automation.workflow_orchestrator import WorkflowOrchestrator
from invoice_automation.automation.zapier_client import ZapierClient
from invoice_automation.config import ZapierSettings
from invoice_automation.exceptions import AutomationError
from invoice_automation.extraction.schemas import InvoiceData


def test_zapier_client_raises_when_webhook_not_configured() -> None:
    client = ZapierClient(ZapierSettings(webhook_url=""))
    with pytest.raises(AutomationError):
        client.send_event("invoice_processed", {"invoice_number": "INV-1"})


def test_zapier_client_sends_expected_payload() -> None:
    session = MagicMock(spec=requests.Session)
    session.post.return_value = MagicMock(status_code=200)

    client = ZapierClient(
        ZapierSettings(webhook_url="https://hooks.zapier.com/hooks/catch/x/y/"), session=session
    )
    client.send_event("invoice_processed", {"invoice_number": "INV-1"})

    session.post.assert_called_once()
    _, kwargs = session.post.call_args
    assert kwargs["json"]["event"] == "invoice_processed"
    assert kwargs["json"]["invoice_number"] == "INV-1"


def test_zapier_client_raises_on_error_status() -> None:
    session = MagicMock(spec=requests.Session)
    session.post.return_value = MagicMock(status_code=500, text="server error")

    client = ZapierClient(
        ZapierSettings(webhook_url="https://hooks.zapier.com/hooks/catch/x/y/"), session=session
    )
    with pytest.raises(AutomationError):
        client.send_event("invoice_processed", {})


def test_orchestrator_swallows_automation_errors(sample_invoice: InvoiceData) -> None:
    zapier_client = MagicMock(spec=ZapierClient)
    zapier_client.send_event.side_effect = AutomationError("boom")

    orchestrator = WorkflowOrchestrator(zapier_client=zapier_client)
    # Should not raise, even though the underlying client fails.
    orchestrator.notify_invoice_processed(sample_invoice)


def test_orchestrator_no_op_without_client(sample_invoice: InvoiceData) -> None:
    orchestrator = WorkflowOrchestrator(zapier_client=None)
    orchestrator.notify_invoice_processed(sample_invoice)
    orchestrator.notify_invoice_failed("file.pdf", "reason")
