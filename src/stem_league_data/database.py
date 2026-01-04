"""Database configuration and session management for FastAPI."""

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine, event, JSON, String
from sqlalchemy.orm import Session, sessionmaker

from stem_league_data.models import Base
from stem_league_data.config import get_database_url

# Database URL from environment or defaults (with ROOT_DIR resolution)
DATABASE_URL = get_database_url()

# Determine if using SQLite
_is_sqlite = DATABASE_URL.startswith("sqlite")

# Create engine with appropriate settings
if _is_sqlite:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        """Enable foreign keys for SQLite."""
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    # Patch PostgreSQL types to SQLite-compatible types
    from sqlalchemy.dialects.postgresql import JSONB, ARRAY
    
    # Use compiler hooks to convert types
    from sqlalchemy.ext.compiler import compiles
    
    @compiles(JSONB, 'sqlite')
    def compile_jsonb_sqlite(element, compiler, **kw):
        """Render JSONB as JSON for SQLite."""
        return "JSON"
    
    @compiles(ARRAY, 'sqlite')
    def compile_array_sqlite(element, compiler, **kw):
        """Render ARRAY as TEXT (stored as JSON) for SQLite."""
        return "TEXT"
else:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """Drop all database tables."""
    Base.metadata.drop_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency to get a database session.
    
    Use as a FastAPI dependency:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """Context manager to get a database session.
    
    Use for scripts and CLI:
        with get_db_context() as db:
            ...
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
