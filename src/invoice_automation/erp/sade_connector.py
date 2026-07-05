"""SQL connection management for the SADE ERP integration.

The specialist implementing this kind of integration is typically not
responsible for the ERP's own interface; the responsibility is to produce a
correct, well-typed "data matrix" that the ERP's SQL database can ingest.
This module manages the SQLAlchemy engine/session lifecycle so the
``repository`` module can focus purely on that data matrix.

Any SQLAlchemy-compatible database can be used by changing
``SADE_DATABASE_URL`` (see ``.env.example``): SQLite for local development
and tests, or PostgreSQL / MySQL / SQL Server for a real SADE deployment.
"""

from __future__ import annotations

import logging

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from invoice_automation.config import ERPSettings
from invoice_automation.erp.models import Base
from invoice_automation.exceptions import ERPIntegrationError

logger = logging.getLogger(__name__)


class SadeERPConnector:
    """Manages the SQL engine and sessions used to talk to the SADE ERP database."""

    def __init__(self, settings: ERPSettings) -> None:
        self._settings = settings
        self._engine: Engine = self._build_engine()
        self._session_factory = sessionmaker(bind=self._engine, expire_on_commit=False)

    def _build_engine(self) -> Engine:
        try:
            return create_engine(self._settings.database_url, future=True)
        except Exception as exc:  # noqa: BLE001 - surface any connection-string error uniformly
            raise ERPIntegrationError(
                f"Could not create SQL engine for '{self._settings.database_url}': {exc}"
            ) from exc

    def initialize_schema(self) -> None:
        """Create the integration tables if they do not already exist.

        In a production deployment against a live SADE database, this would
        typically be replaced by pointing the engine at the ERP's own
        existing tables/views rather than creating new ones.
        """
        Base.metadata.create_all(self._engine)
        logger.info("ERP integration schema is ready")

    def session(self) -> Session:
        """Return a new SQLAlchemy session bound to the ERP database."""
        return self._session_factory()

    @property
    def engine(self) -> Engine:
        return self._engine

    def dispose(self) -> None:
        """Release the underlying connection pool.

        Should be called when the connector is no longer needed (e.g. at the
        end of a CLI command or in test teardown) to avoid leaking open
        database connections, particularly with file-based SQLite engines.
        """
        self._engine.dispose()
