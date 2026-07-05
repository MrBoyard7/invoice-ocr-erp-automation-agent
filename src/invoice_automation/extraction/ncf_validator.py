"""Validation helpers for Dominican Republic fiscal receipt numbers (NCF).

The Dominican tax authority (DGII) defines two main NCF formats:

* Legacy NCF: 11 characters - a letter ("A" or "B"), a 2-digit document
  type code, and an 8-digit sequential number, e.g. ``B0100000001``.
* Electronic invoice (e-CF): 13 characters - the letter "E", a 2-digit
  document type code, and a 10-digit sequential number,
  e.g. ``E310000000001``.

This module implements a simplified, best-effort validator covering both
formats. It is intended for demonstration and pipeline "sanity checking"
purposes; a production deployment should validate against the authoritative
DGII technical specification (Norma General sobre Comprobantes Fiscales) and
ideally verify the receipt number against the DGII web services.
"""

from __future__ import annotations

import re

from invoice_automation.exceptions import NCFValidationError

_LEGACY_NCF_PATTERN = re.compile(r"^[AB]\d{2}\d{8}$")
_ECF_PATTERN = re.compile(r"^E\d{2}\d{10}$")

# Common legacy NCF document type codes (non-exhaustive, illustrative subset).
LEGACY_DOCUMENT_TYPES = {
    "01": "Credit and Debit Invoice",
    "02": "Final Consumer Invoice",
    "14": "Foreign Regime Invoice",
    "15": "Government Invoice",
}


def is_valid_ncf(value: str) -> bool:
    """Return ``True`` if ``value`` matches a known NCF or e-CF format."""
    if not value:
        return False
    candidate = value.strip().upper()
    return bool(_LEGACY_NCF_PATTERN.match(candidate) or _ECF_PATTERN.match(candidate))


def get_document_type_code(value: str) -> str:
    """Return the 2-digit document type code embedded in an NCF/e-CF value."""
    candidate = value.strip().upper()
    if _LEGACY_NCF_PATTERN.match(candidate) or _ECF_PATTERN.match(candidate):
        return candidate[1:3]
    raise NCFValidationError(f"'{value}' is not a recognized NCF or e-CF format")


def validate_ncf(value: str) -> str:
    """Validate an NCF value, raising ``NCFValidationError`` if it is invalid.

    Returns:
        The normalized (uppercased, trimmed) NCF value on success.
    """
    candidate = value.strip().upper() if value else ""
    if not is_valid_ncf(candidate):
        raise NCFValidationError(
            f"'{value}' does not match a known NCF (11 chars) or e-CF (13 chars) format"
        )
    return candidate
