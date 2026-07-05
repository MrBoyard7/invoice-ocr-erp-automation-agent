"""SQLAlchemy ORM models representing the ERP-side invoice tables.

These tables represent the minimal data matrix required for the SADE ERP
(or any comparable SQL-backed ERP) to ingest Accounts Receivable and
Accounts Payable transactions. Table names are deliberately generic and in
English so this schema can sit in front of the ERP's own native tables via a
staging/integration schema, or be adapted directly to the ERP's real schema.
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import DateTime, Numeric, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base shared by all ERP integration tables."""


class AccountsReceivableEntry(Base):
    """A single Accounts Receivable transaction (money owed to the firm)."""

    __tablename__ = "accounts_receivable"
    __table_args__ = (UniqueConstraint("invoice_number", name="uq_ar_invoice_number"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    invoice_number: Mapped[str] = mapped_column(String(64), nullable=False)
    ncf: Mapped[str | None] = mapped_column(String(32), nullable=True)
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_rnc: Mapped[str | None] = mapped_column(String(32), nullable=True)
    issue_date: Mapped[date] = mapped_column(nullable=False)
    due_date: Mapped[date | None] = mapped_column(nullable=True)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="DOP")
    subtotal: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False, default=0)
    tax_amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False, default=0)
    total_amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False, default=0)
    source_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AccountsPayableEntry(Base):
    """A single Accounts Payable transaction (money owed by the firm)."""

    __tablename__ = "accounts_payable"
    __table_args__ = (UniqueConstraint("invoice_number", name="uq_ap_invoice_number"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    invoice_number: Mapped[str] = mapped_column(String(64), nullable=False)
    ncf: Mapped[str | None] = mapped_column(String(32), nullable=True)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    vendor_rnc: Mapped[str | None] = mapped_column(String(32), nullable=True)
    issue_date: Mapped[date] = mapped_column(nullable=False)
    due_date: Mapped[date | None] = mapped_column(nullable=True)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="DOP")
    subtotal: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False, default=0)
    tax_amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False, default=0)
    total_amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False, default=0)
    source_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
