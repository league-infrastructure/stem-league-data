"""System tests for loading JSON data into the SQLAlchemy data model.

This test creates a SQLite database, loads data from JSON files in tests/data,
and verifies the data is properly stored in the database.

Note: This test patches PostgreSQL-specific types to work with SQLite:
- JSONB -> JSON (stored as TEXT)
- ARRAY -> JSON (stored as TEXT)
"""

import json
from datetime import datetime
from pathlib import Path
from unittest import mock

import pytest
import requests
from sqlalchemy import create_engine, text, event, JSON
from sqlalchemy.orm import sessionmaker

# Patch PostgreSQL types BEFORE importing models
# This makes JSONB and ARRAY work with SQLite
from sqlalchemy.dialects import postgresql

# Create a mock JSONB that works like JSON
original_jsonb = postgresql.JSONB


class SQLiteCompatibleJSONB(JSON):
    """JSONB replacement that works with SQLite."""
    pass


# Patch ARRAY to work as JSON in SQLite
class SQLiteCompatibleARRAY(JSON):
    """ARRAY replacement that works with SQLite (stores as JSON)."""
    
    def __init__(self, *args, **kwargs):
        super().__init__()


# Apply patches
postgresql.JSONB = SQLiteCompatibleJSONB
postgresql.ARRAY = SQLiteCompatibleARRAY

# Now import models (they will use patched types)
from stem_league_data.models import (
    Base,
    Metro,
    Venue,
    Org,
    Person,
    Staff,
    Visitor,
    Service,
    Activity,
    Occurrence,
    Content,
    Announcement,
    Group,
    Program,
    Track,
    Category,
    SubCategory,
    Topic,
    Tag,
    Meetup,
    Pike13Service,
    P13Location,
)
from stem_league_data.models.events import RRule


# Path to test data
TEST_DATA_DIR = Path(__file__).parent.parent / "data"
TEST_DB_PATH = TEST_DATA_DIR / "test.db"

# External data URL
PAST_MEETUPS_URL = "https://snips.jtlapp.net/leaguesync/past_meetups.json"


@pytest.fixture(scope="module")
def engine():
    """Create a SQLite database engine for testing."""
    # Remove existing test database
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()
    
    engine = create_engine(f"sqlite:///{TEST_DB_PATH}", echo=False)
    
    # Enable foreign keys in SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    yield engine
    
    # Cleanup after tests (optional - keep for inspection)
    # if TEST_DB_PATH.exists():
    #     TEST_DB_PATH.unlink()


@pytest.fixture(scope="module")
def session(engine):
    """Create a database session."""
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def load_json(filepath: Path) -> list[dict]:
    """Load a JSON file and return its contents."""
    with open(filepath, "r") as f:
        return json.load(f)


def parse_datetime(value: str | None) -> datetime | None:
    """Parse an ISO datetime string."""
    if not value:
        return None
    try:
        # Handle ISO format with Z suffix
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        # Handle datetime with timezone offset like "2025-12-14 13:00:00-08:00"
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None


def parse_date(value: str | None):
    """Parse a date string."""
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


class TestDatabaseSetup:
    """Test database creation and table setup."""
    
    def test_database_created(self, engine):
        """Test that the database file was created."""
        assert TEST_DB_PATH.exists()
    
    def test_tables_created(self, engine):
        """Test that core tables were created."""
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ))
            tables = {row[0] for row in result}
        
        # Check key tables exist
        expected_tables = {
            "metros", "venues", "orgs",
            "persons", "staff", "visitors",
            "services", "activities", "occurrences",
            "contents", "groups", "tags",
            "meetups", "pike13_services", "p13_locations",
        }
        
        for table in expected_tables:
            assert table in tables, f"Table {table} not found. Found: {tables}"


class TestLoadMetro:
    """Test loading metro data."""
    
    def test_load_metro(self, session):
        """Load a default metro for San Diego."""
        metro = Metro(
            name="San Diego",
            slug="san-diego",
            timezone="America/Los_Angeles",
        )
        session.add(metro)
        session.commit()
        
        assert metro.id is not None
        assert metro.name == "San Diego"


class TestLoadPike13Locations:
    """Test loading Pike13 locations into P13Location."""
    
    def test_load_p13_locations(self, session):
        """Load Pike13 locations from JSON into P13Location table."""
        locations_file = TEST_DATA_DIR / "pike13" / "locations.json"
        if not locations_file.exists():
            pytest.skip("Pike13 locations file not found")
        
        locations = load_json(locations_file)
        
        loaded_count = 0
        for loc in locations:
            loc_id = loc.get("id")
            if not loc_id:
                continue
            
            p13_loc = P13Location(
                id=int(loc_id),
                code=loc.get("code"),
                name=loc.get("name"),
                address=loc.get("address"),
                latitude=loc.get("latitude"),
                longitude=loc.get("longitude"),
                phone=loc.get("phone"),
                description=loc.get("description"),
                slug=loc.get("slug"),
                position=loc.get("position"),
                formatted_address=loc.get("formatted_address"),
                street_address=loc.get("street_address"),
                street_address2=loc.get("street_address2"),
                city=loc.get("city"),
                state_code=loc.get("state_code"),
                postal_code=loc.get("postal_code"),
                country_code=loc.get("country_code"),
                timezone_friendly=loc.get("timezone_friendly"),
                timezone=loc.get("timezone"),
                type=loc.get("type"),
            )
            session.merge(p13_loc)
            loaded_count += 1
        
        session.commit()
        
        result = session.query(P13Location).all()
        assert len(result) == loaded_count
        
        # Verify some records have proper integer IDs
        first_loc = session.query(P13Location).first()
        assert isinstance(first_loc.id, int)


class TestLoadPike13Services:
    """Test loading Pike13 services."""
    
    def test_load_pike13_services(self, session):
        """Load Pike13 services from JSON."""
        services_file = TEST_DATA_DIR / "pike13" / "services.json"
        if not services_file.exists():
            pytest.skip("Pike13 services file not found")
        
        services = load_json(services_file)
        
        loaded_count = 0
        for svc in services:
            svc_id = svc.get("id")
            if not svc_id:
                continue
            
            # Extract price string from pricing object
            pricing = svc.get("pricing", {})
            single_visit = pricing.get("single_visit", {})
            base_price = single_visit.get("base_price", {})
            price_string = base_price.get("price_string")
            
            pike13_service = Pike13Service(
                id=int(svc_id),
                name=svc.get("name"),
                type=svc.get("type"),
                description=svc.get("description"),
                description_short=svc.get("description_short"),
                instructions=svc.get("instructions"),
                category_name=svc.get("category_name"),
                category_id=svc.get("category_id"),
                scheduled_events_count=svc.get("scheduled_events_count"),
                duration_in_minutes=svc.get("duration_in_minutes"),
                has_waitlist=svc.get("has_waitlist"),
                allow_recurring=svc.get("allow_recurring"),
                waitlist_only=svc.get("waitlist_only"),
                price_string=price_string,
            )
            session.merge(pike13_service)
            loaded_count += 1
        
        session.commit()
        
        result = session.query(Pike13Service).all()
        assert len(result) == loaded_count
        
        # Verify some records have proper integer IDs
        first_svc = session.query(Pike13Service).first()
        assert isinstance(first_svc.id, int)


class TestLoadVenuesFromP13Locations:
    """Test loading venues from Pike13 locations."""
    
    def test_load_venues_from_p13_locations(self, session):
        """Load Venue records from P13Location data."""
        metro = session.query(Metro).filter_by(slug="san-diego").first()
        p13_locations = session.query(P13Location).all()
        
        loaded_count = 0
        for loc in p13_locations[:10]:  # Load first 10
            venue = Venue(
                name=loc.name or "Unknown",
                address=loc.address or loc.formatted_address,
                metro_id=metro.id if metro else None,
            )
            session.add(venue)
            loaded_count += 1
        
        session.commit()
        
        venues = session.query(Venue).all()
        assert len(venues) == loaded_count


class TestLoadStaff:
    """Test loading staff from Pike13 staff data."""
    
    def test_load_persons_and_staff(self, session):
        """Load Pike13 staff as Person + Staff records."""
        staff_file = TEST_DATA_DIR / "pike13" / "staff.json"
        if not staff_file.exists():
            pytest.skip("Pike13 staff file not found")
        
        staff_data = load_json(staff_file)
        metro = session.query(Metro).filter_by(slug="san-diego").first()
        
        loaded_count = 0
        for s in staff_data[:20]:  # Load first 20
            # Create Person record
            person = Person(
                first_name=s.get("first_name", "Unknown"),
                last_name=s.get("last_name", "Unknown"),
                email=s.get("email"),
                phone=s.get("phone"),
                metro_id=metro.id if metro else None,
            )
            session.add(person)
            session.flush()  # Get the person ID
            
            # Create Staff record linked to Person
            staff = Staff(
                person_id=person.id,
                role=s.get("role"),
                bio=s.get("bio"),
                photo=s.get("profile_photo", {}).get("x200") if isinstance(s.get("profile_photo"), dict) else None,
                is_adult=True,
            )
            session.add(staff)
            loaded_count += 1
        
        session.commit()
        
        persons = session.query(Person).all()
        staff_records = session.query(Staff).all()
        assert len(persons) >= loaded_count
        assert len(staff_records) == loaded_count


class TestLoadProgramsCategoriesTopics:
    """Test loading Programs, Categories, and Topics from content.json."""
    
    def test_load_taxonomy_from_content(self, session):
        """Load programs, categories, and topics from content.json."""
        content_file = TEST_DATA_DIR / "content.json"
        if not content_file.exists():
            pytest.skip("Content file not found")
        
        content_data = load_json(content_file)
        
        # First, load Programs from _class: "Program" entries (they have content)
        programs_loaded = {}
        for item in content_data:
            if item.get("_class") == "Program":
                slug = item.get("slug")
                if not slug or slug in programs_loaded:
                    continue
                
                # Create Content for the program
                program_content = Content(
                    title=item.get("title", slug.replace("-", " ").title()),
                    blurb=item.get("blurb"),
                    description=item.get("description"),
                )
                session.add(program_content)
                session.flush()
                
                # Create Program with content
                program = Program(
                    title=item.get("title", slug.replace("-", " ").title()),
                    slug=slug,
                    content_id=program_content.id,
                )
                session.add(program)
                programs_loaded[slug] = program
        
        # Extract unique programs, categories, and topics from Class entries
        programs_seen = set()
        categories_seen = set()
        topics_seen = set()
        
        for item in content_data:
            if item.get("_class") != "Class":
                continue
                
            # Programs
            programs = item.get("programs", [])
            if isinstance(programs, str):
                programs = [programs]
            for p in programs:
                if p and p not in programs_loaded:
                    programs_seen.add(p)
            
            # Categories
            categories = item.get("categories", [])
            if isinstance(categories, str):
                categories = [categories]
            for c in categories:
                if c:
                    categories_seen.add(c)
            
            # Topics (using Topic model which is a Group subtype)
            topics = item.get("topics", [])
            if isinstance(topics, str):
                topics = [topics]
            for t in topics:
                if t:
                    topics_seen.add(t.strip())
        
        # Create Program records for any not already loaded (no content)
        for p in programs_seen:
            program = Program(
                title=p.replace("-", " ").title(),
                slug=p,
                content_id=None,  # No content for programs only referenced by slug
            )
            session.add(program)
        
        # Create Category records (no content for now)
        for c in categories_seen:
            category = Category(
                title=c.replace("-", " ").title(),
                slug=c,
                content_id=None,
            )
            session.add(category)
        
        # Create Topic records (no content - topics are just tags)
        for t in topics_seen:
            topic = Topic(
                title=t.replace("-", " ").title(),
                slug=t.lower().replace(" ", "-"),
                content_id=None,
            )
            session.add(topic)
        
        session.commit()
        
        programs = session.query(Program).all()
        categories = session.query(Category).all()
        topics = session.query(Topic).all()
        
        # Count programs with content
        programs_with_content = [p for p in programs if p.content_id is not None]
        
        print(f"\nLoaded: {len(programs)} programs ({len(programs_with_content)} with content), "
              f"{len(categories)} categories, {len(topics)} topics")
        
        total_programs = len(programs_loaded) + len(programs_seen)
        assert len(programs) == total_programs
        assert len(categories) == len(categories_seen)
        assert len(topics) == len(topics_seen)
        assert len(programs_with_content) == len(programs_loaded)


class TestLoadMeetupsFromURL:
    """Test fetching and loading Meetup events from external URL."""
    
    def test_fetch_and_load_past_meetups(self, session):
        """Fetch past_meetups.json from URL and load into Meetup table."""
        try:
            response = requests.get(PAST_MEETUPS_URL, timeout=10)
            response.raise_for_status()
            meetups_data = response.json()
        except (requests.RequestException, json.JSONDecodeError) as e:
            pytest.skip(f"Could not fetch meetups from URL: {e}")
        
        # The data structure has an 'events' key (list of event objects)
        events = meetups_data.get("events", [])
        if not events:
            pytest.skip("No events found in meetups data")
        
        loaded_count = 0
        for m in events[:50]:  # Load first 50
            meetup_id = m.get("id")
            if not meetup_id:
                continue
            
            # Parse venue info
            venue = m.get("venue", {}) or {}
            
            # Parse photo info
            photo = m.get("featuredEventPhoto", {}) or {}
            
            # Parse event hosts
            hosts = m.get("eventHosts", [])
            
            meetup = Meetup(
                id=str(meetup_id),
                title=m.get("title"),
                date_time=parse_datetime(m.get("dateTime")),
                description=m.get("description"),
                event_url=m.get("eventUrl"),
                status=m.get("status"),
                meetup_slug=m.get("meetup_slug"),
                group=m.get("group"),
                subgroup=m.get("subgroup"),
                group_path=m.get("group_path"),
                venue_id=venue.get("id"),
                venue_name=venue.get("name"),
                venue_address=venue.get("address"),
                photo_id=photo.get("id"),
                photo_base_url=photo.get("baseUrl"),
                title_font_size=m.get("title_font_size"),
                event_hosts=hosts,
            )
            session.merge(meetup)
            loaded_count += 1
        
        session.commit()
        
        result = session.query(Meetup).all()
        assert len(result) == loaded_count
        
        # Verify some records
        first_meetup = session.query(Meetup).first()
        assert first_meetup.id is not None
        print(f"\nLoaded {loaded_count} meetups from URL")


class TestLoadAnnouncements:
    """Test loading Announcements from content.json."""
    
    def test_load_announcements(self, session):
        """Load Announcement entries from content.json."""
        content_file = TEST_DATA_DIR / "content.json"
        if not content_file.exists():
            pytest.skip("Content file not found")
        
        content_data = load_json(content_file)
        
        loaded_count = 0
        for item in content_data:
            if item.get("_class") != "Announcement":
                continue
            
            # Create Content for the announcement
            announcement_content = Content(
                title=item.get("title", "Unknown"),
                blurb=item.get("content"),
                link=item.get("link"),
            )
            session.add(announcement_content)
            session.flush()
            
            # Create Announcement
            announcement = Announcement(
                content_id=announcement_content.id,
                from_date=parse_datetime(item.get("from_date")),
                until_date=parse_datetime(item.get("until_date")),
            )
            session.add(announcement)
            loaded_count += 1
        
        session.commit()
        
        announcements = session.query(Announcement).all()
        assert len(announcements) == loaded_count
        print(f"\nLoaded {loaded_count} announcements")


class TestRRuleValidation:
    """Test RRule composite value object validation and serialization."""
    
    def test_rrule_manual(self):
        """Test manual scheduling (no automatic occurrences)."""
        rule = RRule.manual()
        assert rule.frequency is None
        assert rule.is_valid()
        assert rule.to_ical_rrule() is None
        assert "Manual" in rule.describe()
    
    def test_rrule_once(self):
        """Test single occurrence scheduling."""
        rule = RRule.once()
        assert rule.frequency == "ONCE"
        assert rule.is_valid()
        assert rule.to_ical_rrule() is None
        assert "Single" in rule.describe()
    
    def test_rrule_weekly(self):
        """Test weekly recurring schedule."""
        # Wed/Fri
        rule = RRule.weekly(days=[2, 4])
        assert rule.frequency == "WEEKLY"
        assert rule.days == [2, 4]
        assert rule.interval == 1
        assert rule.is_valid()
        
        rrule_str = rule.to_ical_rrule()
        assert "FREQ=WEEKLY" in rrule_str
        assert "BYDAY=WE,FR" in rrule_str
        assert "Wednesday" in rule.describe()
        assert "Friday" in rule.describe()
    
    def test_rrule_weekly_with_interval(self):
        """Test biweekly schedule."""
        rule = RRule.weekly(days=[0], interval=2, count=10)
        assert rule.interval == 2
        assert rule.count == 10
        assert rule.is_valid()
        
        rrule_str = rule.to_ical_rrule()
        assert "INTERVAL=2" in rrule_str
        assert "COUNT=10" in rrule_str
    
    def test_rrule_monthly(self):
        """Test monthly on Nth weekday schedule."""
        # 4th Tuesday
        rule = RRule.monthly_weekday(weekday=1, week=4)
        assert rule.frequency == "MONTHLY"
        assert rule.days == [1]
        assert rule.setpos == 4
        assert rule.is_valid()
        
        rrule_str = rule.to_ical_rrule()
        assert "FREQ=MONTHLY" in rrule_str
        assert "BYDAY=TU" in rrule_str
        assert "BYSETPOS=4" in rrule_str
        assert "4th" in rule.describe()
        assert "Tuesday" in rule.describe()
    
    def test_rrule_monthly_last_weekday(self):
        """Test monthly on last Saturday schedule."""
        rule = RRule.monthly_weekday(weekday=5, week=-1)
        assert rule.setpos == -1
        assert rule.is_valid()
        assert "last" in rule.describe()
        assert "Saturday" in rule.describe()
    
    def test_rrule_validation_errors(self):
        """Test that invalid RRules are detected."""
        # Weekly without days
        rule = RRule(frequency="WEEKLY")
        errors = rule.validate()
        assert len(errors) > 0
        assert not rule.is_valid()
        
        # Monthly without setpos
        rule = RRule(frequency="MONTHLY", days=[1])
        errors = rule.validate()
        assert len(errors) > 0
        
        # Monthly with multiple days
        rule = RRule(frequency="MONTHLY", days=[1, 2], setpos=1)
        errors = rule.validate()
        assert len(errors) > 0
        
        # Invalid weekday
        rule = RRule(frequency="WEEKLY", days=[7])
        errors = rule.validate()
        assert len(errors) > 0
    
    def test_rrule_raise_if_invalid(self):
        """Test that raise_if_invalid raises ValueError."""
        rule = RRule(frequency="WEEKLY")  # Missing days
        with pytest.raises(ValueError, match="Invalid RRule"):
            rule.raise_if_invalid()
    
    def test_rrule_equality(self):
        """Test RRule equality comparison."""
        rule1 = RRule.weekly(days=[2, 4])
        rule2 = RRule.weekly(days=[2, 4])
        rule3 = RRule.weekly(days=[1, 3])
        
        assert rule1 == rule2
        assert rule1 != rule3
        assert rule1 != "not an RRule"
    
    def test_rrule_with_dates(self):
        """Test RRule with start_dt and end_dt."""
        from datetime import datetime
        
        start = datetime(2026, 1, 15, 16, 0, 0)
        end = datetime(2026, 3, 31, 17, 30, 0)
        
        rule = RRule.weekly(days=[2, 4], start_dt=start, end_dt=end)
        assert rule.start_dt == start
        assert rule.end_dt == end
        assert rule.is_valid()
        
        # Test once with dates
        rule_once = RRule.once(start_dt=start, end_dt=end)
        assert rule_once.start_dt == start
        assert rule_once.end_dt == end
        
        # Test monthly with dates
        rule_monthly = RRule.monthly_weekday(
            weekday=1, week=4, start_dt=start, end_dt=end
        )
        assert rule_monthly.start_dt == start
        assert rule_monthly.end_dt == end


class TestLoadServicesAndActivitiesFromContent:
    """Test loading Services and Activities by linking content.json Classes to Pike13."""
    
    def test_load_services_from_classes_with_pike13_link(self, session):
        """Find Class entries with services, link to Pike13, create Service+Activity."""
        content_file = TEST_DATA_DIR / "content.json"
        if not content_file.exists():
            pytest.skip("Content file not found")
        
        content_data = load_json(content_file)
        
        # Get Pike13 services for lookup
        pike13_services = {str(s.id): s for s in session.query(Pike13Service).all()}
        
        # Get taxonomy lookups
        programs_by_slug = {p.slug: p for p in session.query(Program).all()}
        categories_by_slug = {c.slug: c for c in session.query(Category).all()}
        topics_by_slug = {t.slug: t for t in session.query(Topic).all()}
        
        # Get a venue for activities
        venue = session.query(Venue).first()
        if not venue:
            pytest.skip("No venue available for activities")
        
        # Track services by slug
        services_by_slug = {}
        services_created = 0
        activities_created = 0
        activities_with_taxonomy = 0
        
        for item in content_data:
            if item.get("_class") != "Class":
                continue
            
            # Get services array (Pike13 service IDs)
            content_services = item.get("services", [])
            if not content_services:
                continue
            
            slug = item.get("slug")
            if not slug:
                continue
            
            # Find first Pike13 service ID from the services array
            pike13_id = None
            for svc_id in content_services:
                if str(svc_id) in pike13_services:
                    pike13_id = int(svc_id)
                    break
            
            # Create Service for each Class with services (keyed by slug)
            if slug not in services_by_slug:
                # Create Content for the service
                service_content = Content(
                    title=item.get("title", "Unknown"),
                    blurb=item.get("blurb"),
                    description=item.get("description"),
                )
                session.add(service_content)
                session.flush()
                
                service = Service(
                    slug=slug,
                    content_id=service_content.id,
                    pike13_service_id=pike13_id,
                    grade=item.get("grade"),
                    level=item.get("level"),
                )
                session.add(service)
                session.flush()
                services_by_slug[slug] = service
                services_created += 1
            
            # Get service for this activity
            service = services_by_slug.get(slug)
            
            # Create Content for the activity
            activity_content = Content(
                title=item.get("title", "Unknown"),
                blurb=item.get("blurb"),
                description=item.get("description"),
            )
            session.add(activity_content)
            session.flush()
            
            # Determine schedule from day_numbers if available
            day_numbers = item.get("day_numbers", [])
            start_dt = parse_datetime(item.get("start_date"))
            end_dt = parse_datetime(item.get("end_date"))
            
            if day_numbers:
                schedule = RRule.weekly(days=day_numbers, start_dt=start_dt, end_dt=end_dt)
            else:
                schedule = RRule.manual(start_dt=start_dt, end_dt=end_dt)
            
            # Create Activity with RRule schedule (start_dt/end_dt are in schedule)
            activity = Activity(
                type="class",
                status="published",
                service_id=service.id if service else None,
                content_id=activity_content.id,
                venue_id=venue.id,
                enrollment_closes=parse_datetime(item.get("enrollment_closes")),
                schedule_link=item.get("enroll_link"),
                active=item.get("active", True),
                capacity=20,
                schedule=schedule,
            )
            session.add(activity)
            session.flush()
            
            # Link activity to programs
            item_programs = item.get("programs", [])
            if isinstance(item_programs, str):
                item_programs = [item_programs]
            for p_slug in item_programs:
                if p_slug in programs_by_slug:
                    activity.programs.append(programs_by_slug[p_slug])
            
            # Link activity to categories
            item_categories = item.get("categories", [])
            if isinstance(item_categories, str):
                item_categories = [item_categories]
            for c_slug in item_categories:
                if c_slug in categories_by_slug:
                    activity.categories.append(categories_by_slug[c_slug])
            
            # Link activity to topics
            item_topics = item.get("topics", [])
            if isinstance(item_topics, str):
                item_topics = [item_topics]
            for t in item_topics:
                t_slug = t.lower().replace(" ", "-")
                if t_slug in topics_by_slug:
                    activity.topics.append(topics_by_slug[t_slug])
            
            if activity.programs or activity.categories or activity.topics:
                activities_with_taxonomy += 1
            
            activities_created += 1
        
        session.commit()
        
        services = session.query(Service).all()
        activities = session.query(Activity).all()
        
        print(f"\nCreated {services_created} services and {activities_created} activities")
        print(f"Activities with taxonomy links: {activities_with_taxonomy}")
        
        assert services_created >= 12, f"Expected at least 12 services, got {services_created}"
        assert len(activities) == activities_created
        assert activities_with_taxonomy > 0, "Expected some activities to have taxonomy links"
        
        # Verify pike13_service_id is linked
        services_with_pike13 = [s for s in services if s.pike13_service_id is not None]
        print(f"Services linked to Pike13: {len(services_with_pike13)}")


class TestLoadOccurrences:
    """Test loading occurrences from Pike13 data."""
    
    def test_load_occurrences(self, session):
        """Load Pike13 occurrences as Occurrence records."""
        occurrences_file = TEST_DATA_DIR / "pike13" / "occurrences.json"
        if not occurrences_file.exists():
            pytest.skip("Pike13 occurrences file not found")
        
        occurrences_data = load_json(occurrences_file)
        
        # Get an activity to associate occurrences with
        activity = session.query(Activity).first()
        if not activity:
            pytest.skip("No activity available for occurrences")
        
        loaded_count = 0
        for occ in occurrences_data[:50]:  # Load first 50
            start_time = parse_datetime(occ.get("start_at"))
            end_time = parse_datetime(occ.get("end_at"))
            
            if not start_time or not end_time:
                continue
            
            occurrence = Occurrence(
                activity_id=activity.id,
                start_time=start_time,
                end_time=end_time,
                rsvp_count=0,
                visitor_count=0,
                walk_in_count=0,
                notes=occ.get("description", "")[:500] if occ.get("description") else None,
            )
            session.add(occurrence)
            loaded_count += 1
        
        session.commit()
        
        result = session.query(Occurrence).all()
        assert len(result) == loaded_count


class TestDataIntegrity:
    """Test data integrity after all loads."""
    
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
            "Announcement": session.query(Announcement).count(),
        }
        
        print("\nData counts:")
        for name, count in counts.items():
            print(f"  {name}: {count}")
        
        # Verify we have data in key tables
        assert counts["Metro"] >= 1
        assert counts["Venue"] >= 1
        assert counts["Person"] >= 1
        assert counts["Pike13Service"] >= 1
        assert counts["P13Location"] >= 1
        assert counts["Meetup"] >= 1
        assert counts["Program"] >= 1
        assert counts["Topic"] >= 1
        assert counts["Service"] >= 1
        assert counts["Activity"] >= 1
        
        # Verify activities have taxonomy links
        activities_with_programs = session.query(Activity).filter(Activity.programs.any()).count()
        activities_with_categories = session.query(Activity).filter(Activity.categories.any()).count()
        activities_with_topics = session.query(Activity).filter(Activity.topics.any()).count()
        
        print(f"\nActivities with programs: {activities_with_programs}")
        print(f"Activities with categories: {activities_with_categories}")
        print(f"Activities with topics: {activities_with_topics}")
        
        assert activities_with_programs > 0, "Expected some activities linked to programs"
        assert activities_with_categories > 0, "Expected some activities linked to categories"
        assert activities_with_topics > 0, "Expected some activities linked to topics"
