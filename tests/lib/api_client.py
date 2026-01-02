"""FastAPI test client utilities.

Provides test client setup with database dependency injection
for both SQLite and PostgreSQL databases.
"""

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Callable

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from stem_league_data.models import Base
from stem_league_data.database import get_db


def _setup_sqlite_compatibility() -> None:
    """Set up SQLite compatibility for PostgreSQL types."""
    from sqlalchemy.dialects.postgresql import JSONB, ARRAY
    from sqlalchemy.ext.compiler import compiles
    
    # Only register if not already registered
    # These decorators are idempotent for the same function
    @compiles(JSONB, 'sqlite')
    def compile_jsonb_sqlite(element, compiler, **kw):
        """Render JSONB as JSON for SQLite."""
        return "JSON"
    
    @compiles(ARRAY, 'sqlite')
    def compile_array_sqlite(element, compiler, **kw):
        """Render ARRAY as TEXT (stored as JSON) for SQLite."""
        return "TEXT"


def create_test_engine(
    database_url: str | None = None,
    in_memory: bool = True,
):
    """Create a test database engine.
    
    Args:
        database_url: Database URL. If None, uses TEST_DATABASE_URL env var
                     or defaults to in-memory SQLite.
        in_memory: If True and no URL provided, use in-memory SQLite.
                  Ignored if database_url is provided.
    
    Returns:
        SQLAlchemy engine configured for testing.
    """
    if database_url is None:
        database_url = os.getenv("TEST_DATABASE_URL")
    
    if database_url is None:
        if in_memory:
            database_url = "sqlite:///:memory:"
        else:
            # Use a temp file for persistent test database
            test_db_path = Path(__file__).parent.parent / "data" / "test_api.db"
            database_url = f"sqlite:///{test_db_path}"
    
    is_sqlite = database_url.startswith("sqlite")
    
    if is_sqlite:
        _setup_sqlite_compatibility()
        
        # For in-memory SQLite, use StaticPool to share connection across threads
        if ":memory:" in database_url:
            engine = create_engine(
                database_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
            )
        else:
            engine = create_engine(
                database_url,
                connect_args={"check_same_thread": False},
            )
        
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """Enable foreign keys for SQLite."""
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
    else:
        # PostgreSQL or other database
        engine = create_engine(database_url, pool_pre_ping=True)
    
    return engine


def create_test_session_factory(engine) -> sessionmaker:
    """Create a session factory for testing.
    
    Args:
        engine: SQLAlchemy engine.
    
    Returns:
        Session factory bound to the engine.
    """
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


class TestDatabaseManager:
    """Manages test database lifecycle and provides session injection.
    
    Usage:
        manager = TestDatabaseManager()
        manager.setup()  # Creates tables
        
        # Get a test client with database injection
        with manager.get_test_client(app) as client:
            response = client.get("/api/orgs")
            assert response.status_code == 200
        
        manager.teardown()  # Drops tables
    
    Or use the context manager:
        with TestDatabaseManager() as manager:
            with manager.get_test_client(app) as client:
                response = client.get("/api/orgs")
    """
    
    def __init__(
        self,
        database_url: str | None = None,
        in_memory: bool = True,
    ):
        """Initialize test database manager.
        
        Args:
            database_url: Database URL. Defaults to in-memory SQLite.
            in_memory: Use in-memory SQLite if no URL provided.
        """
        self.engine = create_test_engine(database_url, in_memory)
        self.SessionFactory = create_test_session_factory(self.engine)
        self._tables_created = False
    
    def setup(self) -> None:
        """Create all database tables."""
        Base.metadata.create_all(bind=self.engine)
        self._tables_created = True
    
    def teardown(self) -> None:
        """Drop all database tables."""
        Base.metadata.drop_all(bind=self.engine)
        self._tables_created = False
    
    def reset(self) -> None:
        """Drop and recreate all tables."""
        self.teardown()
        self.setup()
    
    def get_session(self) -> Generator[Session, None, None]:
        """Get a database session (generator for dependency injection).
        
        Yields:
            SQLAlchemy session.
        """
        session = self.SessionFactory()
        try:
            yield session
        finally:
            session.close()
    
    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """Context manager for a database session.
        
        Yields:
            SQLAlchemy session that commits on success, rolls back on error.
        """
        session = self.SessionFactory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    @contextmanager
    def get_test_client(self, app: FastAPI) -> Generator[TestClient, None, None]:
        """Get a test client with database dependency overridden.
        
        Args:
            app: FastAPI application instance.
        
        Yields:
            TestClient with database dependency pointing to test database.
        """
        # Override the get_db dependency
        app.dependency_overrides[get_db] = self.get_session
        
        try:
            with TestClient(app) as client:
                yield client
        finally:
            # Clear dependency overrides
            app.dependency_overrides.clear()
    
    def __enter__(self) -> "TestDatabaseManager":
        """Enter context manager - sets up tables."""
        self.setup()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager - tears down tables."""
        self.teardown()


def get_test_client(
    app: FastAPI,
    database_url: str | None = None,
    setup_tables: bool = True,
) -> Generator[tuple[TestClient, TestDatabaseManager], None, None]:
    """Convenience function to get a test client with managed database.
    
    This is a generator that yields a tuple of (client, manager) and handles
    setup/teardown automatically.
    
    Args:
        app: FastAPI application instance.
        database_url: Database URL. Defaults to in-memory SQLite.
        setup_tables: Whether to create tables on setup.
    
    Yields:
        Tuple of (TestClient, TestDatabaseManager).
    
    Example:
        def test_endpoint():
            from stem_league_data.app import app
            
            with get_test_client(app) as (client, db):
                # Tables are created, dependency is injected
                response = client.get("/api/orgs")
                assert response.status_code == 200
                
                # Can access db manager for seeding data
                with db.session_scope() as session:
                    session.add(Org(name="Test Org"))
    """
    manager = TestDatabaseManager(database_url=database_url)
    
    if setup_tables:
        manager.setup()
    
    try:
        with manager.get_test_client(app) as client:
            yield client, manager
    finally:
        if setup_tables:
            manager.teardown()


# Pytest fixtures - can be imported in conftest.py
def pytest_test_db_fixture():
    """Returns a pytest fixture for test database manager.
    
    Usage in conftest.py:
        from tests.lib.api_client import pytest_test_db_fixture
        test_db = pytest_test_db_fixture()
    
    Or define it manually in conftest.py:
        @pytest.fixture
        def test_db():
            manager = TestDatabaseManager()
            manager.setup()
            yield manager
            manager.teardown()
    """
    import pytest
    
    @pytest.fixture
    def test_db():
        manager = TestDatabaseManager()
        manager.setup()
        yield manager
        manager.teardown()
    
    return test_db


def pytest_test_client_fixture():
    """Returns a pytest fixture for test client.
    
    Usage in conftest.py:
        from tests.lib.api_client import pytest_test_client_fixture
        client = pytest_test_client_fixture()
    """
    import pytest
    
    @pytest.fixture
    def client(test_db):
        from stem_league_data.app import app
        
        with test_db.get_test_client(app) as client:
            yield client
    
    return client
