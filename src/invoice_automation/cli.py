"""Command-line interface for the invoice automation agent."""

from __future__ import annotations

import logging

import click

from invoice_automation.automation.workflow_orchestrator import WorkflowOrchestrator
from invoice_automation.automation.zapier_client import ZapierClient
from invoice_automation.config import get_settings
from invoice_automation.erp.repository import InvoiceRepository
from invoice_automation.erp.sade_connector import SadeERPConnector
from invoice_automation.exceptions import NCFValidationError
from invoice_automation.extraction.ncf_validator import validate_ncf
from invoice_automation.extraction.schemas import InvoiceType
from invoice_automation.ingestion.scanner_ingestor import ScannerIngestor
from invoice_automation.ocr.tesseract_client import TesseractClient
from invoice_automation.pipeline import InvoiceAutomationPipeline


def _configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )


@click.group()
def main() -> None:
    """Invoice OCR + ERP automation agent."""


@main.command("validate-ncf")
@click.argument("value")
def validate_ncf_command(value: str) -> None:
    """Validate a Dominican Republic NCF / e-CF value."""
    try:
        normalized = validate_ncf(value)
        click.echo(f"'{normalized}' is a valid NCF/e-CF.")
    except NCFValidationError as exc:
        click.echo(f"Invalid NCF: {exc}", err=True)
        raise SystemExit(1) from exc


@main.command("run")
@click.option(
    "--invoice-type",
    type=click.Choice([t.value for t in InvoiceType]),
    default=InvoiceType.ACCOUNTS_PAYABLE.value,
    help="Invoice type to assign to newly captured documents.",
)
def run_command(invoice_type: str) -> None:
    """Run one pipeline pass over the configured scanner watch folder."""
    settings = get_settings()
    _configure_logging(settings.log_level)

    connector = SadeERPConnector(settings.erp)
    try:
        connector.initialize_schema()

        zapier_client = ZapierClient(settings.zapier) if settings.zapier.webhook_url else None
        orchestrator = WorkflowOrchestrator(zapier_client=zapier_client)

        pipeline = InvoiceAutomationPipeline(
            sources=[ScannerIngestor(settings.scanner)],
            ocr_client=TesseractClient(),
            repository=InvoiceRepository(connector),
            orchestrator=orchestrator,
            default_invoice_type=InvoiceType(invoice_type),
        )

        result = pipeline.run()
        click.echo(f"Processed: {result.success_count} | Failed: {result.failure_count}")
    finally:
        connector.dispose()


if __name__ == "__main__":
    main()
