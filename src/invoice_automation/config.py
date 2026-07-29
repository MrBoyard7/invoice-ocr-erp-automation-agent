"""Centralized application configuration.

Configuration values are read from environment variables (optionally loaded
from a local ``.env`` file via ``python-dotenv``). Every setting has a sane
default for local development and testing, so the pipeline can run out of
the box against a local SQLite database and stubbed OCR/automation clients.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

# Load variables from a local ".env" file if present. This is a no-op in
# environments (such as CI) where the file does not exist.
load_dotenv()


def _get_bool(name: str, default: bool) -> bool:
    """Parse a boolean environment variable."""
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class EmailSettings:
    """IMAP configuration used by the email ingestion adapter."""

    host: str = field(default_factory=lambda: os.getenv("IMAP_HOST", "imap.example.com"))
    port: int = field(default_factory=lambda: int(os.getenv("IMAP_PORT", "993")))
    username: str = field(default_factory=lambda: os.getenv("IMAP_USERNAME", ""))
    password: str = field(default_factory=lambda: os.getenv("IMAP_PASSWORD", ""))
    mailbox: str = field(default_factory=lambda: os.getenv("IMAP_MAILBOX", "INBOX"))
    use_ssl: bool = field(default_factory=lambda: _get_bool("IMAP_USE_SSL", True))


@dataclass(frozen=True)
class ScannerSettings:
    """Filesystem configuration used by the scanner ingestion adapter."""

    watch_folder: str = field(
        default_factory=lambda: os.getenv("SCANNER_WATCH_FOLDER", "./data/incoming_scans")
    )
    processed_folder: str = field(
        default_factory=lambda: os.getenv("SCANNER_PROCESSED_FOLDER", "./data/processed_scans")
    )


@dataclass(frozen=True)
class ParseurSettings:
    """Configuration for the Parseur OCR API client."""

    api_key: str = field(default_factory=lambda: os.getenv("PARSEUR_API_KEY", ""))
    mailbox_id: str = field(default_factory=lambda: os.getenv("PARSEUR_MAILBOX_ID", ""))
    base_url: str = field(
        default_factory=lambda: os.getenv("PARSEUR_BASE_URL", "https://api.parseur.com")
    )


@dataclass(frozen=True)
class ZapierSettings:
    """Configuration for the Zapier webhook automation client."""

    webhook_url: str = field(default_factory=lambda: os.getenv("ZAPIER_WEBHOOK_URL", ""))


@dataclass(frozen=True)
class ERPSettings:
    """Configuration for the SADE ERP SQL connection."""

    database_url: str = field(
        default_factory=lambda: os.getenv("SADE_DATABASE_URL", "sqlite:///./demo.db")
    )


@dataclass(frozen=True)
class Settings:
    """Aggregate application settings."""

    email: EmailSettings = field(default_factory=EmailSettings)
    scanner: ScannerSettings = field(default_factory=ScannerSettings)
    parseur: ParseurSettings = field(default_factory=ParseurSettings)
    zapier: ZapierSettings = field(default_factory=ZapierSettings)
    erp: ERPSettings = field(default_factory=ERPSettings)
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    environment: str = field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))


def get_settings() -> Settings:
    """Build a fresh ``Settings`` instance from the current environment.

    A factory function (rather than a module-level singleton) makes it easy
    to reload configuration in tests after mutating environment variables.
    """
    return Settings()
