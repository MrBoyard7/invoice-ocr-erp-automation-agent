"""Tests for the local Tesseract OCR fallback client."""

import sys
import types
from unittest.mock import MagicMock

import pytest

from invoice_automation.exceptions import OCRError
from invoice_automation.ocr.tesseract_client import TesseractClient


def test_extract_raises_when_optional_dependencies_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(sys.modules, "pytesseract", None)

    client = TesseractClient()
    with pytest.raises(OCRError):
        client.extract(b"fake image bytes", "scan.png")


def test_extract_returns_ocr_result_when_dependencies_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_image = MagicMock()

    fake_pil_image_module = types.ModuleType("PIL.Image")
    fake_pil_image_module.open = MagicMock(return_value=fake_image)

    fake_pil_module = types.ModuleType("PIL")
    fake_pil_module.Image = fake_pil_image_module

    fake_pytesseract_module = types.ModuleType("pytesseract")
    fake_pytesseract_module.image_to_string = MagicMock(return_value="INVOICE TEXT")

    monkeypatch.setitem(sys.modules, "PIL", fake_pil_module)
    monkeypatch.setitem(sys.modules, "PIL.Image", fake_pil_image_module)
    monkeypatch.setitem(sys.modules, "pytesseract", fake_pytesseract_module)

    client = TesseractClient(language="eng")
    result = client.extract(b"fake image bytes", "scan.png")

    assert result.provider == "tesseract"
    assert result.raw_text == "INVOICE TEXT"
    fake_pytesseract_module.image_to_string.assert_called_once_with(fake_image, lang="eng")
