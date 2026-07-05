"""Invoice OCR + ERP Automation Agent.

This package implements an end-to-end pipeline for capturing invoices
(Accounts Receivable and Accounts Payable), extracting their data via OCR,
validating the extracted data, and posting the resulting transactions into a
SQL-backed ERP system (referred to throughout this project as "SADE").

The pipeline is organized into five composable stages:

1. ``ingestion``   - Capture raw invoice documents from email or scanners.
2. ``ocr``         - Extract structured or raw text data from documents.
3. ``extraction``  - Normalize and validate OCR output into invoice records.
4. ``automation``  - Trigger downstream workflows (e.g. Zapier) on events.
5. ``erp``         - Persist Accounts Receivable / Payable records to SQL.

See ``pipeline.py`` for the orchestrator that wires these stages together,
and ``cli.py`` for the command-line entry point.
"""

__version__ = "1.0.3"
