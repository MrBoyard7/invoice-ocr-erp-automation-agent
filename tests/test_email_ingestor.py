"""Tests for the IMAP-based email ingestion adapter."""

from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from unittest.mock import MagicMock, patch

import pytest

from invoice_automation.config import EmailSettings
from invoice_automation.exceptions import IngestionError
from invoice_automation.ingestion.email_ingestor import EmailIngestor


def _build_raw_email_with_attachment(filename: str, content: bytes) -> bytes:
    message = MIMEMultipart()
    message["Message-ID"] = "<test-message-1@example.com>"
    message["Subject"] = "Invoice"
    message.attach(MIMEText("Please find the attached invoice.", "plain"))

    attachment = MIMEApplication(content)
    attachment.add_header("Content-Disposition", "attachment", filename=filename)
    message.attach(attachment)

    return message.as_bytes()


@pytest.fixture()
def email_settings() -> EmailSettings:
    return EmailSettings(
        host="imap.example.com",
        port=993,
        username="invoices@example.com",
        password="secret",
        mailbox="INBOX",
        use_ssl=True,
    )


def test_fetch_new_documents_extracts_supported_attachment(email_settings: EmailSettings) -> None:
    raw_email = _build_raw_email_with_attachment("invoice_001.pdf", b"%PDF-1.4 fake content")

    mock_connection = MagicMock()
    mock_connection.search.return_value = ("OK", [b"1"])
    mock_connection.fetch.return_value = ("OK", [(None, raw_email)])

    with patch("imaplib.IMAP4_SSL", return_value=mock_connection):
        ingestor = EmailIngestor(email_settings)
        documents = list(ingestor.fetch_new_documents())

    assert len(documents) == 1
    assert documents[0].filename == "invoice_001.pdf"
    assert documents[0].origin == "email"
    assert documents[0].content == b"%PDF-1.4 fake content"
    mock_connection.store.assert_called_once_with(b"1", "+FLAGS", "\\Seen")
    mock_connection.logout.assert_called_once()


def test_fetch_new_documents_returns_empty_when_no_unread_messages(
    email_settings: EmailSettings,
) -> None:
    mock_connection = MagicMock()
    mock_connection.search.return_value = ("OK", [b""])

    with patch("imaplib.IMAP4_SSL", return_value=mock_connection):
        ingestor = EmailIngestor(email_settings)
        documents = list(ingestor.fetch_new_documents())

    assert documents == []


def test_fetch_new_documents_raises_when_search_fails(email_settings: EmailSettings) -> None:
    mock_connection = MagicMock()
    mock_connection.search.return_value = ("NO", [b""])

    with patch("imaplib.IMAP4_SSL", return_value=mock_connection):
        ingestor = EmailIngestor(email_settings)
        with pytest.raises(IngestionError):
            list(ingestor.fetch_new_documents())


def test_connect_raises_ingestion_error_on_login_failure(email_settings: EmailSettings) -> None:
    with patch("imaplib.IMAP4_SSL", side_effect=OSError("connection refused")):
        ingestor = EmailIngestor(email_settings)
        with pytest.raises(IngestionError):
            list(ingestor.fetch_new_documents())
