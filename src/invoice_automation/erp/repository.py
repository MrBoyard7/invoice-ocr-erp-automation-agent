"""Repository layer translating ``InvoiceData`` into ERP SQL transactions."""

from __future__ import annotations

import logging

from sqlalchemy.exc import IntegrityError

from invoice_automation.erp.models import AccountsPayableEntry, AccountsReceivableEntry
from invoice_automation.erp.sade_connector import SadeERPConnector
from invoice_automation.exceptions import ERPIntegrationError
from invoice_automation.extraction.schemas import InvoiceData, InvoiceType

logger = logging.getLogger(__name__)


class InvoiceRepository:
    """Persists normalized invoices as AR/AP entries in the ERP database."""

    def __init__(self, connector: SadeERPConnector) -> None:
        self._connector = connector

    def save(self, invoice: InvoiceData) -> None:
        """Persist an invoice as either an Accounts Receivable or Payable entry.

        Raises:
            ERPIntegrationError: If the record cannot be committed, e.g.
                because the invoice number has already been posted.
        """
        if invoice.invoice_type == InvoiceType.ACCOUNTS_RECEIVABLE:
            entry = AccountsReceivableEntry(
                invoice_number=invoice.invoice_number,
                ncf=invoice.ncf,
                customer_name=invoice.counterparty_name,
                customer_rnc=invoice.counterparty_rnc,
                issue_date=invoice.issue_date,
                due_date=invoice.due_date,
                currency=invoice.currency,
                subtotal=invoice.subtotal,
                tax_amount=invoice.tax_amount,
                total_amount=invoice.total_amount,
                source_filename=invoice.source_filename,
            )
        else:
            entry = AccountsPayableEntry(
                invoice_number=invoice.invoice_number,
                ncf=invoice.ncf,
                vendor_name=invoice.counterparty_name,
                vendor_rnc=invoice.counterparty_rnc,
                issue_date=invoice.issue_date,
                due_date=invoice.due_date,
                currency=invoice.currency,
                subtotal=invoice.subtotal,
                tax_amount=invoice.tax_amount,
                total_amount=invoice.total_amount,
                source_filename=invoice.source_filename,
            )

        session = self._connector.session()
        try:
            with session.begin():
                session.add(entry)
            logger.info(
                "Posted %s entry for invoice %s to the ERP database",
                invoice.invoice_type.value,
                invoice.invoice_number,
            )
        except IntegrityError as exc:
            raise ERPIntegrationError(
                f"Invoice '{invoice.invoice_number}' has already been posted to the ERP"
            ) from exc
        finally:
            session.close()

    def count_receivables(self) -> int:
        """Return the number of Accounts Receivable entries currently stored."""
        session = self._connector.session()
        try:
            return session.query(AccountsReceivableEntry).count()
        finally:
            session.close()

    def count_payables(self) -> int:
        """Return the number of Accounts Payable entries currently stored."""
        session = self._connector.session()
        try:
            return session.query(AccountsPayableEntry).count()
        finally:
            session.close()
