"""Router for Admin operations: data loading, database management."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from stem_league_data.database import get_db, create_tables, drop_tables
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

# Default path to dump directory
DEFAULT_DUMP_DIR = Path(__file__).parent.parent.parent.parent / "tests" / "dump"

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
                  Defaults to tests/dump.
    
    Returns:
        Summary of loaded records per model.
    """
    data_dir = Path(dump_dir) if dump_dir else DEFAULT_DUMP_DIR
    
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
    
    Returns:
        Summary of loaded records.
    """
    data_dir = Path(dump_dir) if dump_dir else DEFAULT_DUMP_DIR
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
