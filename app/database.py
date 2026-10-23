"""SQLAlchemy database engine and session management."""

from __future__ import annotations

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app import config

engine = create_engine(
    config.DATABASE_URL,
    connect_args={"check_same_thread": False},  # required for SQLite
    echo=False,
)

# Enable WAL mode and foreign keys for SQLite
@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_conn, _connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.close()


SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db() -> Session:  # type: ignore[misc]
    """FastAPI dependency: yield a DB session and close it after the request."""
    db = SessionLocal()
    try:
        yield db  # type: ignore[misc]
    finally:
        db.close()
