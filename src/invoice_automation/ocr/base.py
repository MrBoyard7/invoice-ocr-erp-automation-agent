"""Common interfaces for OCR provider clients."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class OCRResult:
    """Normalized output of an OCR provider, prior to invoice extraction.

    Attributes:
        raw_text: Best-effort plain-text representation of the document.
        fields: Structured key/value pairs already identified by the OCR
            provider (Parseur returns these natively via its parsing
            templates; a local OCR engine may leave this empty).
        provider: Name of the OCR provider that produced this result.
    """

    raw_text: str
    fields: dict[str, Any] = field(default_factory=dict)
    provider: str = "unknown"


class OCRClient(ABC):
    """Base class for any OCR provider integration."""

    @abstractmethod
    def extract(self, content: bytes, filename: str) -> OCRResult:
        """Run OCR extraction on a document and return normalized output."""
        raise NotImplementedError
