"""OCR client backed by the Parseur API.

Parseur (https://parseur.com) is a document parsing service that accepts a
document upload, applies a user-defined parsing template, and returns
structured JSON containing the fields of interest (invoice number, dates,
amounts, tax identifiers, etc). This client wraps the upload + polling
sequence needed to retrieve that structured output.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import requests

from invoice_automation.config import ParseurSettings
from invoice_automation.exceptions import OCRError
from invoice_automation.ocr.base import OCRClient, OCRResult

logger = logging.getLogger(__name__)

DEFAULT_POLL_INTERVAL_SECONDS = 2
DEFAULT_MAX_POLL_ATTEMPTS = 15


class ParseurClient(OCRClient):
    """Uploads documents to Parseur and retrieves the parsed invoice fields."""

    def __init__(
        self,
        settings: ParseurSettings,
        poll_interval_seconds: int = DEFAULT_POLL_INTERVAL_SECONDS,
        max_poll_attempts: int = DEFAULT_MAX_POLL_ATTEMPTS,
        session: requests.Session | None = None,
    ) -> None:
        self._settings = settings
        self._poll_interval_seconds = poll_interval_seconds
        self._max_poll_attempts = max_poll_attempts
        self._session = session or requests.Session()

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Token {self._settings.api_key}"}

    def _upload_document(self, content: bytes, filename: str) -> str:
        """Upload a document to the configured Parseur mailbox and return its document id."""
        url = f"{self._settings.base_url}/mailboxes/{self._settings.mailbox_id}/upload"
        response = self._session.post(
            url,
            headers=self._headers(),
            files={"file": (filename, content)},
            timeout=30,
        )
        if response.status_code >= 400:
            raise OCRError(
                f"Parseur upload failed with status {response.status_code}: {response.text}"
            )
        payload = response.json()
        document_id = payload.get("id")
        if not document_id:
            raise OCRError("Parseur upload response did not contain a document id")
        return str(document_id)

    def _poll_for_parsed_result(self, document_id: str) -> dict[str, Any]:
        """Poll Parseur until the document has been parsed or a timeout is reached."""
        url = f"{self._settings.base_url}/documents/{document_id}"

        for attempt in range(1, self._max_poll_attempts + 1):
            response = self._session.get(url, headers=self._headers(), timeout=30)
            if response.status_code >= 400:
                raise OCRError(
                    f"Parseur polling failed with status {response.status_code}: {response.text}"
                )

            payload = response.json()
            status = payload.get("status")
            if status == "processed":
                return payload
            if status == "failed":
                raise OCRError(f"Parseur failed to process document {document_id}")

            logger.debug(
                "Parseur document %s not ready yet (attempt %d/%d)",
                document_id,
                attempt,
                self._max_poll_attempts,
            )
            time.sleep(self._poll_interval_seconds)

        raise OCRError(f"Timed out waiting for Parseur to process document {document_id}")

    def extract(self, content: bytes, filename: str) -> OCRResult:
        """Upload a document to Parseur and return its structured fields."""
        document_id = self._upload_document(content, filename)
        payload = self._poll_for_parsed_result(document_id)

        parsed_fields: dict[str, Any] = payload.get("parsed", {})
        raw_text: str = payload.get("text", "")

        return OCRResult(raw_text=raw_text, fields=parsed_fields, provider="parseur")
