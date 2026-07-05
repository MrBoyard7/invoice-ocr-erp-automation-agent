"""Scanner / watched-folder document ingestion adapter.

Physical scanners and tablet scanning applications are typically configured
to drop captured invoice files (PDF or image) into a shared folder. This
adapter polls that folder, yields new files as ``RawDocument`` instances, and
moves them to a "processed" folder to prevent duplicate ingestion.
"""

from __future__ import annotations

import logging
import shutil
from collections.abc import Iterator
from pathlib import Path

from invoice_automation.config import ScannerSettings
from invoice_automation.exceptions import IngestionError
from invoice_automation.ingestion.base import DocumentSource, RawDocument

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = (".pdf", ".png", ".jpg", ".jpeg", ".tiff")


class ScannerIngestor(DocumentSource):
    """Watches a folder for newly scanned invoice files."""

    def __init__(self, settings: ScannerSettings) -> None:
        self._settings = settings
        self._watch_folder = Path(settings.watch_folder)
        self._processed_folder = Path(settings.processed_folder)
        self._ensure_folders_exist()

    def _ensure_folders_exist(self) -> None:
        try:
            self._watch_folder.mkdir(parents=True, exist_ok=True)
            self._processed_folder.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise IngestionError(f"Unable to prepare scanner folders: {exc}") from exc

    def fetch_new_documents(self) -> Iterator[RawDocument]:
        """Yield every supported file currently sitting in the watch folder.

        Each file is moved into the processed folder immediately after being
        read, so a subsequent call only picks up genuinely new scans.
        """
        candidate_files = sorted(
            path
            for path in self._watch_folder.iterdir()
            if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
        )
        logger.info("Found %d new scanned file(s)", len(candidate_files))

        for path in candidate_files:
            try:
                content = path.read_bytes()
            except OSError as exc:
                logger.error("Could not read scanned file %s: %s", path, exc)
                continue

            document = RawDocument(
                source_id=str(path),
                filename=path.name,
                content=content,
                origin="scanner",
            )

            destination = self._processed_folder / path.name
            shutil.move(str(path), str(destination))

            yield document
