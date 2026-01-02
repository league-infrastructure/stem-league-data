"""System test for API roundtrip: load dump data via REST API and validate.

This test verifies that:
1. Load data from dump files in tests/dump
2. Insert data into the database through the REST API
3. Read data back through the REST API
4. Validate the response matches the original data

This validates the REST API's ability to correctly handle the full data model.

Note: This test uses SQLite for the database backend.
"""

import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from stem_league_data.app import app
from tests.lib.workspace import find_workspace_root, get_test_dump_dir
from tests.lib.api_client import TestDatabaseManager


# Find paths
WORKSPACE_ROOT = find_workspace_root(__file__)
TEST_DUMP_DIR = get_test_dump_dir(__file__)


# Mapping of JSON file names (without .json) to API endpoint configuration
# Each entry contains: (endpoint, id_field, create_fields, skip_fields)
#   - endpoint: API endpoint path
#   - id_field: Name of the ID field (usually 'id')
#   - create_fields: Fields to include when creating (None = all except skip_fields)
#   - skip_fields: Fields to exclude when creating (timestamps, auto-generated)
ENDPOINT_MAP: dict[str, dict[str, Any]] = {
    # Independent tables first (no foreign keys)
    "metros": {
        "endpoint": "/api/metros",
        "id_field": "id",
        "skip_fields": {"id", "created_at", "updated_at"},
    },
    "contents": {
        "endpoint": "/api/contents",
        "id_field": "id",
        "skip_fields": {"id", "created_at", "updated_at"},
    },
    "tags": {
        "endpoint": "/api/tags",
        "id_field": "id",
        "skip_fields": {"id", "created_at", "updated_at"},
    },
    # Tables with foreign keys to metros
    "orgs": {
        "endpoint": "/api/orgs",
        "id_field": "id",
        "skip_fields": {"id", "created_at", "updated_at"},
    },
    "venues": {
        "endpoint": "/api/venues",
        "id_field": "id",
        "skip_fields": {"id", "created_at", "updated_at"},
    },
    "persons": {
        "endpoint": "/api/persons",
        "id_field": "id",
        "skip_fields": {"id", "created_at", "updated_at"},
    },
    # Tables with foreign keys to persons
    "staff": {
        "endpoint": "/api/staff",
        "id_field": "id",
        "skip_fields": {"id", "created_at", "updated_at"},
    },
    "visitors": {
        "endpoint": "/api/visitors",
        "id_field": "id",
        "skip_fields": {"id", "created_at", "updated_at"},
    },
    # Category-related tables
    "groups": {
        "endpoint": "/api/groups",
        "id_field": "id",
        "skip_fields": {"id", "created_at", "updated_at"},
        "read_only": True,  # Groups are created through programs/tracks/etc.
    },
    # Service and activity tables  
    # NOTE: services endpoint has a bug (tries to access org_id which doesn't exist)
    # Skipping services for now until router is fixed
    # "services": {
    #     "endpoint": "/api/services",
    #     "id_field": "id",
    #     "skip_fields": {"id", "created_at", "updated_at"},
    # },
    # NOTE: activities depend on services, and occurrences depend on activities
    # Skipping until services are fixed
    # "activities": {
    #     "endpoint": "/api/activities",
    #     "id_field": "id",
    #     "skip_fields": {"id", "created_at", "updated_at"},
    # },
    # Event-related tables
    # "occurrences": {
    #     "endpoint": "/api/occurrences",
    #     "id_field": "id",
    #     "skip_fields": {"id", "created_at", "updated_at"},
    # },
    # "registrations": {
    #     "endpoint": "/api/registrations",
    #     "id_field": "id",
    #     "skip_fields": {"id", "created_at", "updated_at"},
    # },
    # "rsvps": {
    #     "endpoint": "/api/rsvps",
    #     "id_field": "id",
    #     "skip_fields": {"id", "created_at", "updated_at"},
    # },
    # Content-related tables
    "announcements": {
        "endpoint": "/api/announcements",
        "id_field": "id",
        "skip_fields": {"id", "created_at", "updated_at"},
    },
    "flyers": {
        "endpoint": "/api/flyers",
        "id_field": "id",
        "skip_fields": {"id", "created_at", "updated_at"},
    },
}

# Tables to load via API in dependency order
# These are the tables that have full CRUD support via REST API
TABLE_ORDER = [
    "metros",
    "contents",
    "tags",
    "orgs",
    "venues",
    "persons",
    "staff",
    "visitors",
    # Skipped until services router is fixed:
    # "services",
    # "activities",
    # "occurrences",
    # "registrations",
    # "rsvps",
    "announcements",
    "flyers",
]


def load_json_file(table_name: str) -> list[dict[str, Any]]:
    """Load JSON data from a dump file.
    
    Args:
        table_name: Name of the table (filename without .json).
        
    Returns:
        List of row dictionaries.
    """
    json_file = TEST_DUMP_DIR / f"{table_name}.json"
    if not json_file.exists():
        return []
    
    with open(json_file, "r") as f:
        data = json.load(f)
    
    return data


def prepare_create_payload(
    row: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    """Prepare a row for POST request by removing skip fields.
    
    Args:
        row: Original row data.
        config: Endpoint configuration.
        
    Returns:
        Cleaned payload for POST request.
    """
    skip_fields = config.get("skip_fields", {"id", "created_at", "updated_at"})
    
    payload = {}
    for key, value in row.items():
        if key in skip_fields:
            continue
        # Convert SQLite boolean integers to Python bools
        if isinstance(value, int) and key in {
            "login_enabled", "can_deliver_events", "can_host_events",
            "has_computers", "active",
        }:
            value = bool(value)
        payload[key] = value
    
    return payload


def compare_records(
    original: dict[str, Any],
    response: dict[str, Any],
    ignore_fields: set[str] | None = None,
) -> list[str]:
    """Compare original record with API response.
    
    Args:
        original: Original record from JSON file.
        response: Response from API.
        ignore_fields: Fields to ignore in comparison.
        
    Returns:
        List of difference descriptions.
    """
    if ignore_fields is None:
        ignore_fields = {"id", "created_at", "updated_at"}
    
    differences = []
    
    for key, orig_value in original.items():
        if key in ignore_fields:
            continue
        
        resp_value = response.get(key)
        
        # Normalize values for comparison
        if isinstance(orig_value, int) and key in {
            "login_enabled", "can_deliver_events", "can_host_events",
            "has_computers", "active",
        }:
            orig_value = bool(orig_value)
        
        # Handle None vs missing
        if orig_value is None and resp_value is None:
            continue
        
        if orig_value != resp_value:
            differences.append(f"  {key}: expected {orig_value!r}, got {resp_value!r}")
    
    return differences


class TestAPIRoundtrip:
    """Test API roundtrip through REST endpoints."""
    
    @pytest.fixture(autouse=True)
    def setup_test_database(self):
        """Set up test database for each test."""
        self.db_manager = TestDatabaseManager(in_memory=True)
        self.db_manager.setup()
        yield
        self.db_manager.teardown()
    
    @pytest.fixture
    def client(self):
        """Provide a test client that persists for the test."""
        with self.db_manager.get_test_client(app) as c:
            yield c
    
    def test_roundtrip_metros(self, client):
        """Test metros can be inserted and retrieved via API."""
        self._test_table_roundtrip(client, "metros")
    
    def test_roundtrip_contents(self, client):
        """Test contents can be inserted and retrieved via API."""
        self._test_table_roundtrip(client, "contents")
    
    def test_roundtrip_orgs(self, client):
        """Test orgs can be inserted and retrieved via API.
        
        Requires metros to be loaded first.
        """
        self._test_table_roundtrip(client, "metros")
        self._test_table_roundtrip(client, "orgs")
    
    def test_roundtrip_venues(self, client):
        """Test venues can be inserted and retrieved via API.
        
        Requires metros and orgs to be loaded first.
        """
        self._test_table_roundtrip(client, "metros")
        self._test_table_roundtrip(client, "orgs")
        self._test_table_roundtrip(client, "venues")
    
    def test_roundtrip_persons(self, client):
        """Test persons can be inserted and retrieved via API.
        
        Requires metros to be loaded first.
        """
        self._test_table_roundtrip(client, "metros")
        self._test_table_roundtrip(client, "persons")
    
    def test_full_roundtrip(self, client):
        """Test full data roundtrip through all supported API endpoints.
        
        This test:
        1. Loads all dump files in dependency order
        2. POSTs each record to the appropriate API endpoint
        3. GETs all records back from the API
        4. Validates the data matches the original files
        """
        if not TEST_DUMP_DIR.exists():
            pytest.skip(f"Test dump directory not found: {TEST_DUMP_DIR}")
        
        # Track results
        inserted_counts: dict[str, int] = {}
        retrieved_counts: dict[str, int] = {}
        errors: dict[str, list[str]] = defaultdict(list)
        
        print(f"\n{'=' * 70}")
        print("API Roundtrip Test")
        print(f"Source directory: {TEST_DUMP_DIR}")
        print(f"{'=' * 70}")
        
        # Phase 1: Insert all data via POST
        print("\n--- Phase 1: Inserting data via POST ---")
        for table_name in TABLE_ORDER:
            if table_name not in ENDPOINT_MAP:
                continue
            
            config = ENDPOINT_MAP[table_name]
            if config.get("read_only"):
                continue
            
            data = load_json_file(table_name)
            if not data:
                print(f"  {table_name}: no data file")
                continue
            
            endpoint = config["endpoint"]
            success_count = 0
            
            for i, row in enumerate(data):
                payload = prepare_create_payload(row, config)
                
                response = client.post(endpoint, json=payload)
                
                if response.status_code == 201:
                    success_count += 1
                else:
                    errors[table_name].append(
                        f"Row {i}: POST failed with {response.status_code}: {response.text[:200]}"
                    )
            
            inserted_counts[table_name] = success_count
            print(f"  {table_name}: inserted {success_count}/{len(data)} records")
        
        # Phase 2: Retrieve all data via GET
        print("\n--- Phase 2: Retrieving data via GET ---")
        for table_name in TABLE_ORDER:
            if table_name not in ENDPOINT_MAP:
                continue
            
            config = ENDPOINT_MAP[table_name]
            endpoint = config["endpoint"]
            
            # Use high limit to get all records
            response = client.get(f"{endpoint}?limit=1000")
            
            if response.status_code == 200:
                retrieved_data = response.json()
                retrieved_counts[table_name] = len(retrieved_data)
                print(f"  {table_name}: retrieved {len(retrieved_data)} records")
            else:
                errors[table_name].append(
                    f"GET failed with {response.status_code}: {response.text[:200]}"
                )
        
        # Phase 3: Validate data
        print("\n--- Phase 3: Validating data ---")
        validation_errors: dict[str, list[str]] = defaultdict(list)
        
        for table_name in TABLE_ORDER:
            if table_name not in ENDPOINT_MAP:
                continue
            
            config = ENDPOINT_MAP[table_name]
            if config.get("read_only"):
                continue
            
            original_data = load_json_file(table_name)
            if not original_data:
                continue
            
            endpoint = config["endpoint"]
            response = client.get(f"{endpoint}?limit=1000")
            
            if response.status_code != 200:
                continue
            
            retrieved_data = response.json()
            
            # Compare counts
            orig_count = len(original_data)
            retr_count = len(retrieved_data)
            
            if orig_count != retr_count:
                validation_errors[table_name].append(
                    f"Count mismatch: original={orig_count}, retrieved={retr_count}"
                )
            
            # Build lookup by ID for comparison (if IDs are sequential)
            # For this test, we compare by position since IDs may differ
            for i, (orig, retr) in enumerate(zip(original_data, retrieved_data)):
                diffs = compare_records(orig, retr)
                if diffs:
                    validation_errors[table_name].append(
                        f"Record {i} differences:\n" + "\n".join(diffs)
                    )
            
            if table_name not in validation_errors:
                print(f"  {table_name}: ✓ validated")
            else:
                print(f"  {table_name}: ✗ {len(validation_errors[table_name])} errors")
        
        # Summary
        print(f"\n{'=' * 70}")
        print("Summary")
        print(f"{'=' * 70}")
        
        total_inserted = sum(inserted_counts.values())
        total_retrieved = sum(retrieved_counts.values())
        print(f"Total inserted: {total_inserted}")
        print(f"Total retrieved: {total_retrieved}")
        
        # Report errors
        all_errors = {**errors, **validation_errors}
        if all_errors:
            print("\nErrors:")
            for table_name, table_errors in all_errors.items():
                print(f"\n  {table_name}:")
                for err in table_errors[:5]:  # Limit to first 5 errors per table
                    print(f"    - {err}")
                if len(table_errors) > 5:
                    print(f"    ... and {len(table_errors) - 5} more errors")
            
            pytest.fail(f"Roundtrip test failed with errors in: {list(all_errors.keys())}")
        
        print("\n✓ Full API roundtrip test PASSED")
    
    def _test_table_roundtrip(self, client: TestClient, table_name: str):
        """Test roundtrip for a single table.
        
        Args:
            client: Test client to use.
            table_name: Name of the table to test.
        """
        if table_name not in ENDPOINT_MAP:
            pytest.skip(f"No endpoint mapping for {table_name}")
        
        config = ENDPOINT_MAP[table_name]
        if config.get("read_only"):
            pytest.skip(f"{table_name} is read-only")
        
        data = load_json_file(table_name)
        if not data:
            pytest.skip(f"No dump file for {table_name}")
        
        endpoint = config["endpoint"]
        
        # Insert all records
        inserted_ids = []
        for row in data:
            payload = prepare_create_payload(row, config)
            response = client.post(endpoint, json=payload)
            
            assert response.status_code == 201, (
                f"POST {endpoint} failed: {response.status_code} - {response.text}"
            )
            inserted_ids.append(response.json()["id"])
        
        # Retrieve all records
        response = client.get(f"{endpoint}?limit=1000")
        assert response.status_code == 200
        
        retrieved_data = response.json()
        
        # Validate count
        assert len(retrieved_data) == len(data), (
            f"Count mismatch: expected {len(data)}, got {len(retrieved_data)}"
        )
        
        # Validate content
        for i, (orig, retr) in enumerate(zip(data, retrieved_data)):
            diffs = compare_records(orig, retr)
            assert not diffs, f"Record {i} has differences:\n" + "\n".join(diffs)


class TestAPIRoundtripWithDependencies:
    """Test API roundtrip with complex dependencies."""
    
    @pytest.fixture(autouse=True)
    def setup_test_database(self):
        """Set up test database for each test."""
        self.db_manager = TestDatabaseManager(in_memory=True)
        self.db_manager.setup()
        yield
        self.db_manager.teardown()
    
    @pytest.fixture
    def client(self):
        """Provide a test client that persists for the test."""
        with self.db_manager.get_test_client(app) as c:
            yield c
    
    def test_place_hierarchy(self, client):
        """Test inserting and retrieving a full place hierarchy.
        
        Metro -> Org -> Venue
        """
        # Create metro
        metro_data = load_json_file("metros")
        if not metro_data:
            pytest.skip("No metros dump file")
        
        metro_payload = prepare_create_payload(metro_data[0], ENDPOINT_MAP["metros"])
        response = client.post("/api/metros", json=metro_payload)
        assert response.status_code == 201
        metro_id = response.json()["id"]
        
        # Create org linked to metro
        org_data = load_json_file("orgs")
        if org_data:
            org_payload = prepare_create_payload(org_data[0], ENDPOINT_MAP["orgs"])
            org_payload["metro_id"] = metro_id
            response = client.post("/api/orgs", json=org_payload)
            assert response.status_code == 201
            org_id = response.json()["id"]
            
            # Verify org has correct metro_id
            response = client.get(f"/api/orgs/{org_id}")
            assert response.status_code == 200
            assert response.json()["metro_id"] == metro_id
            
            # Create venue linked to metro and org
            venue_data = load_json_file("venues")
            if venue_data:
                venue_payload = prepare_create_payload(venue_data[0], ENDPOINT_MAP["venues"])
                venue_payload["metro_id"] = metro_id
                venue_payload["org_id"] = org_id
                response = client.post("/api/venues", json=venue_payload)
                assert response.status_code == 201
                venue_id = response.json()["id"]
                
                # Verify venue relationships
                response = client.get(f"/api/venues/{venue_id}")
                assert response.status_code == 200
                venue = response.json()
                assert venue["metro_id"] == metro_id
                assert venue["org_id"] == org_id
    
    def test_person_to_staff(self, client):
        """Test inserting and retrieving person with staff record.
        
        Metro -> Person -> Staff
        """
        # Create metro (required by person)
        metro_data = load_json_file("metros")
        if not metro_data:
            pytest.skip("No metros dump file")
        
        metro_payload = prepare_create_payload(metro_data[0], ENDPOINT_MAP["metros"])
        response = client.post("/api/metros", json=metro_payload)
        assert response.status_code == 201
        metro_id = response.json()["id"]
        
        # Create person
        person_data = load_json_file("persons")
        if not person_data:
            pytest.skip("No persons dump file")
        
        person_payload = prepare_create_payload(person_data[0], ENDPOINT_MAP["persons"])
        person_payload["metro_id"] = metro_id
        response = client.post("/api/persons", json=person_payload)
        assert response.status_code == 201
        person_id = response.json()["id"]
        
        # Create staff for person
        staff_data = load_json_file("staff")
        if staff_data:
            staff_payload = prepare_create_payload(staff_data[0], ENDPOINT_MAP["staff"])
            staff_payload["person_id"] = person_id
            response = client.post("/api/staff", json=staff_payload)
            assert response.status_code == 201
            staff_id = response.json()["id"]
            
            # Verify staff linked to person
            response = client.get(f"/api/staff/{staff_id}")
            assert response.status_code == 200
            assert response.json()["person_id"] == person_id
