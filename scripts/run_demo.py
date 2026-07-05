#!/usr/bin/env python
"""Runnable, self-contained demo of the full capture-to-ERP pipeline.

This script does not require any external credentials (no real IMAP
mailbox, Parseur account, or Zapier webhook). It uses:

* An in-memory stub document source (simulating a scanned invoice).
* A stub OCR client seeded with the sample data from
  ``examples/sample_parseur_output.json`` (simulating a real Parseur
  response, without requiring a Parseur API key).
* A local SQLite database file (``demo.db``) as the "SADE ERP" target.

Run it with:
    python scripts/run_demo.py
"""

from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from pathlib import Path

from invoice_automation.automation.workflow_orchestrator import WorkflowOrchestrator
from invoice_automation.config import ERPSettings
from invoice_automation.erp.repository import InvoiceRepository
from invoice_automation.erp.sade_connector import SadeERPConnector
from invoice_automation.extraction.schemas import InvoiceType
from invoice_automation.ingestion.base import DocumentSource, RawDocument
from invoice_automation.ocr.base import OCRClient, OCRResult
from invoice_automation.pipeline import InvoiceAutomationPipeline

logging.basicConfig(level=logging.INFO, format="%(levelname)-8s | %(message)s")

REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_PATH = REPO_ROOT / "examples" / "sample_parseur_output.json"


class DemoDocumentSource(DocumentSource):
    """Yields a single fake scanned invoice, simulating a tablet/scanner drop."""

    def fetch_new_documents(self) -> Iterator[RawDocument]:
        yield RawDocument(
            source_id="demo-1",
            filename="invoice_1001.pdf",
            content=b"%PDF-1.4 (demo placeholder bytes)",
            origin="scanner",
        )


class DemoOCRClient(OCRClient):
    """Returns pre-recorded Parseur-style output instead of calling a real API."""

    def __init__(self, sample_path: Path) -> None:
        payload = json.loads(sample_path.read_text(encoding="utf-8"))
        self._result = OCRResult(
            raw_text=payload["text"], fields=payload["parsed"], provider="parseur-demo"
        )

    def extract(self, content: bytes, filename: str) -> OCRResult:
        return self._result


def main() -> None:
    demo_db_path = REPO_ROOT / "demo.db"
    connector = SadeERPConnector(ERPSettings(database_url=f"sqlite:///{demo_db_path}"))
    try:
        connector.initialize_schema()

        pipeline = InvoiceAutomationPipeline(
            sources=[DemoDocumentSource()],
            ocr_client=DemoOCRClient(SAMPLE_PATH),
            repository=InvoiceRepository(connector),
            orchestrator=WorkflowOrchestrator(zapier_client=None),
            default_invoice_type=InvoiceType.ACCOUNTS_PAYABLE,
        )

        result = pipeline.run()

        print()
        print(f"Processed: {result.success_count} | Failed: {result.failure_count}")
        for invoice in result.processed:
            print(
                f"  -> {invoice.invoice_number} | NCF={invoice.ncf} | "
                f"{invoice.counterparty_name} | {invoice.currency} {invoice.total_amount}"
            )
        print(f"\nSQLite ERP database written to: {demo_db_path}")
    finally:
        connector.dispose()


if __name__ == "__main__":
    main()
