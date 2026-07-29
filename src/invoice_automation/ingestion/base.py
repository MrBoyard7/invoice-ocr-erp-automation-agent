"""Common interfaces for document ingestion adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass


@dataclass(frozen=True)
class RawDocument:
    """A single captured document, prior to any OCR processing.

    Attributes:
        source_id: Identifier of the document within its source system
            (e.g. an email message UID, or a file path).
        filename: Original filename, used to infer content type and for
            traceability in logs and ERP audit trails.
        content: Raw binary content of the document (PDF or image bytes).
        origin: Human-readable label for where the document came from,
            e.g. "email" or "scanner".
    """

    source_id: str
    filename: str
    content: bytes
    origin: str


class DocumentSource(ABC):
    """Base class for any adapter that can yield ``RawDocument`` instances."""

    @abstractmethod
    def fetch_new_documents(self) -> Iterator[RawDocument]:
        """Yield documents that have not yet been processed.

        Implementations are responsible for their own bookkeeping (e.g.
        marking emails as read, or moving processed files) so repeated
        calls do not return the same document twice.
        """
        raise NotImplementedError
