from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session

from src.core.config import get_settings


class Base(DeclarativeBase):
    """Base class for SQLAlchemy ORM models."""
    pass


def _build_engine_url() -> str:
    settings = get_settings()
    return settings.DATABASE_URL


# Create SQLAlchemy engine
DATABASE_URL = _build_engine_url()

# SQLite requires check_same_thread=False for use across threads
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, echo=False, future=True, connect_args=connect_args)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=Session)


# PUBLIC_INTERFACE
def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session and ensures cleanup.

    Yields:
        Session: SQLAlchemy ORM session bound to application engine.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
# PUBLIC_INTERFACE
def db_session() -> Generator[Session, None, None]:
    """Context manager for DB sessions outside FastAPI dependency system.

    Yields:
        Session: SQLAlchemy session with automatic commit/rollback.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
