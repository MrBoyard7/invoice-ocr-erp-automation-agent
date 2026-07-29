"""End-to-end pipeline wiring ingestion, OCR, extraction, automation, and ERP posting."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from invoice_automation.automation.workflow_orchestrator import WorkflowOrchestrator
from invoice_automation.erp.repository import InvoiceRepository
from invoice_automation.exceptions import InvoiceAutomationError
from invoice_automation.extraction.invoice_parser import parse_invoice
from invoice_automation.extraction.schemas import InvoiceData, InvoiceType
from invoice_automation.ingestion.base import DocumentSource
from invoice_automation.ocr.base import OCRClient

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Summary of a single pipeline run."""

    processed: list[InvoiceData]
    failed: list[str]

    @property
    def success_count(self) -> int:
        return len(self.processed)

    @property
    def failure_count(self) -> int:
        return len(self.failed)


class InvoiceAutomationPipeline:
    """Coordinates the full capture-to-ERP workflow for one or more document sources."""

    def __init__(
        self,
        sources: list[DocumentSource],
        ocr_client: OCRClient,
        repository: InvoiceRepository,
        orchestrator: WorkflowOrchestrator,
        default_invoice_type: InvoiceType = InvoiceType.ACCOUNTS_PAYABLE,
    ) -> None:
        self._sources = sources
        self._ocr_client = ocr_client
        self._repository = repository
        self._orchestrator = orchestrator
        self._default_invoice_type = default_invoice_type

    def run(self) -> PipelineResult:
        """Pull new documents from every configured source and process each one.

        Returns:
            A ``PipelineResult`` summarizing successes and failures. A single
            document failure does not stop the run; it is recorded and the
            pipeline continues with the next document.
        """
        processed: list[InvoiceData] = []
        failed: list[str] = []

        for source in self._sources:
            for document in source.fetch_new_documents():
                try:
                    ocr_result = self._ocr_client.extract(document.content, document.filename)
                    invoice = parse_invoice(
                        ocr_result,
                        invoice_type=self._default_invoice_type,
                        source_filename=document.filename,
                    )
                    self._repository.save(invoice)
                    self._orchestrator.notify_invoice_processed(invoice)
                    processed.append(invoice)
                except InvoiceAutomationError as exc:
                    logger.error("Failed to process '%s': %s", document.filename, exc)
                    self._orchestrator.notify_invoice_failed(document.filename, str(exc))
                    failed.append(document.filename)

        logger.info("Pipeline run complete: %d processed, %d failed", len(processed), len(failed))
        return PipelineResult(processed=processed, failed=failed)
