"""Normalize raw OCR output into a validated ``InvoiceData`` record."""

from __future__ import annotations

import logging
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Optional

from invoice_automation.exceptions import ExtractionError
from invoice_automation.extraction.ncf_validator import validate_ncf
from invoice_automation.extraction.schemas import InvoiceData, InvoiceType
from invoice_automation.ocr.base import OCRResult

logger = logging.getLogger(__name__)

_DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y")


def _parse_date(raw_value: Optional[str]) -> Optional[date]:
    if not raw_value:
        return None
    for date_format in _DATE_FORMATS:
        try:
            return datetime.strptime(raw_value.strip(), date_format).date()
        except ValueError:
            continue
    logger.warning("Could not parse date value '%s' with known formats", raw_value)
    return None


def _parse_decimal(raw_value: Any) -> Decimal:
    if raw_value in (None, ""):
        return Decimal("0")
    try:
        # Normalize common thousands separators before parsing.
        cleaned = str(raw_value).replace(",", "")
        return Decimal(cleaned)
    except InvalidOperation as exc:
        raise ExtractionError(f"Could not parse numeric value: '{raw_value}'") from exc


def parse_invoice(
    ocr_result: OCRResult,
    invoice_type: InvoiceType,
    source_filename: Optional[str] = None,
) -> InvoiceData:
    """Convert OCR output into a normalized, validated ``InvoiceData`` record.

    Args:
        ocr_result: Structured (or partially structured) OCR output.
        invoice_type: Whether this document is an AR or AP transaction.
        source_filename: Original filename, kept for audit/traceability.

    Raises:
        ExtractionError: If required fields are missing or malformed.
    """
    fields: dict[str, Any] = ocr_result.fields or {}

    invoice_number = fields.get("invoice_number") or fields.get("invoice_id")
    if not invoice_number:
        raise ExtractionError("OCR output is missing a required 'invoice_number' field")

    counterparty_name = (
        fields.get("counterparty_name") or fields.get("vendor_name") or fields.get("customer_name")
    )
    if not counterparty_name:
        raise ExtractionError("OCR output is missing a required counterparty name field")

    issue_date = _parse_date(fields.get("issue_date"))
    if issue_date is None:
        raise ExtractionError("OCR output is missing a valid 'issue_date' field")

    raw_ncf = fields.get("ncf")
    ncf = validate_ncf(raw_ncf) if raw_ncf else None

    invoice = InvoiceData(
        invoice_number=str(invoice_number),
        ncf=ncf,
        invoice_type=invoice_type,
        issuer_rnc=fields.get("issuer_rnc"),
        counterparty_rnc=fields.get("counterparty_rnc"),
        counterparty_name=str(counterparty_name),
        issue_date=issue_date,
        due_date=_parse_date(fields.get("due_date")),
        currency=fields.get("currency", "DOP"),
        subtotal=_parse_decimal(fields.get("subtotal")),
        tax_amount=_parse_decimal(fields.get("tax_amount") or fields.get("itbis")),
        total_amount=_parse_decimal(fields.get("total_amount") or fields.get("total")),
        source_filename=source_filename,
        ocr_provider=ocr_result.provider,
    )

    logger.info(
        "Parsed invoice %s (%s) for counterparty '%s'",
        invoice.invoice_number,
        invoice.invoice_type.value,
        invoice.counterparty_name,
    )
    return invoice
