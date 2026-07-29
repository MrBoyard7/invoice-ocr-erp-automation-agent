"""Tests for OCR-output-to-InvoiceData normalization."""

from datetime import date

import pytest

from invoice_automation.exceptions import ExtractionError
from invoice_automation.extraction.invoice_parser import parse_invoice
from invoice_automation.extraction.schemas import InvoiceType
from invoice_automation.ocr.base import OCRResult


def test_parse_invoice_builds_expected_record(sample_ocr_result: OCRResult) -> None:
    invoice = parse_invoice(
        sample_ocr_result,
        invoice_type=InvoiceType.ACCOUNTS_PAYABLE,
        source_filename="invoice_1001.pdf",
    )

    assert invoice.invoice_number == "INV-1001"
    assert invoice.ncf == "B0100000001"
    assert invoice.counterparty_name == "Ferreteria Popular SRL"
    assert invoice.issue_date == date(2026, 6, 15)
    assert invoice.due_date == date(2026, 7, 15)
    assert invoice.subtotal == 10000
    assert invoice.tax_amount == 1800
    assert invoice.total_amount == 11800
    assert invoice.ocr_provider == "parseur"


def test_parse_invoice_requires_invoice_number() -> None:
    ocr_result = OCRResult(
        raw_text="", fields={"counterparty_name": "Acme", "issue_date": "2026-01-01"}
    )
    with pytest.raises(ExtractionError):
        parse_invoice(ocr_result, invoice_type=InvoiceType.ACCOUNTS_PAYABLE)


def test_parse_invoice_requires_counterparty_name() -> None:
    ocr_result = OCRResult(
        raw_text="", fields={"invoice_number": "INV-1", "issue_date": "2026-01-01"}
    )
    with pytest.raises(ExtractionError):
        parse_invoice(ocr_result, invoice_type=InvoiceType.ACCOUNTS_PAYABLE)


def test_parse_invoice_requires_valid_issue_date() -> None:
    ocr_result = OCRResult(
        raw_text="",
        fields={"invoice_number": "INV-1", "counterparty_name": "Acme", "issue_date": "not-a-date"},
    )
    with pytest.raises(ExtractionError):
        parse_invoice(ocr_result, invoice_type=InvoiceType.ACCOUNTS_PAYABLE)


def test_parse_invoice_accepts_alternate_date_format() -> None:
    ocr_result = OCRResult(
        raw_text="",
        fields={
            "invoice_number": "INV-2",
            "counterparty_name": "Acme",
            "issue_date": "15/06/2026",
            "total_amount": "1,250.50",
        },
    )
    invoice = parse_invoice(ocr_result, invoice_type=InvoiceType.ACCOUNTS_RECEIVABLE)
    assert invoice.issue_date == date(2026, 6, 15)
    assert invoice.total_amount == pytest.approx(1250.50)
