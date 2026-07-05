"""Pydantic data models representing a normalized invoice record."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class InvoiceType(str, Enum):
    """Whether an invoice represents money owed to us or by us."""

    ACCOUNTS_RECEIVABLE = "accounts_receivable"
    ACCOUNTS_PAYABLE = "accounts_payable"


class LineItem(BaseModel):
    """A single line item within an invoice."""

    description: str
    quantity: Decimal = Field(default=Decimal("1"))
    unit_price: Decimal = Field(default=Decimal("0"))
    line_total: Decimal = Field(default=Decimal("0"))


class InvoiceData(BaseModel):
    """Normalized, ERP-ready representation of a captured invoice.

    This is the common contract between the ``extraction`` stage (which
    produces it from raw OCR output) and the ``erp`` stage (which persists
    it as an Accounts Receivable or Accounts Payable transaction).
    """

    invoice_number: str
    ncf: Optional[str] = Field(
        default=None,
        description="Dominican Republic fiscal receipt number (Número de "
        "Comprobante Fiscal), when present on the document.",
    )
    invoice_type: InvoiceType
    issuer_rnc: Optional[str] = Field(
        default=None, description="Tax ID (RNC) of the invoice issuer."
    )
    counterparty_rnc: Optional[str] = Field(
        default=None, description="Tax ID (RNC) of the counterparty (customer or vendor)."
    )
    counterparty_name: str
    issue_date: date
    due_date: Optional[date] = None
    currency: str = Field(default="DOP")
    subtotal: Decimal = Field(default=Decimal("0"))
    tax_amount: Decimal = Field(default=Decimal("0"), description="ITBIS or equivalent tax.")
    total_amount: Decimal = Field(default=Decimal("0"))
    line_items: list[LineItem] = Field(default_factory=list)
    source_filename: Optional[str] = None
    ocr_provider: Optional[str] = None

    @field_validator("currency")
    @classmethod
    def _uppercase_currency(cls, value: str) -> str:
        return value.upper()

    @field_validator("total_amount")
    @classmethod
    def _total_must_be_non_negative(cls, value: Decimal) -> Decimal:
        if value < 0:
            raise ValueError("total_amount must not be negative")
        return value
