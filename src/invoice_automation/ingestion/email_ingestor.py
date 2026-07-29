"""Email-based document ingestion adapter.

Invoices are frequently sent to a dedicated mailbox as PDF or image
attachments. This adapter connects to that mailbox over IMAP, scans for
unread messages, and yields each attachment as a ``RawDocument`` for
downstream OCR processing.
"""

from __future__ import annotations

import email
import imaplib
import logging
from collections.abc import Iterator
from email.message import Message

from invoice_automation.config import EmailSettings
from invoice_automation.exceptions import IngestionError
from invoice_automation.ingestion.base import DocumentSource, RawDocument

logger = logging.getLogger(__name__)

# Only these attachment types are considered valid invoice documents.
SUPPORTED_EXTENSIONS = (".pdf", ".png", ".jpg", ".jpeg", ".tiff")


class EmailIngestor(DocumentSource):
    """Fetches invoice attachments from an IMAP mailbox."""

    def __init__(self, settings: EmailSettings) -> None:
        self._settings = settings

    def _connect(self) -> imaplib.IMAP4:
        """Open and authenticate an IMAP connection."""
        try:
            if self._settings.use_ssl:
                connection: imaplib.IMAP4 = imaplib.IMAP4_SSL(
                    self._settings.host, self._settings.port
                )
            else:
                connection = imaplib.IMAP4(self._settings.host, self._settings.port)
            connection.login(self._settings.username, self._settings.password)
            connection.select(self._settings.mailbox)
            return connection
        except (imaplib.IMAP4.error, OSError) as exc:
            raise IngestionError(f"Unable to connect to IMAP mailbox: {exc}") from exc

    @staticmethod
    def _extract_attachments(message: Message) -> list[RawDocument]:
        """Extract supported attachments from a parsed email message."""
        documents: list[RawDocument] = []
        message_id = message.get("Message-ID", "unknown")

        for part in message.walk():
            filename = part.get_filename()
            if not filename:
                continue
            if not filename.lower().endswith(SUPPORTED_EXTENSIONS):
                logger.debug("Skipping unsupported attachment: %s", filename)
                continue

            payload = part.get_payload(decode=True)
            if not payload:
                continue

            documents.append(
                RawDocument(
                    source_id=f"{message_id}:{filename}",
                    filename=filename,
                    content=payload,
                    origin="email",
                )
            )
        return documents

    def fetch_new_documents(self) -> Iterator[RawDocument]:
        """Fetch unread emails and yield their invoice attachments.

        Successfully processed messages are flagged as ``\\Seen`` so they are
        not picked up again on the next polling cycle.
        """
        connection = self._connect()
        try:
            status, data = connection.search(None, "UNSEEN")
            if status != "OK":
                raise IngestionError(f"IMAP search failed with status: {status}")

            message_numbers = data[0].split()
            logger.info("Found %d unread message(s) in mailbox", len(message_numbers))

            for number in message_numbers:
                status, msg_data = connection.fetch(number, "(RFC822)")
                if status != "OK" or not msg_data or not msg_data[0]:
                    logger.warning("Could not fetch message %s, skipping", number)
                    continue

                raw_email = msg_data[0][1]
                message = email.message_from_bytes(raw_email)

                yield from self._extract_attachments(message)

                # Mark as read only after attachments have been yielded.
                connection.store(number, "+FLAGS", "\\Seen")
        finally:
            try:
                connection.close()
            except imaplib.IMAP4.error:
                logger.debug("IMAP connection was already closed")
            connection.logout()
