"""Tests for OCR client implementations."""

from unittest.mock import MagicMock

import pytest
import requests

from invoice_automation.config import ParseurSettings
from invoice_automation.exceptions import OCRError
from invoice_automation.ocr.parseur_client import ParseurClient


def _make_response(status_code: int, json_body: dict) -> MagicMock:
    response = MagicMock(spec=requests.Response)
    response.status_code = status_code
    response.json.return_value = json_body
    response.text = str(json_body)
    return response


def test_parseur_client_extracts_fields_on_success() -> None:
    session = MagicMock(spec=requests.Session)
    session.post.return_value = _make_response(200, {"id": "doc-123"})
    session.get.return_value = _make_response(
        200,
        {
            "status": "processed",
            "text": "raw ocr text",
            "parsed": {"invoice_number": "INV-1", "total_amount": "100.00"},
        },
    )

    client = ParseurClient(
        ParseurSettings(api_key="key", mailbox_id="mailbox-1"),
        poll_interval_seconds=0,
        session=session,
    )

    result = client.extract(b"%PDF-1.4 ...", "invoice.pdf")

    assert result.provider == "parseur"
    assert result.raw_text == "raw ocr text"
    assert result.fields["invoice_number"] == "INV-1"
    session.post.assert_called_once()
    session.get.assert_called_once()


def test_parseur_client_raises_on_upload_failure() -> None:
    session = MagicMock(spec=requests.Session)
    session.post.return_value = _make_response(500, {"error": "server error"})

    client = ParseurClient(ParseurSettings(api_key="key", mailbox_id="mailbox-1"), session=session)

    with pytest.raises(OCRError):
        client.extract(b"content", "invoice.pdf")


def test_parseur_client_raises_when_processing_fails() -> None:
    session = MagicMock(spec=requests.Session)
    session.post.return_value = _make_response(200, {"id": "doc-123"})
    session.get.return_value = _make_response(200, {"status": "failed"})

    client = ParseurClient(
        ParseurSettings(api_key="key", mailbox_id="mailbox-1"),
        poll_interval_seconds=0,
        session=session,
    )

    with pytest.raises(OCRError):
        client.extract(b"content", "invoice.pdf")


def test_parseur_client_times_out_after_max_attempts() -> None:
    session = MagicMock(spec=requests.Session)
    session.post.return_value = _make_response(200, {"id": "doc-123"})
    session.get.return_value = _make_response(200, {"status": "processing"})

    client = ParseurClient(
        ParseurSettings(api_key="key", mailbox_id="mailbox-1"),
        poll_interval_seconds=0,
        max_poll_attempts=2,
        session=session,
    )

    with pytest.raises(OCRError):
        client.extract(b"content", "invoice.pdf")
    assert session.get.call_count == 2
