"""Integration-style tests for the end-to-end pipeline."""

from collections.abc import Iterator
from unittest.mock import MagicMock

from invoice_automation.automation.workflow_orchestrator import WorkflowOrchestrator
from invoice_automation.erp.repository import InvoiceRepository
from invoice_automation.exceptions import ExtractionError
from invoice_automation.extraction.schemas import InvoiceType
from invoice_automation.ingestion.base import DocumentSource, RawDocument
from invoice_automation.ocr.base import OCRClient, OCRResult
from invoice_automation.pipeline import InvoiceAutomationPipeline


class _StubSource(DocumentSource):
    def __init__(self, documents):
        self._documents = documents

    def fetch_new_documents(self) -> Iterator[RawDocument]:
        yield from self._documents


class _StubOCRClient(OCRClient):
    def __init__(self, results_by_filename):
        self._results_by_filename = results_by_filename

    def extract(self, content: bytes, filename: str) -> OCRResult:
        result = self._results_by_filename.get(filename)
        if result is None:
            raise ExtractionError(f"No stub OCR result configured for {filename}")
        return result


def test_pipeline_processes_valid_documents_end_to_end(
    invoice_repository: InvoiceRepository,
) -> None:
    document = RawDocument(
        source_id="1", filename="invoice_ok.pdf", content=b"fake", origin="scanner"
    )
    ocr_result = OCRResult(
        raw_text="",
        fields={
            "invoice_number": "INV-9001",
            "counterparty_name": "Suplidora Dominicana SRL",
            "issue_date": "2026-06-01",
            "total_amount": "5000.00",
        },
        provider="stub",
    )

    pipeline = InvoiceAutomationPipeline(
        sources=[_StubSource([document])],
        ocr_client=_StubOCRClient({"invoice_ok.pdf": ocr_result}),
        repository=invoice_repository,
        orchestrator=WorkflowOrchestrator(zapier_client=None),
        default_invoice_type=InvoiceType.ACCOUNTS_PAYABLE,
    )

    result = pipeline.run()

    assert result.success_count == 1
    assert result.failure_count == 0
    assert invoice_repository.count_payables() == 1


def test_pipeline_records_failures_without_stopping(
    invoice_repository: InvoiceRepository,
) -> None:
    good_document = RawDocument(
        source_id="1", filename="good.pdf", content=b"fake", origin="scanner"
    )
    bad_document = RawDocument(source_id="2", filename="bad.pdf", content=b"fake", origin="scanner")
    good_result = OCRResult(
        raw_text="",
        fields={
            "invoice_number": "INV-9002",
            "counterparty_name": "Ferreteria del Este SRL",
            "issue_date": "2026-06-02",
            "total_amount": "3200.00",
        },
        provider="stub",
    )

    orchestrator = MagicMock(spec=WorkflowOrchestrator)

    pipeline = InvoiceAutomationPipeline(
        sources=[_StubSource([good_document, bad_document])],
        ocr_client=_StubOCRClient({"good.pdf": good_result}),  # no result for bad.pdf
        repository=invoice_repository,
        orchestrator=orchestrator,
        default_invoice_type=InvoiceType.ACCOUNTS_PAYABLE,
    )

    result = pipeline.run()

    assert result.success_count == 1
    assert result.failure_count == 1
    assert "bad.pdf" in result.failed
    orchestrator.notify_invoice_failed.assert_called_once()
    orchestrator.notify_invoice_processed.assert_called_once()
