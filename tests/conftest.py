"""Shared pytest fixtures for the test suite."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import date

import pytest

from invoice_automation.config import ERPSettings, ZapierSettings
from invoice_automation.erp.repository import InvoiceRepository
from invoice_automation.erp.sade_connector import SadeERPConnector
from invoice_automation.extraction.schemas import InvoiceData, InvoiceType
from invoice_automation.ocr.base import OCRResult


@pytest.fixture()
def erp_connector() -> Iterator[SadeERPConnector]:
    """An in-memory SQLite ERP connector, isolated per test."""
    connector = SadeERPConnector(ERPSettings(database_url="sqlite:///:memory:"))
    connector.initialize_schema()
    yield connector
    connector.dispose()


@pytest.fixture()
def invoice_repository(erp_connector: SadeERPConnector) -> InvoiceRepository:
    return InvoiceRepository(erp_connector)


@pytest.fixture()
def sample_ocr_result() -> OCRResult:
    return OCRResult(
        raw_text="INVOICE #INV-1001 ...",
        fields={
            "invoice_number": "INV-1001",
            "ncf": "B0100000001",
            "counterparty_name": "Ferreteria Popular SRL",
            "issuer_rnc": "101223344",
            "counterparty_rnc": "130987654",
            "issue_date": "2026-06-15",
            "due_date": "2026-07-15",
            "currency": "DOP",
            "subtotal": "10000.00",
            "tax_amount": "1800.00",
            "total_amount": "11800.00",
        },
        provider="parseur",
    )


@pytest.fixture()
def sample_invoice() -> InvoiceData:
    return InvoiceData(
        invoice_number="INV-1001",
        ncf="B0100000001",
        invoice_type=InvoiceType.ACCOUNTS_PAYABLE,
        issuer_rnc="101223344",
        counterparty_rnc="130987654",
        counterparty_name="Ferreteria Popular SRL",
        issue_date=date(2026, 6, 15),
        due_date=date(2026, 7, 15),
        currency="DOP",
        subtotal=10000,
        tax_amount=1800,
        total_amount=11800,
        source_filename="invoice_1001.pdf",
        ocr_provider="parseur",
    )


@pytest.fixture()
def disabled_zapier_settings() -> ZapierSettings:
    return ZapierSettings(webhook_url="")
