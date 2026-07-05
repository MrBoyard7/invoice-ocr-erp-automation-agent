"""Tests for the Dominican Republic NCF/e-CF validator."""

import pytest

from invoice_automation.exceptions import NCFValidationError
from invoice_automation.extraction.ncf_validator import (
    get_document_type_code,
    is_valid_ncf,
    validate_ncf,
)


@pytest.mark.parametrize(
    "value",
    [
        "B0100000001",  # legacy NCF, type 01
        "A0200000123",  # legacy NCF, type 02
        "E310000000001",  # electronic invoice (e-CF)
    ],
)
def test_is_valid_ncf_accepts_known_formats(value: str) -> None:
    assert is_valid_ncf(value) is True


@pytest.mark.parametrize(
    "value",
    [
        "",
        "12345",
        "Z0100000001",  # invalid leading letter
        "B01000001",  # too short
        "B010000000012",  # too long
    ],
)
def test_is_valid_ncf_rejects_invalid_formats(value: str) -> None:
    assert is_valid_ncf(value) is False


def test_validate_ncf_normalizes_case_and_whitespace() -> None:
    assert validate_ncf(" b0100000001 ") == "B0100000001"


def test_validate_ncf_raises_on_invalid_value() -> None:
    with pytest.raises(NCFValidationError):
        validate_ncf("not-an-ncf")


def test_get_document_type_code_extracts_correct_segment() -> None:
    assert get_document_type_code("B0100000001") == "01"
    assert get_document_type_code("E310000000001") == "31"


def test_get_document_type_code_raises_on_invalid_value() -> None:
    with pytest.raises(NCFValidationError):
        get_document_type_code("invalid")
