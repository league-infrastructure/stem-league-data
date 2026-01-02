"""Pytest configuration and fixtures for unit tests."""

import sys
from pathlib import Path

# Add the project root to Python path for tests
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest

from tests.lib.api_client import DatabaseTestManager


@pytest.fixture
def test_db():
    """Fixture providing a test database manager with tables created.
    
    Tables are created before the test and dropped after.
    
    Usage:
        def test_something(test_db):
            with test_db.session_scope() as session:
                session.add(SomeModel(...))
    """
    manager = DatabaseTestManager()
    manager.setup()
    yield manager
    manager.teardown()


@pytest.fixture
def client(test_db):
    """Fixture providing a FastAPI test client with test database.
    
    The database dependency is overridden to use the test database.
    
    Usage:
        def test_endpoint(client):
            response = client.get("/api/orgs")
            assert response.status_code == 200
    """
    from stem_league_data.app import app
    
    with test_db.get_test_client(app) as test_client:
        yield test_client


@pytest.fixture
def seeded_db(test_db):
    """Fixture providing a test database with seed data.
    
    Creates basic test data for common entities.
    
    Usage:
        def test_with_data(seeded_db, client):
            response = client.get("/api/orgs")
            assert len(response.json()) > 0
    """
    from stem_league_data.models import Metro, Org, Venue, Content
    
    with test_db.session_scope() as session:
        # Create a metro
        metro = Metro(
            id=1,
            name="Test Metro",
            slug="test-metro",
        )
        session.add(metro)
        session.flush()
        
        # Create an org (no slug field on Org model)
        org = Org(
            id=1,
            name="Test Organization",
            metro_id=metro.id,
        )
        session.add(org)
        session.flush()
        
        # Create a venue (no slug field on Venue model)
        venue = Venue(
            id=1,
            name="Test Venue",
            address="123 Test St",
            metro_id=metro.id,
            org_id=org.id,
        )
        session.add(venue)
        
        # Create some content
        content = Content(
            id=1,
            title="Test Content",
            blurb="Test blurb",
            content_type="content",
        )
        session.add(content)
    
    yield test_db


@pytest.fixture
def seeded_client(seeded_db):
    """Fixture providing a test client with seeded database.
    
    Combines seeded_db and client fixtures.
    
    Usage:
        def test_with_data(seeded_client):
            response = seeded_client.get("/api/orgs")
            assert len(response.json()) == 1
    """
    from stem_league_data.app import app
    
    with seeded_db.get_test_client(app) as test_client:
        yield test_client
