"""SQLAlchemy database engine and session factory.

Usage::

    from services.storage.database import get_engine, get_session

    engine = get_engine()          # reads DATABASE_URL from env
    with get_session(engine) as db:
        db.execute(...)
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


_DEFAULT_SQLITE_URL = "sqlite:///data/news_intelligence.db"


def get_database_url() -> str:
    """Return the database URL from environment or fall back to SQLite."""
    return os.environ.get("DATABASE_URL", _DEFAULT_SQLITE_URL)


def get_engine(
    url: str | None = None,
    *,
    pool_size: int = 10,
    max_overflow: int = 20,
    echo: bool = False,
) -> Engine:
    """Create a SQLAlchemy engine with connection-pool settings.

    For PostgreSQL the pool is fully configured.  For SQLite (local dev /
    tests) pooling is disabled because SQLite does not support concurrent
    writers.
    """
    url = url or get_database_url()

    if url.startswith("sqlite"):
        engine = create_engine(
            url,
            echo=echo,
            connect_args={"check_same_thread": False},
            pool_pre_ping=True,
        )
        # Enable WAL mode and foreign-key enforcement for SQLite.
        @event.listens_for(engine, "connect")
        def _set_sqlite_pragma(dbapi_conn, _connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        return engine

    return create_engine(
        url,
        echo=echo,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_pre_ping=True,
        pool_recycle=3600,
    )


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Return a configured ``sessionmaker`` bound to *engine*."""
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)


@contextmanager
def get_session(
    engine: Engine | None = None,
) -> Generator[Session, None, None]:
    """Provide a transactional database session.

    Commits on clean exit, rolls back on exception.
    """
    eng = engine or get_engine()
    factory = make_session_factory(eng)
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
