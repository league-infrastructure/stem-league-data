#!/usr/bin/env python3
"""Dump the test database to JSON files.

This script loads data from external sources (Pike13, Meetups, content.json)
into a SQLite database, then dumps each table to a JSON file in the output
directory.

Usage:
    python -m tests.bin.dump_db_to_json [--output-dir DIR]
    
Options:
    --output-dir DIR    Output directory for JSON files (default: tests/dump)
"""

import argparse
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.lib.workspace import find_workspace_root, get_test_dump_dir
from tests.lib.database import (
    create_sqlite_engine,
    create_session,
    dump_database_to_json,
)


def main():
    parser = argparse.ArgumentParser(
        description="Dump test database to JSON files"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory for JSON files (default: tests/dump)",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=None,
        help="Path to database file (default: tests/data/test.db)",
    )
    args = parser.parse_args()
    
    # Find workspace root
    workspace_root = find_workspace_root(__file__)
    
    # Set output directory
    if args.output_dir is None:
        output_dir = get_test_dump_dir(__file__)
    else:
        output_dir = args.output_dir
    
    # Set database path
    if args.db_path is None:
        db_path = workspace_root / "tests" / "data" / "test.db"
    else:
        db_path = args.db_path
    
    if not db_path.exists():
        print(f"Error: Database file not found: {db_path}")
        print("\nYou need to run test_ext_data_load.py first to create the database:")
        print("  uv run pytest tests/bin/test_ext_data_load.py -v")
        sys.exit(1)
    
    print(f"Dumping database: {db_path}")
    print(f"Output directory: {output_dir}")
    
    # Create engine and session
    engine = create_sqlite_engine(db_path)
    session = create_session(engine)
    
    try:
        # Dump all tables
        counts = dump_database_to_json(session, output_dir)
        
        print(f"\nDumped {len(counts)} tables:")
        for table_name, count in sorted(counts.items()):
            print(f"  {table_name}: {count} rows")
        
        print(f"\nJSON files written to: {output_dir}")
        
    finally:
        session.close()


if __name__ == "__main__":
    main()
