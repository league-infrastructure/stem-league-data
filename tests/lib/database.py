"""Database utilities for tests.

Provides functions to create test databases, dump to JSON, and load from JSON.
"""

import json
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, event, inspect, MetaData, text
from sqlalchemy.orm import sessionmaker, Session


def create_sqlite_engine(db_path: Path | str, echo: bool = False):
    """Create a SQLite engine with foreign key support.
    
    Args:
        db_path: Path to the database file. Use ":memory:" for in-memory.
        echo: Whether to echo SQL statements.
        
    Returns:
        SQLAlchemy engine.
    """
    if db_path == ":memory:":
        engine = create_engine("sqlite:///:memory:", echo=echo)
    else:
        engine = create_engine(f"sqlite:///{db_path}", echo=echo)
    
    # Enable foreign keys in SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    return engine


def create_session(engine) -> Session:
    """Create a database session.
    
    Args:
        engine: SQLAlchemy engine.
        
    Returns:
        SQLAlchemy session.
    """
    Session = sessionmaker(bind=engine)
    return Session()


class JSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for database values."""
    
    def default(self, obj):
        if isinstance(obj, datetime):
            return {"__type__": "datetime", "value": obj.isoformat()}
        if isinstance(obj, date):
            return {"__type__": "date", "value": obj.isoformat()}
        if isinstance(obj, Decimal):
            return {"__type__": "decimal", "value": str(obj)}
        if isinstance(obj, bytes):
            return {"__type__": "bytes", "value": obj.hex()}
        return super().default(obj)


def json_decoder_hook(obj: dict) -> Any:
    """Custom JSON decoder hook for database values."""
    if "__type__" in obj:
        type_name = obj["__type__"]
        value = obj["value"]
        if type_name == "datetime":
            return datetime.fromisoformat(value)
        if type_name == "date":
            return date.fromisoformat(value)
        if type_name == "decimal":
            return Decimal(value)
        if type_name == "bytes":
            return bytes.fromhex(value)
    return obj


def dump_table_to_json(session: Session, table_name: str) -> list[dict]:
    """Dump a table to a list of dictionaries.
    
    Args:
        session: SQLAlchemy session.
        table_name: Name of the table to dump.
        
    Returns:
        List of row dictionaries.
    """
    # Quote table name to handle reserved words
    result = session.execute(text(f'SELECT * FROM "{table_name}"'))
    columns = result.keys()
    rows = []
    for row in result:
        row_dict = {}
        for i, col in enumerate(columns):
            value = row[i]
            # Convert any non-JSON-serializable types
            if isinstance(value, (datetime, date, Decimal, bytes)):
                pass  # JSONEncoder will handle these
            row_dict[col] = value
        rows.append(row_dict)
    return rows


def dump_database_to_json(
    session: Session,
    output_dir: Path,
    tables: list[str] | None = None,
) -> dict[str, int]:
    """Dump all tables in a database to JSON files.
    
    Args:
        session: SQLAlchemy session.
        output_dir: Directory to write JSON files.
        tables: List of table names to dump. If None, dumps all tables.
        
    Returns:
        Dictionary mapping table names to row counts.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get list of tables
    if tables is None:
        result = session.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        )
        tables = [row[0] for row in result]
    
    counts = {}
    for table_name in tables:
        rows = dump_table_to_json(session, table_name)
        counts[table_name] = len(rows)
        
        output_file = output_dir / f"{table_name}.json"
        with open(output_file, "w") as f:
            json.dump(rows, f, indent=2, cls=JSONEncoder)
    
    return counts


def load_json_to_table(
    session: Session,
    table_name: str,
    data: list[dict],
) -> int:
    """Load JSON data into a table.
    
    Args:
        session: SQLAlchemy session.
        table_name: Name of the table to load into.
        data: List of row dictionaries.
        
    Returns:
        Number of rows loaded.
    """
    if not data:
        return 0
    
    for row in data:
        columns = list(row.keys())
        # Quote column names to handle reserved words like 'group'
        quoted_columns = [f'"{col}"' for col in columns]
        placeholders = ", ".join([f":{col}" for col in columns])
        column_names = ", ".join(quoted_columns)
        
        sql = f'INSERT INTO "{table_name}" ({column_names}) VALUES ({placeholders})'
        session.execute(text(sql), row)
    
    return len(data)


def load_database_from_json(
    session: Session,
    input_dir: Path,
    table_order: list[str] | None = None,
) -> dict[str, int]:
    """Load all JSON files from a directory into database tables.
    
    Args:
        session: SQLAlchemy session.
        input_dir: Directory containing JSON files.
        table_order: Order to load tables (for foreign key constraints).
                    If None, loads in alphabetical order.
        
    Returns:
        Dictionary mapping table names to row counts.
    """
    input_dir = Path(input_dir)
    
    # Find all JSON files
    json_files = list(input_dir.glob("*.json"))
    
    if table_order is not None:
        # Load in specified order
        ordered_files = []
        for table in table_order:
            file_path = input_dir / f"{table}.json"
            if file_path.exists():
                ordered_files.append(file_path)
        # Add any remaining files not in the order
        remaining = [f for f in json_files if f not in ordered_files]
        json_files = ordered_files + remaining
    else:
        json_files = sorted(json_files)
    
    counts = {}
    for json_file in json_files:
        table_name = json_file.stem
        
        with open(json_file) as f:
            data = json.load(f, object_hook=json_decoder_hook)
        
        count = load_json_to_table(session, table_name, data)
        counts[table_name] = count
    
    return counts


def compare_databases(
    session1: Session,
    session2: Session,
    tables: list[str] | None = None,
) -> dict[str, Any]:
    """Compare two databases and return differences.
    
    Args:
        session1: First database session.
        session2: Second database session.
        tables: List of tables to compare. If None, compares all tables.
        
    Returns:
        Dictionary with comparison results:
        - "identical": bool - True if databases are identical
        - "tables_only_in_1": list - Tables only in first database
        - "tables_only_in_2": list - Tables only in second database
        - "table_diffs": dict - Per-table differences
    """
    # Get tables from both databases
    result1 = session1.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    )
    tables1 = set(row[0] for row in result1)
    
    result2 = session2.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    )
    tables2 = set(row[0] for row in result2)
    
    if tables is not None:
        tables1 = tables1 & set(tables)
        tables2 = tables2 & set(tables)
    
    report = {
        "identical": True,
        "tables_only_in_1": sorted(tables1 - tables2),
        "tables_only_in_2": sorted(tables2 - tables1),
        "table_diffs": {},
    }
    
    if report["tables_only_in_1"] or report["tables_only_in_2"]:
        report["identical"] = False
    
    # Compare common tables
    common_tables = tables1 & tables2
    for table_name in sorted(common_tables):
        diff = compare_tables(session1, session2, table_name)
        if diff["has_differences"]:
            report["identical"] = False
            report["table_diffs"][table_name] = diff
    
    return report


def compare_tables(
    session1: Session,
    session2: Session,
    table_name: str,
) -> dict[str, Any]:
    """Compare a single table between two databases.
    
    Args:
        session1: First database session.
        session2: Second database session.
        table_name: Name of table to compare.
        
    Returns:
        Dictionary with comparison results.
    """
    rows1 = dump_table_to_json(session1, table_name)
    rows2 = dump_table_to_json(session2, table_name)
    
    diff = {
        "has_differences": False,
        "row_count_1": len(rows1),
        "row_count_2": len(rows2),
        "rows_only_in_1": [],
        "rows_only_in_2": [],
        "row_differences": [],
    }
    
    # Convert to comparable format (use JSON for consistent comparison)
    def row_key(row: dict) -> str:
        return json.dumps(row, sort_keys=True, cls=JSONEncoder)
    
    set1 = {row_key(r): r for r in rows1}
    set2 = {row_key(r): r for r in rows2}
    
    keys1 = set(set1.keys())
    keys2 = set(set2.keys())
    
    only_in_1 = keys1 - keys2
    only_in_2 = keys2 - keys1
    
    if only_in_1:
        diff["has_differences"] = True
        diff["rows_only_in_1"] = [set1[k] for k in sorted(only_in_1)]
    
    if only_in_2:
        diff["has_differences"] = True
        diff["rows_only_in_2"] = [set2[k] for k in sorted(only_in_2)]
    
    return diff


def format_comparison_report(report: dict[str, Any]) -> str:
    """Format a comparison report as human-readable text.
    
    Args:
        report: Comparison report from compare_databases.
        
    Returns:
        Formatted report string.
    """
    lines = []
    lines.append("=" * 70)
    lines.append("DATABASE COMPARISON REPORT")
    lines.append("=" * 70)
    
    if report["identical"]:
        lines.append("\n✓ Databases are IDENTICAL\n")
        return "\n".join(lines)
    
    lines.append("\n✗ Databases have DIFFERENCES\n")
    
    if report["tables_only_in_1"]:
        lines.append("Tables only in database 1:")
        for t in report["tables_only_in_1"]:
            lines.append(f"  - {t}")
        lines.append("")
    
    if report["tables_only_in_2"]:
        lines.append("Tables only in database 2:")
        for t in report["tables_only_in_2"]:
            lines.append(f"  - {t}")
        lines.append("")
    
    for table_name, diff in report["table_diffs"].items():
        lines.append("-" * 70)
        lines.append(f"Table: {table_name}")
        lines.append(f"  Row count in DB1: {diff['row_count_1']}")
        lines.append(f"  Row count in DB2: {diff['row_count_2']}")
        
        if diff["rows_only_in_1"]:
            lines.append(f"\n  Rows only in DB1 ({len(diff['rows_only_in_1'])}):")
            for row in diff["rows_only_in_1"][:10]:  # Limit output
                lines.append(f"    {json.dumps(row, cls=JSONEncoder)}")
            if len(diff["rows_only_in_1"]) > 10:
                lines.append(f"    ... and {len(diff['rows_only_in_1']) - 10} more")
        
        if diff["rows_only_in_2"]:
            lines.append(f"\n  Rows only in DB2 ({len(diff['rows_only_in_2'])}):")
            for row in diff["rows_only_in_2"][:10]:  # Limit output
                lines.append(f"    {json.dumps(row, cls=JSONEncoder)}")
            if len(diff["rows_only_in_2"]) > 10:
                lines.append(f"    ... and {len(diff['rows_only_in_2']) - 10} more")
        
        lines.append("")
    
    lines.append("=" * 70)
    return "\n".join(lines)
