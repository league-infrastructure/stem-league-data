"""Router for Admin operations: data loading, database management, backups."""

import json
import os
import shutil
import subprocess
import sqlite3
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy import inspect, text, event
from sqlalchemy.orm import Session
from sqlalchemy.dialects.sqlite import base as sqlite_dialect

from stem_league_data.database import get_db, create_tables, drop_tables, engine, SessionLocal, DATABASE_URL
from stem_league_data.config import get_backup_dir, get_root_dir, get_sqlite_database_path, get_dump_dir
from stem_league_data.models import (
    Metro, Org, Venue, Flyer,
    Person, Staff, Visitor,
    Content, Announcement,
    Group, Program, Track, Category, SubCategory, Topic, Tag,
    Service, Activity, Occurrence, Registration, RSVP,
    JobPosting, InstructorAssignment, InstructorEvaluation,
    Meetup, Pike13Service, P13Location,
)

router = APIRouter()

# Model loading order (respects foreign key dependencies)
LOAD_ORDER = [
    ("metros.json", Metro),
    ("orgs.json", Org),
    ("venues.json", Venue),
    ("flyers.json", Flyer),
    ("persons.json", Person),
    ("staff.json", Staff),
    ("visitors.json", Visitor),
    ("contents.json", Content),
    ("announcements.json", Announcement),
    ("groups.json", Group),
    ("tags.json", Tag),
    ("services.json", Service),
    ("activities.json", Activity),
    ("occurrences.json", Occurrence),
    ("registrations.json", Registration),
    ("rsvps.json", RSVP),
    ("job_postings.json", JobPosting),
    ("instructor_assignments.json", InstructorAssignment),
    ("instructor_evaluations.json", InstructorEvaluation),
    ("meetups.json", Meetup),
    ("pike13_services.json", Pike13Service),
    ("p13_locations.json", P13Location),
]


def load_json_file(filepath: Path) -> list[dict[str, Any]]:
    """Load and parse a JSON file."""
    if not filepath.exists():
        return []
    with open(filepath) as f:
        return json.load(f)


# Mapping of JSON column names to Python attribute names for reserved keywords
COLUMN_NAME_MAPPING = {
    "for": "for_",  # Content.for_ column is named "for" in DB
    "from": "from_date",  # Announcement.from_date column is named "from" in DB
}


def parse_datetime(value: str | None) -> datetime | None:
    """Parse a datetime string into a datetime object."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    # Try common datetime formats
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    # Try ISO format as fallback
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def clean_model_data(data: dict[str, Any], model_class: type) -> dict[str, Any]:
    """Clean data to match model columns, removing unknown fields and parsing datetimes."""
    from sqlalchemy.dialects.postgresql import ARRAY
    
    # Get the column info from the model
    mapper = inspect(model_class)
    
    # Build a mapping of column names to attribute names and their types
    column_to_attr: dict[str, str] = {}
    datetime_attrs: set[str] = set()
    array_attrs: set[str] = set()
    
    for attr in mapper.attrs:
        if hasattr(attr, "columns"):
            for col in attr.columns:
                column_to_attr[col.name] = attr.key
                # Check if this is a datetime column
                if hasattr(col.type, "python_type"):
                    try:
                        if col.type.python_type is datetime:
                            datetime_attrs.add(attr.key)
                    except NotImplementedError:
                        pass
                # Check if this is an ARRAY column
                if isinstance(col.type, ARRAY):
                    array_attrs.add(attr.key)
    
    result = {}
    for key, value in data.items():
        # Map column name to attribute name (handles reserved words like 'for' -> 'for_')
        attr_name = column_to_attr.get(key, key)
        
        # Skip if this attribute doesn't exist on the model
        if attr_name not in column_to_attr.values() and key not in column_to_attr:
            continue
        
        # Parse datetime strings
        if attr_name in datetime_attrs and isinstance(value, str):
            value = parse_datetime(value)
        
        # Handle "null" string in ARRAY fields (JSON dump artifact)
        if attr_name in array_attrs and value == "null":
            value = None
        
        result[attr_name] = value
    
    return result


@router.post("/admin/reset-database", tags=["admin"])
def reset_database(db: Session = Depends(get_db)) -> dict[str, str]:
    """
    Drop all tables and recreate them.
    WARNING: This will delete all data!
    """
    drop_tables()
    create_tables()
    return {"status": "success", "message": "Database reset complete"}


@router.post("/admin/load-data", tags=["admin"])
def load_data(
    dump_dir: str | None = None,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Load data from JSON dump files into the database.
    
    Args:
        dump_dir: Optional path to directory containing JSON dump files.
                  Defaults to tests/dump (resolved relative to ROOT_DIR).
    
    Returns:
        Summary of loaded records per model.
    """
    data_dir = get_dump_dir(dump_dir)
    
    if not data_dir.exists():
        raise HTTPException(status_code=400, detail=f"Dump directory not found: {data_dir}")
    
    results = {}
    errors = []
    
    for filename, model_class in LOAD_ORDER:
        filepath = data_dir / filename
        
        if not filepath.exists():
            results[filename] = {"skipped": True, "reason": "file not found"}
            continue
        
        try:
            records = load_json_file(filepath)
            count = 0
            
            for record in records:
                # Clean the record to only include known columns
                cleaned_data = clean_model_data(record, model_class)
                
                # Create model instance
                instance = model_class(**cleaned_data)
                db.add(instance)
                count += 1
            
            db.commit()
            results[filename] = {"loaded": count}
            
        except Exception as e:
            db.rollback()
            error_msg = f"Error loading {filename}: {str(e)}"
            errors.append(error_msg)
            results[filename] = {"error": str(e)}
    
    return {
        "status": "success" if not errors else "partial",
        "results": results,
        "errors": errors,
    }


@router.get("/admin/stats", tags=["admin"])
def get_database_stats(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Get counts of all records in the database."""
    from sqlalchemy import func
    
    stats = {}
    models = [
        ("metros", Metro),
        ("orgs", Org),
        ("venues", Venue),
        ("flyers", Flyer),
        ("persons", Person),
        ("staff", Staff),
        ("visitors", Visitor),
        ("contents", Content),
        ("announcements", Announcement),
        ("groups", Group),
        ("tags", Tag),
        ("services", Service),
        ("activities", Activity),
        ("occurrences", Occurrence),
        ("registrations", Registration),
        ("rsvps", RSVP),
        ("job_postings", JobPosting),
        ("instructor_assignments", InstructorAssignment),
        ("instructor_evaluations", InstructorEvaluation),
        ("meetups", Meetup),
        ("pike13_services", Pike13Service),
        ("p13_locations", P13Location),
    ]
    
    for name, model in models:
        count = db.query(func.count(model.id)).scalar()
        stats[name] = count
    
    stats["total"] = sum(stats.values())
    return stats


@router.delete("/admin/clear-data", tags=["admin"])
def clear_all_data(db: Session = Depends(get_db)) -> dict[str, str]:
    """
    Delete all data from all tables (but keep tables intact).
    WARNING: This will delete all data!
    """
    # Delete in reverse order to respect foreign keys
    for filename, model_class in reversed(LOAD_ORDER):
        db.query(model_class).delete()
    
    db.commit()
    return {"status": "success", "message": "All data cleared"}


@router.post("/admin/load-file/{filename}", tags=["admin"])
def load_single_file(
    filename: str,
    dump_dir: str | None = None,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Load data from a single JSON dump file.
    
    Args:
        filename: Name of the JSON file to load (e.g., "orgs.json")
        dump_dir: Optional path to directory containing JSON dump files.
                  Defaults to tests/dump (resolved relative to ROOT_DIR).
    
    Returns:
        Summary of loaded records.
    """
    data_dir = get_dump_dir(dump_dir)
    filepath = data_dir / filename
    
    if not filepath.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {filepath}")
    
    # Find the model class for this file
    model_class = None
    for fn, mc in LOAD_ORDER:
        if fn == filename:
            model_class = mc
            break
    
    if model_class is None:
        raise HTTPException(status_code=400, detail=f"Unknown file: {filename}")
    
    try:
        records = load_json_file(filepath)
        count = 0
        
        for record in records:
            cleaned_data = clean_model_data(record, model_class)
            instance = model_class(**cleaned_data)
            db.add(instance)
            count += 1
        
        db.commit()
        return {"status": "success", "loaded": count}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error loading file: {str(e)}")


# ============================================================================
# Backup Management Functions
# ============================================================================def is_postgresql() -> bool:
    """Check if using PostgreSQL."""
    return DATABASE_URL.startswith("postgres")


def is_sqlite() -> bool:
    """Check if using SQLite."""
    return DATABASE_URL.startswith("sqlite")


def get_sqlite_path() -> Path:
    """Get the SQLite database file path from resolved configuration.
    
    Uses get_sqlite_database_path() from config module to ensure paths
    are resolved relative to ROOT_DIR.
    
    Returns:
        Path: Absolute path to SQLite database file
        
    Raises:
        ValueError: If DATABASE_URL is not SQLite
    """
    db_path = get_sqlite_database_path()
    if db_path is None:
        raise ValueError("DATABASE_URL is not SQLite, cannot get database path")
    return db_path


@router.post("/admin/backups/backup", tags=["admin"])
def create_backup() -> dict[str, Any]:
    """
    Create a backup of the database.
    - For PostgreSQL: Creates a PostgreSQL dump file
    - For SQLite: Copies the database file
    
    Backup is named with ISO datetime (second resolution).
    """
    backup_dir = get_backup_dir()
    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    
    try:
        if is_postgresql():
            # PostgreSQL dump
            from urllib.parse import urlparse
            parsed = urlparse(DATABASE_URL)
            
            backup_file = backup_dir / f"backup-{timestamp}.sql"
            
            # Build pg_dump command
            env = {}
            if parsed.password:
                env["PGPASSWORD"] = parsed.password
            
            cmd = [
                "pg_dump",
                "-h", parsed.hostname or "localhost",
                "-U", parsed.username or "postgres",
                "-d", parsed.path.lstrip("/"),
                "-f", str(backup_file),
            ]
            
            result = subprocess.run(cmd, env={**os.environ, **env}, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"pg_dump failed: {result.stderr}")
            
            return {
                "status": "success",
                "backup_file": str(backup_file),
                "timestamp": timestamp,
                "type": "postgresql",
            }
        
        elif is_sqlite():
            # SQLite backup
            src_db = get_sqlite_path()
            backup_file = backup_dir / f"backup-{timestamp}.db"
            
            shutil.copy2(src_db, backup_file)
            
            return {
                "status": "success",
                "backup_file": str(backup_file),
                "timestamp": timestamp,
                "type": "sqlite",
            }
        
        else:
            raise HTTPException(status_code=400, detail="Unsupported database type")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backup failed: {str(e)}")


@router.get("/admin/backups/list", tags=["admin"])
def list_backups() -> dict[str, Any]:
    """List all available backups."""
    backup_dir = get_backup_dir()
    
    if not backup_dir.exists():
        return {"backups": [], "count": 0}
    
    backups = []
    for backup_file in sorted(backup_dir.glob("backup-*"), reverse=True):
        stat = backup_file.stat()
        backups.append({
            "filename": backup_file.name,
            "path": str(backup_file),
            "size_bytes": stat.st_size,
            "created": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        })
    
    return {"backups": backups, "count": len(backups)}


@router.post("/admin/backups/restore", tags=["admin"])
def restore_backup(
    backup_name: str | None = Query(None, description="Backup filename. If not specified, restores the most recent."),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Restore a backup of the database.
    
    Args:
        backup_name: Name of the backup file (e.g., "backup-2024-01-15T10:30:45.sql")
                     If not specified, restores the most recent backup.
    """
    backup_dir = get_backup_dir()
    
    if not backup_dir.exists() or not list(backup_dir.glob("backup-*")):
        raise HTTPException(status_code=404, detail="No backups found")
    
    if backup_name:
        backup_file = backup_dir / backup_name
    else:
        # Get most recent backup
        backups = sorted(backup_dir.glob("backup-*"), reverse=True)
        if not backups:
            raise HTTPException(status_code=404, detail="No backups found")
        backup_file = backups[0]
    
    if not backup_file.exists():
        raise HTTPException(status_code=404, detail=f"Backup not found: {backup_name}")
    
    try:
        if is_postgresql():
            # PostgreSQL restore
            from urllib.parse import urlparse
            parsed = urlparse(DATABASE_URL)
            
            env = {}
            if parsed.password:
                env["PGPASSWORD"] = parsed.password
            
            cmd = [
                "psql",
                "-h", parsed.hostname or "localhost",
                "-U", parsed.username or "postgres",
                "-d", parsed.path.lstrip("/"),
                "-f", str(backup_file),
            ]
            
            result = subprocess.run(cmd, env={**os.environ, **env}, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"psql restore failed: {result.stderr}")
            
            return {
                "status": "success",
                "backup_file": backup_file.name,
                "message": "Database restored from PostgreSQL dump",
            }
        
        elif is_sqlite():
            # SQLite restore
            target_db = get_sqlite_path()
            shutil.copy2(backup_file, target_db)
            
            return {
                "status": "success",
                "backup_file": backup_file.name,
                "message": "Database restored from SQLite backup",
            }
        
        else:
            raise HTTPException(status_code=400, detail="Unsupported database type")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Restore failed: {str(e)}")


# ============================================================================
# SQLite Export/Import Functions
# ============================================================================

@router.get("/admin/sqlite/export", tags=["admin"])
def export_sqlite() -> FileResponse:
    """
    Export the database as a SQLite file.
    Returns the SQLite database file for download.
    """
    if not is_sqlite():
        raise HTTPException(status_code=400, detail="Only available for SQLite databases")
    
    db_path = get_sqlite_path()
    if not db_path.exists():
        raise HTTPException(status_code=404, detail="Database file not found")
    
    filename = f"export-{datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}.db"
    
    return FileResponse(
        path=db_path,
        filename=filename,
        media_type="application/octet-stream",
    )


@router.post("/admin/sqlite/import", tags=["admin"])
async def import_sqlite(file: UploadFile = File(...)) -> dict[str, Any]:
    """
    Import a SQLite database file.
    Replaces the current database with the uploaded file.
    """
    if not is_sqlite():
        raise HTTPException(status_code=400, detail="Only available for SQLite databases")
    
    try:
        db_path = get_sqlite_path()
        contents = await file.read()
        
        # Backup current database
        backup_dir = get_backup_dir()
        backup_file = backup_dir / f"backup-pre-import-{datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}.db"
        if db_path.exists():
            shutil.copy2(db_path, backup_file)
        
        # Write new database
        with open(db_path, "wb") as f:
            f.write(contents)
        
        return {
            "status": "success",
            "message": "SQLite database imported successfully",
            "backup_created": str(backup_file) if db_path.exists() else None,
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


# ============================================================================
# ZIP Export/Import Functions
# ============================================================================

@router.get("/admin/zip/export", tags=["admin"])
def export_zip(db: Session = Depends(get_db)) -> StreamingResponse:
    """
    Export all data as a ZIP file containing JSON files.
    One JSON file per table.
    """
    try:
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for filename, model_class in LOAD_ORDER:
                # Query all records for this model
                records = db.query(model_class).all()
                
                # Convert to JSON-serializable format
                json_data = []
                for record in records:
                    row_dict = {}
                    for col in inspect(model_class).columns:
                        value = getattr(record, col.name)
                        # Handle datetime objects
                        if isinstance(value, datetime):
                            value = value.isoformat()
                        row_dict[col.name] = value
                    json_data.append(row_dict)
                
                # Write JSON file to ZIP
                json_content = json.dumps(json_data, indent=2, default=str)
                zip_file.writestr(filename, json_content)
        
        zip_buffer.seek(0)
        
        timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        return StreamingResponse(
            iter([zip_buffer.getvalue()]),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename=data-{timestamp}.zip"},
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/admin/zip/import", tags=["admin"])
async def import_zip(file: UploadFile = File(...), db: Session = Depends(get_db)) -> dict[str, Any]:
    """
    Import data from a ZIP file containing JSON files.
    """
    try:
        contents = await file.read()
        results = {}
        errors = []
        
        with zipfile.ZipFile(BytesIO(contents), "r") as zip_file:
            for filename, model_class in LOAD_ORDER:
                try:
                    if filename not in zip_file.namelist():
                        results[filename] = {"skipped": True, "reason": "file not in ZIP"}
                        continue
                    
                    json_content = zip_file.read(filename).decode("utf-8")
                    records = json.loads(json_content)
                    count = 0
                    
                    for record in records:
                        cleaned_data = clean_model_data(record, model_class)
                        instance = model_class(**cleaned_data)
                        db.add(instance)
                        count += 1
                    
                    db.commit()
                    results[filename] = {"imported": count}
                
                except Exception as e:
                    db.rollback()
                    error_msg = f"Error importing {filename}: {str(e)}"
                    errors.append(error_msg)
                    results[filename] = {"error": str(e)}
        
        return {
            "status": "success" if not errors else "partial",
            "results": results,
            "errors": errors,
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


# ============================================================================
# Single Table Export/Import Functions
# ============================================================================

@router.get("/admin/tables/{table_name}/export", tags=["admin"])
def export_table(table_name: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    """
    Export a single table as JSON.
    
    Args:
        table_name: Name of the table (e.g., "metros", "persons")
    """
    # Find the model class
    model_class = None
    for _, mc in LOAD_ORDER:
        if mc.__tablename__ == table_name:
            model_class = mc
            break
    
    if model_class is None:
        raise HTTPException(status_code=404, detail=f"Table not found: {table_name}")
    
    try:
        records = db.query(model_class).all()
        
        # Convert to JSON-serializable format
        json_data = []
        for record in records:
            row_dict = {}
            for col in inspect(model_class).columns:
                value = getattr(record, col.name)
                # Handle datetime objects
                if isinstance(value, datetime):
                    value = value.isoformat()
                row_dict[col.name] = value
            json_data.append(row_dict)
        
        return {
            "table_name": table_name,
            "record_count": len(json_data),
            "records": json_data,
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/admin/tables/{table_name}/import", tags=["admin"])
async def import_table(
    table_name: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Import data to a single table from a JSON file.
    
    Args:
        table_name: Name of the table (e.g., "metros", "persons")
    """
    # Find the model class
    model_class = None
    for _, mc in LOAD_ORDER:
        if mc.__tablename__ == table_name:
            model_class = mc
            break
    
    if model_class is None:
        raise HTTPException(status_code=404, detail=f"Table not found: {table_name}")
    
    try:
        contents = await file.read()
        records = json.loads(contents.decode("utf-8"))
        count = 0
        
        for record in records:
            cleaned_data = clean_model_data(record, model_class)
            instance = model_class(**cleaned_data)
            db.add(instance)
            count += 1
        
        db.commit()
        
        return {
            "status": "success",
            "table_name": table_name,
            "imported": count,
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")
