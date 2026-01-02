"""System test for database roundtrip: dump to JSON and reload.

This test verifies that:
1. Load data from dump files into a SQLite database (DB1)
2. Dump DB1 to JSON in a temporary directory
3. Load the temporary JSON into a new database (DB2)
4. Compare DB1 and DB2 to ensure they are identical

This validates the JSON serialization/deserialization roundtrip.

Note: This test patches PostgreSQL-specific types to work with SQLite.
"""

import sys
import tempfile
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
from stem_league_data.models import Base

from tests.lib.workspace import find_workspace_root, get_test_dump_dir
from tests.lib.database import (
    create_sqlite_engine,
    create_session,
    dump_database_to_json,
    load_database_from_json,
    compare_databases,
    format_comparison_report,
)


# Find paths
WORKSPACE_ROOT = find_workspace_root(__file__)
TEST_DUMP_DIR = get_test_dump_dir(__file__)

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
    "groups",
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


class TestDatabaseRoundtrip:
    """Test database roundtrip through JSON serialization."""
    
    def test_roundtrip_preserves_data(self):
        """Test that dump->load->dump->load produces identical databases."""
        # Check if dump files exist
        if not TEST_DUMP_DIR.exists() or not list(TEST_DUMP_DIR.glob("*.json")):
            pytest.skip(
                f"Dump files not found in {TEST_DUMP_DIR}. "
                "Run dump_db_to_json.py first."
            )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            db1_path = temp_path / "db1.sqlite"
            db2_path = temp_path / "db2.sqlite"
            json_dump_dir = temp_path / "json_dump"
            
            # Print paths for debugging
            print(f"\n{'=' * 70}")
            print(f"Source dump dir: {TEST_DUMP_DIR}")
            print(f"Temp directory:  {temp_path}")
            print(f"DB1 path:        {db1_path}")
            print(f"DB2 path:        {db2_path}")
            print(f"JSON dump dir:   {json_dump_dir}")
            print(f"{'=' * 70}")
            
            # Step 1: Load original dump into DB1
            print("\nStep 1: Loading original dump files into DB1...")
            engine1 = create_sqlite_engine(db1_path)
            engine1 = create_sqlite_engine(db1_path)
            Base.metadata.create_all(engine1)
            session1 = create_session(engine1)
            
            counts1 = load_database_from_json(
                session1,
                TEST_DUMP_DIR,
                table_order=TABLE_ORDER,
            )
            session1.commit()
            
            print(f"  Loaded {sum(counts1.values())} total rows into DB1")
            
            # Step 2: Dump DB1 to JSON in temp directory
            print("\nStep 2: Dumping DB1 to JSON...")
            counts_dump = dump_database_to_json(session1, json_dump_dir)
            print(f"  Dumped {sum(counts_dump.values())} total rows to JSON")
            
            # Step 3: Load JSON dump into DB2
            print("\nStep 3: Loading JSON dump into DB2...")
            engine2 = create_sqlite_engine(db2_path)
            Base.metadata.create_all(engine2)
            session2 = create_session(engine2)
            
            counts2 = load_database_from_json(
                session2,
                json_dump_dir,
                table_order=TABLE_ORDER,
            )
            session2.commit()
            
            print(f"  Loaded {sum(counts2.values())} total rows into DB2")
            
            # Step 4: Compare DB1 and DB2
            print("\nStep 4: Comparing databases...")
            report = compare_databases(session1, session2)
            
            # Print report
            print("\n" + format_comparison_report(report))
            
            # Clean up sessions
            session1.close()
            session2.close()
            
            # Assert databases are identical
            if not report["identical"]:
                # Provide detailed failure information
                error_lines = ["Databases are not identical!\n"]
                
                if report["tables_only_in_1"]:
                    error_lines.append(f"Tables only in DB1: {report['tables_only_in_1']}")
                
                if report["tables_only_in_2"]:
                    error_lines.append(f"Tables only in DB2: {report['tables_only_in_2']}")
                
                for table, diff in report["table_diffs"].items():
                    error_lines.append(f"\nTable '{table}' differences:")
                    error_lines.append(f"  Rows in DB1: {diff['row_count_1']}")
                    error_lines.append(f"  Rows in DB2: {diff['row_count_2']}")
                    
                    if diff["rows_only_in_1"]:
                        error_lines.append(f"  Rows only in DB1: {len(diff['rows_only_in_1'])}")
                        for row in diff["rows_only_in_1"][:3]:
                            error_lines.append(f"    {row}")
                    
                    if diff["rows_only_in_2"]:
                        error_lines.append(f"  Rows only in DB2: {len(diff['rows_only_in_2'])}")
                        for row in diff["rows_only_in_2"][:3]:
                            error_lines.append(f"    {row}")
                
                pytest.fail("\n".join(error_lines))
            
            print("\n✓ Roundtrip test PASSED - databases are identical")
    
    def test_row_counts_match(self):
        """Test that row counts match between original and roundtrip."""
        if not TEST_DUMP_DIR.exists() or not list(TEST_DUMP_DIR.glob("*.json")):
            pytest.skip(
                f"Dump files not found in {TEST_DUMP_DIR}. "
                "Run dump_db_to_json.py first."
            )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            db_path = temp_path / "test.sqlite"
            json_dump_dir = temp_path / "json_dump"
            
            # Load original dump
            engine = create_sqlite_engine(db_path)
            Base.metadata.create_all(engine)
            session = create_session(engine)
            
            original_counts = load_database_from_json(
                session,
                TEST_DUMP_DIR,
                table_order=TABLE_ORDER,
            )
            session.commit()
            
            # Dump to JSON
            dump_counts = dump_database_to_json(session, json_dump_dir)
            
            session.close()
            
            # Verify counts match
            print("\nRow count comparison:")
            mismatches = []
            for table in sorted(set(original_counts.keys()) | set(dump_counts.keys())):
                orig = original_counts.get(table, 0)
                dump = dump_counts.get(table, 0)
                status = "✓" if orig == dump else "✗"
                print(f"  {status} {table}: loaded={orig}, dumped={dump}")
                if orig != dump:
                    mismatches.append((table, orig, dump))
            
            assert not mismatches, f"Row count mismatches: {mismatches}"


def _perform_roundtrip(
    temp_path: Path,
    delete_table: str | None = None,
    delete_first_row_from: str | None = None,
) -> tuple[dict, dict, dict]:
    """
    Perform a database roundtrip with optional mutations for testing comparison logic.
    
    Args:
        temp_path: Temporary directory path for databases
        delete_table: If provided, delete all rows from this table in DB2 before comparison
        delete_first_row_from: If provided, delete the first row from this table in DB2
    
    Returns:
        Tuple of (comparison_report, db1_counts, db2_counts)
    """
    db1_path = temp_path / "original.sqlite"
    db2_path = temp_path / "roundtrip.sqlite"
    json_dump_dir = temp_path / "json_dump"
    
    # Load dump files into DB1
    engine1 = create_sqlite_engine(db1_path)
    Base.metadata.create_all(engine1)
    session1 = create_session(engine1)
    
    db1_counts = load_database_from_json(
        session1,
        TEST_DUMP_DIR,
        table_order=TABLE_ORDER,
    )
    session1.commit()
    
    # Dump DB1 to JSON
    dump_database_to_json(session1, json_dump_dir)
    
    # Load JSON into DB2
    engine2 = create_sqlite_engine(db2_path)
    Base.metadata.create_all(engine2)
    session2 = create_session(engine2)
    
    db2_counts = load_database_from_json(
        session2,
        json_dump_dir,
        table_order=TABLE_ORDER,
    )
    session2.commit()
    
    # Apply mutations if requested
    if delete_table:
        result = session2.execute(text(f'DELETE FROM "{delete_table}"'))
        deleted_count = result.rowcount
        session2.commit()
        print(f"  Deleted all {deleted_count} rows from table '{delete_table}' in DB2")
    
    if delete_first_row_from:
        # Get the first row's primary key and delete it
        result = session2.execute(text(f'SELECT rowid FROM "{delete_first_row_from}" LIMIT 1'))
        row = result.fetchone()
        if row:
            session2.execute(text(f'DELETE FROM "{delete_first_row_from}" WHERE rowid = {row[0]}'))
            session2.commit()
            print(f"  Deleted first row from table '{delete_first_row_from}' in DB2")
    
    # Compare databases (sessions must still be open)
    comparison = compare_databases(session1, session2)
    
    # Now we can close the sessions
    session1.close()
    session2.close()
    
    return comparison, db1_counts, db2_counts


class TestComparisonDetectsDifferences:
    """Tests that verify the comparison logic correctly detects differences."""
    
    def test_detects_deleted_table_contents(self):
        """Test that comparison detects when all rows are deleted from a table."""
        if not TEST_DUMP_DIR.exists() or not list(TEST_DUMP_DIR.glob("*.json")):
            pytest.skip(
                f"Dump files not found in {TEST_DUMP_DIR}. "
                "Run dump_db_to_json.py first."
            )
        
        # Find a table with data to delete
        table_to_delete = "persons"  # Person should always have data
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            print(f"\nTesting deletion detection for table: {table_to_delete}")
            
            comparison, db1_counts, db2_counts = _perform_roundtrip(
                temp_path,
                delete_table=table_to_delete,
            )
            
            # The comparison should show differences
            assert not comparison["identical"], "Comparison should detect differences when table contents are deleted"
            
            # Check that the deleted table has differences
            table_diffs = comparison.get("table_diffs", {})
            table_diff = table_diffs.get(table_to_delete, {})
            rows_missing = len(table_diff.get("rows_only_in_1", []))
            
            print(f"  Comparison found {rows_missing} rows missing from '{table_to_delete}' in DB2")
            
            assert rows_missing > 0, f"Should find rows missing from '{table_to_delete}'"
            
            # Verify the report would show the problem
            report = format_comparison_report(comparison)
            assert table_to_delete in report, f"Report should mention table '{table_to_delete}'"
            
            print(f"  ✓ Comparison correctly detected deletion of {rows_missing} rows")
    
    def test_detects_deleted_row(self):
        """Test that comparison detects when a single row is deleted from a table."""
        if not TEST_DUMP_DIR.exists() or not list(TEST_DUMP_DIR.glob("*.json")):
            pytest.skip(
                f"Dump files not found in {TEST_DUMP_DIR}. "
                "Run dump_db_to_json.py first."
            )
        
        # Find a table with data to delete a row from
        table_with_row = "persons"
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            print(f"\nTesting single row deletion detection for table: {table_with_row}")
            
            comparison, db1_counts, db2_counts = _perform_roundtrip(
                temp_path,
                delete_first_row_from=table_with_row,
            )
            
            # The comparison should show differences
            assert not comparison["identical"], "Comparison should detect differences when a row is deleted"
            
            # Check that the modified table has exactly 1 row difference
            table_diffs = comparison.get("table_diffs", {})
            table_diff = table_diffs.get(table_with_row, {})
            rows_missing = len(table_diff.get("rows_only_in_1", []))
            
            print(f"  Comparison found {rows_missing} row(s) missing from '{table_with_row}' in DB2")
            
            assert rows_missing == 1, f"Should find exactly 1 row missing from '{table_with_row}'"
            
            # Verify the report would show the problem
            report = format_comparison_report(comparison)
            assert table_with_row in report, f"Report should mention table '{table_with_row}'"
            
            print(f"  ✓ Comparison correctly detected deletion of 1 row")
    
    def test_identical_databases_pass(self):
        """Test that identical databases show no differences (sanity check)."""
        if not TEST_DUMP_DIR.exists() or not list(TEST_DUMP_DIR.glob("*.json")):
            pytest.skip(
                f"Dump files not found in {TEST_DUMP_DIR}. "
                "Run dump_db_to_json.py first."
            )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            print("\nTesting that identical databases show no differences")
            
            comparison, _, _ = _perform_roundtrip(temp_path)
            
            assert comparison["identical"], "Identical databases should show no differences"
            
            print("  ✓ Identical databases correctly show no differences")
