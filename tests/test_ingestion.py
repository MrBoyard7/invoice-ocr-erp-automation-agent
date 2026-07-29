"""Tests for the scanner-based ingestion adapter."""

from pathlib import Path

from invoice_automation.config import ScannerSettings
from invoice_automation.ingestion.scanner_ingestor import ScannerIngestor


def test_scanner_ingestor_creates_folders_if_missing(tmp_path: Path) -> None:
    watch_folder = tmp_path / "incoming"
    processed_folder = tmp_path / "processed"

    ScannerIngestor(
        ScannerSettings(watch_folder=str(watch_folder), processed_folder=str(processed_folder))
    )

    assert watch_folder.exists()
    assert processed_folder.exists()


def test_scanner_ingestor_yields_and_moves_supported_files(tmp_path: Path) -> None:
    watch_folder = tmp_path / "incoming"
    processed_folder = tmp_path / "processed"
    watch_folder.mkdir()
    processed_folder.mkdir()

    invoice_file = watch_folder / "invoice_001.pdf"
    invoice_file.write_bytes(b"%PDF-1.4 fake content")

    ignored_file = watch_folder / "notes.txt"
    ignored_file.write_text("not an invoice")

    ingestor = ScannerIngestor(
        ScannerSettings(watch_folder=str(watch_folder), processed_folder=str(processed_folder))
    )

    documents = list(ingestor.fetch_new_documents())

    assert len(documents) == 1
    assert documents[0].filename == "invoice_001.pdf"
    assert documents[0].origin == "scanner"
    assert not (watch_folder / "invoice_001.pdf").exists()
    assert (processed_folder / "invoice_001.pdf").exists()
    # Unsupported files are left untouched.
    assert ignored_file.exists()


def test_scanner_ingestor_returns_empty_when_no_files(tmp_path: Path) -> None:
    ingestor = ScannerIngestor(
        ScannerSettings(
            watch_folder=str(tmp_path / "incoming"),
            processed_folder=str(tmp_path / "processed"),
        )
    )
    assert list(ingestor.fetch_new_documents()) == []
