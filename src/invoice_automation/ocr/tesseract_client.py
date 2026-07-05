"""Local OCR client backed by Tesseract, used as a low-cost fallback.

This client does not require any external API and is well suited to local
development, unit testing, or deployments where a paid OCR subscription is
not justified. Because Tesseract only returns raw text (no structured
fields), all field extraction is deferred to the ``extraction`` package.

The ``pytesseract`` and ``Pillow`` dependencies are optional (see the
``ocr-local`` extra in ``pyproject.toml``) and are imported lazily so the
rest of the package can be used without installing them.
"""

from __future__ import annotations

import io
import logging

from invoice_automation.exceptions import OCRError
from invoice_automation.ocr.base import OCRClient, OCRResult

logger = logging.getLogger(__name__)


class TesseractClient(OCRClient):
    """Extracts raw text from an image using the local Tesseract engine."""

    def __init__(self, language: str = "eng") -> None:
        self._language = language

    def extract(self, content: bytes, filename: str) -> OCRResult:
        """Run local OCR on an image and return its raw text.

        Note:
            PDF documents are not rasterized by this simple client; convert
            PDFs to images upstream (e.g. with ``pdf2image``) before calling
            this method, or use ``ParseurClient`` for native PDF support.
        """
        try:
            import pytesseract
            from PIL import Image
        except ImportError as exc:
            raise OCRError(
                "pytesseract and Pillow are required for local OCR. "
                'Install them with: pip install "invoice-ocr-erp-automation-agent[ocr-local]"'
            ) from exc

        try:
            image = Image.open(io.BytesIO(content))
            raw_text = pytesseract.image_to_string(image, lang=self._language)
        except Exception as exc:  # noqa: BLE001 - surface any Tesseract failure uniformly
            raise OCRError(f"Local OCR failed for '{filename}': {exc}") from exc

        return OCRResult(raw_text=raw_text, fields={}, provider="tesseract")
