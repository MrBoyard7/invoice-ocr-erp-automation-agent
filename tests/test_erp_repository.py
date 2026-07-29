"""Tests for the ERP repository layer."""

import pytest

from invoice_automation.erp.repository import InvoiceRepository
from invoice_automation.exceptions import ERPIntegrationError
from invoice_automation.extraction.schemas import InvoiceData, InvoiceType


def test_save_persists_accounts_payable_entry(
    invoice_repository: InvoiceRepository, sample_invoice: InvoiceData
) -> None:
    invoice_repository.save(sample_invoice)
    assert invoice_repository.count_payables() == 1
    assert invoice_repository.count_receivables() == 0


def test_save_persists_accounts_receivable_entry(
    invoice_repository: InvoiceRepository, sample_invoice: InvoiceData
) -> None:
    receivable = sample_invoice.model_copy(
        update={"invoice_type": InvoiceType.ACCOUNTS_RECEIVABLE, "invoice_number": "INV-2001"}
    )
    invoice_repository.save(receivable)
    assert invoice_repository.count_receivables() == 1
    assert invoice_repository.count_payables() == 0


def test_save_rejects_duplicate_invoice_numbers(
    invoice_repository: InvoiceRepository, sample_invoice: InvoiceData
) -> None:
    invoice_repository.save(sample_invoice)
    with pytest.raises(ERPIntegrationError):
        invoice_repository.save(sample_invoice)
