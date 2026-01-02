"""Test loading data from JSON dump files into SQLite database.

This test loads data from JSON files in tests/dump into a fresh SQLite database
and verifies the data integrity. This is faster than test_ext_data_load.py since
it doesn't require external network access.

Note: This test patches PostgreSQL-specific types to work with SQLite:
- JSONB -> JSON (stored as TEXT)
- ARRAY -> JSON (stored as TEXT)
"""

import json
import sys
from pathlib import Path

import pytest
from sqlalchemy import JSON, text

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Patch PostgreSQL types BEFORE importing models
from sqlalchemy.dialects import postgresql


class SQLiteCompatibleJSONB(JSON):
    """JSONB replacement that works with SQLite."""
    pass


class SQLiteCompatibleARRAY(JSON):
    """ARRAY replacement that works with SQLite (stores as JSON)."""
    
    def __init__(self, *args, **kwargs):
        super().__init__()


postgresql.JSONB = SQLiteCompatibleJSONB
postgresql.ARRAY = SQLiteCompatibleARRAY

# Now import models
from stem_league_data.models import (
    Base,
    Metro,
    Venue,
    Person,
    Staff,
    Service,
    Activity,
    Occurrence,
    Content,
    Program,
    Category,
    Topic,
    Meetup,
    Pike13Service,
    P13Location,
)

from tests.lib.workspace import find_workspace_root, get_test_dump_dir
from tests.lib.database import (
    create_sqlite_engine,
    create_session,
    load_database_from_json,
    json_decoder_hook,
)


# Find paths
WORKSPACE_ROOT = find_workspace_root(__file__)
TEST_DUMP_DIR = get_test_dump_dir(__file__)
TEST_DB_PATH = WORKSPACE_ROOT / "tests" / "data" / "test_from_dump.db"

# Table loading order (respects foreign key constraints)
TABLE_ORDER = [
    # Independent tables first
    "metros",
    "contents",
    "pike13_services",
    "p13_locations",
    "meetups",
    "tags",
    # Tables with FKs to metros/contents
    "orgs",
    "venues",
    "groups",  # Programs, Categories, Topics etc. (uses content_id)
    "persons",
    # Tables with FKs to persons
    "staff",
    "visitors",
    # Tables with FKs to services/venues
    "services",
    "activities",
    # Tables with FKs to activities
    "occurrences",
    "registrations",
    "rsvps",
    "marketingstats",
    "flyers",
    "announcements",
    "instructor_assignments",
    # Association tables
    "activity_programs",
    "activity_tracks",
    "activity_categories",
    "activity_topics",
    "activity_subcategories",
    "activity_tags",
    "service_topics",
    "service_tracks",
    "service_categories",
    "service_subcategories",
    "flyer_activities",
]


@pytest.fixture(scope="module")
def engine():
    """Create a SQLite database engine for testing."""
    # Check if dump files exist
    if not TEST_DUMP_DIR.exists() or not list(TEST_DUMP_DIR.glob("*.json")):
        pytest.skip(
            f"Dump files not found in {TEST_DUMP_DIR}. "
            "Run dump_db_to_json.py first."
        )
    
    # Remove existing test database
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()
    
    engine = create_sqlite_engine(TEST_DB_PATH)
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    yield engine


@pytest.fixture(scope="module")
def session(engine):
    """Create a database session."""
    session = create_session(engine)
    yield session
    session.close()


class TestLoadFromDump:
    """Test loading database from JSON dump files."""
    
    def test_load_all_tables(self, session):
        """Load all tables from JSON dump files."""
        counts = load_database_from_json(
            session,
            TEST_DUMP_DIR,
            table_order=TABLE_ORDER,
        )
        session.commit()
        
        print(f"\nLoaded {len(counts)} tables from dump:")
        for table_name, count in sorted(counts.items()):
            print(f"  {table_name}: {count} rows")
        
        # Verify at least some tables were loaded
        assert len(counts) > 0, "No tables were loaded"
        
        # Check key tables have data
        key_tables = ["metros", "venues", "services", "activities"]
        for table in key_tables:
            if table in counts:
                assert counts[table] > 0, f"Table {table} has no data"


class TestDataIntegrity:
    """Test data integrity after loading from dump."""
    
    def test_foreign_key_relationships(self, session):
        """Test that foreign key relationships are valid."""
        # Staff should have valid person_id
        staff_records = session.query(Staff).all()
        for staff in staff_records:
            person = session.query(Person).filter_by(id=staff.person_id).first()
            assert person is not None, f"Staff {staff.id} has invalid person_id"
        
        # Activities should have valid venue_id
        activities = session.query(Activity).all()
        for activity in activities:
            venue = session.query(Venue).filter_by(id=activity.venue_id).first()
            assert venue is not None, f"Activity {activity.id} has invalid venue_id"
        
        # Occurrences should have valid activity_id
        occurrences = session.query(Occurrence).all()
        for occ in occurrences:
            activity = session.query(Activity).filter_by(id=occ.activity_id).first()
            assert activity is not None, f"Occurrence {occ.id} has invalid activity_id"
    
    def test_data_counts(self, session):
        """Test that reasonable amounts of data were loaded."""
        counts = {
            "Metro": session.query(Metro).count(),
            "Venue": session.query(Venue).count(),
            "Person": session.query(Person).count(),
            "Staff": session.query(Staff).count(),
            "Service": session.query(Service).count(),
            "Activity": session.query(Activity).count(),
            "Occurrence": session.query(Occurrence).count(),
            "Pike13Service": session.query(Pike13Service).count(),
            "P13Location": session.query(P13Location).count(),
            "Meetup": session.query(Meetup).count(),
            "Program": session.query(Program).count(),
            "Category": session.query(Category).count(),
            "Topic": session.query(Topic).count(),
        }
        
        print("\nData counts:")
        for name, count in counts.items():
            print(f"  {name}: {count}")
        
        # Verify we have data in key tables
        assert counts["Metro"] >= 1
        assert counts["Venue"] >= 1
        assert counts["Person"] >= 1


class TestActivitySchedule:
    """Test Activity schedule (RRule composite) loading."""
    
    def test_activities_have_schedule(self, session):
        """Test that activities have schedule data loaded correctly."""
        activities = session.query(Activity).all()
        
        activities_with_schedule = 0
        for activity in activities:
            if activity.schedule is not None:
                activities_with_schedule += 1
                # Verify schedule has expected attributes
                assert hasattr(activity.schedule, "frequency")
                assert hasattr(activity.schedule, "days")
        
        print(f"\nActivities with schedule: {activities_with_schedule}/{len(activities)}")
