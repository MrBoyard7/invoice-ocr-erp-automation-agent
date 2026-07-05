"""Custom exception hierarchy used across the invoice automation pipeline."""


class InvoiceAutomationError(Exception):
    """Base class for all errors raised by this package."""


class IngestionError(InvoiceAutomationError):
    """Raised when a document cannot be retrieved from an ingestion source."""


class OCRError(InvoiceAutomationError):
    """Raised when an OCR provider fails to process a document."""


class ExtractionError(InvoiceAutomationError):
    """Raised when OCR output cannot be normalized into a valid invoice record."""


class NCFValidationError(ExtractionError):
    """Raised when a fiscal receipt number (NCF) does not match a known format."""


class AutomationError(InvoiceAutomationError):
    """Raised when a downstream automation trigger (e.g. Zapier) fails."""


class ERPIntegrationError(InvoiceAutomationError):
    """Raised when a record cannot be persisted to the ERP database."""
