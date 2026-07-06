# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.4] - 2026-07-06

### Fixed
- **Real Python 3.9 CI failure**: `erp/models.py` used PEP 604 union syntax
  (`str | None`) directly inside `Mapped[...]` type hints. Unlike a plain
  function parameter annotation, SQLAlchemy's declarative mapping actually
  evaluates these annotations to determine column types, which raises
  `TypeError` on genuine Python 3.9 (the `|` operator on `type` objects was
  only added in 3.10) even with `from __future__ import annotations` in
  effect. Replaced with `Mapped[Optional[str]]` / `Mapped[Optional[date]]`.
- For consistency, also normalized two function-parameter annotations
  (`session: requests.Session | None`) to `Optional[requests.Session]` in
  `zapier_client.py` and `parseur_client.py`. These were not actually
  evaluated at runtime and were not the cause of the CI failure, but keep
  the codebase consistent with the Python 3.9 compatibility policy
  documented in `pyproject.toml`.

## [1.0.3] - 2026-07-05

### Fixed
- Added `UP045` ("Use `X | None`") to the ruff ignore list, alongside
  `UP007`, for the same Python 3.9 / Pydantic compatibility reason (newer
  ruff versions split the old `Optional`/`Union` upgrade rule in two).
- Replaced a manual `for ... yield` loop with `yield from` in
  `email_ingestor.py` (ruff `UP028`).
- Collapsed a `RawDocument(...)` call in `tests/test_pipeline.py` that fit
  on one line at exactly the 100-character limit (`black`).

## [1.0.2] - 2026-07-04

### Fixed
- Replaced `typing.Iterator` with `collections.abc.Iterator` across the
  codebase (ruff `UP035`).
- Replaced `typing.List` / `typing.Dict` with the built-in generics `list` /
  `dict` (ruff `UP006`), which are fully supported on Python 3.9+ via
  PEP 585. `typing.Optional` is kept as-is (see `UP007` in the ruff
  configuration) since `X | None` syntax is not safely evaluable by Pydantic
  at runtime on Python 3.9.

## [1.0.1] - 2026-07-04

### Added
- Test coverage for the CLI (`cli.py`), the email ingestion adapter
  (`email_ingestor.py`), and the local Tesseract OCR client
  (`tesseract_client.py`).

### Fixed
- Formatting inconsistencies flagged by `black` in `pipeline.py`,
  `invoice_parser.py`, and several test files.
- Import ordering in `tests/test_pipeline.py`.
- Unclosed SQLite connections during tests and CLI runs: `SadeERPConnector`
  now exposes a `dispose()` method, called from the test fixtures, the CLI
  `run` command, and `scripts/run_demo.py`.

## [1.0.0] - 2026-07-04

### Added
- Initial public release of the invoice capture and ERP automation agent.
- Document ingestion adapters for email (IMAP) and scanner/watched-folder sources.
- OCR layer with a `Parseur` client and a local `Tesseract` fallback client.
- Invoice extraction and normalization pipeline, including a Dominican Republic
  NCF (Número de Comprobante Fiscal) format validator.
- Zapier webhook client for downstream workflow automation.
- SQL-based ERP repository layer (SADE-compatible schema) for Accounts
  Receivable and Accounts Payable postings.
- End-to-end pipeline orchestrator and command-line interface.
- Unit test suite with coverage reporting and GitHub Actions CI pipeline.
