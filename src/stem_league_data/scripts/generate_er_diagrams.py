"""Generate ER diagrams grouped by module."""

from pathlib import Path

from eralchemy2 import render_er
from sqlalchemy import MetaData, Table, Column, Integer, String, ForeignKey

from stem_league_data.models import Base


# Define the module groups matching the original mermaid files
GROUPS = {
    "place": {
        "tables": ["metros", "venues", "orgs", "flyers", "flyer_events"],
        "stubs": ["events"],
        "description": "Place-related models: Metro, Venue, Org, Flyer",
    },
    "people": {
        "tables": ["persons"],
        "stubs": ["metros"],
        "description": "People-related models: Person",
    },
    "events": {
        "tables": [
            "events",
            "event_prototypes",
            "tags",
            "registrations",
            "rsvps",
            "event_tags",
            "flyer_events",
        ],
        "stubs": ["metros", "venues", "orgs", "flyers", "persons"],
        "description": "Event-related models: Event, EventPrototype, Tag, Registration, RSVP",
    },
    "jobs": {
        "tables": [
            "job_postings",
            "instructor_assignments",
            "instructor_evaluations",
        ],
        "stubs": ["metros", "orgs", "persons", "events"],
        "description": "Job-related models: JobPosting, InstructorAssignment, InstructorEvaluation",
    },
    "categories": {
        "tables": ["groups"],
        "stubs": ["orgs"],
        "description": "Category-related models: Group, Program, Track, Category, SubCategory, Topic",
    },
    "content": {
        "tables": [
            "contents",
            "classes",
            "enrollments",
            "ctas",
            "announcements",
            "class_categories",
            "class_topics",
            "class_ctas",
            "class_enrollments",
        ],
        "stubs": ["groups"],
        "description": "Content-related models: Content, Page, Class, Enrollment, CTA, Announcement",
    },
    "ext_services": {
        "tables": ["meetups", "pike13_services", "p13_locations"],
        "description": "External service models: Meetup, Pike13Service, P13Location",
    },
}


def create_stub_table(metadata: MetaData, table_name: str, source_metadata: MetaData) -> Table:
    """Create a stub table with just the primary key."""
    source_table = source_metadata.tables.get(table_name)
    if source_table is None:
        raise ValueError(f"Table {table_name} not found in source metadata")

    # Get primary key columns
    pk_columns = []
    for col in source_table.primary_key.columns:
        pk_columns.append(
            Column(col.name, col.type, primary_key=True)
        )

    return Table(table_name, metadata, *pk_columns)


def create_group_metadata(group_name: str, group_config: dict) -> MetaData:
    """Create a metadata object for a specific group."""
    source_metadata = Base.metadata
    group_metadata = MetaData()

    # First, create stub tables (they may be referenced by main tables)
    stub_tables = group_config.get("stubs", [])
    for table_name in stub_tables:
        if table_name in source_metadata.tables:
            create_stub_table(group_metadata, table_name, source_metadata)

    # Then, copy the main tables
    for table_name in group_config["tables"]:
        source_table = source_metadata.tables.get(table_name)
        if source_table is None:
            print(f"Warning: Table {table_name} not found, skipping")
            continue

        # Copy the table structure
        columns = []
        for col in source_table.columns:
            # Check if this is a foreign key to a stub or included table
            fk_target = None
            for fk in col.foreign_keys:
                target_table = fk.column.table.name
                if target_table in stub_tables or target_table in group_config["tables"]:
                    fk_target = f"{target_table}.{fk.column.name}"

            if fk_target:
                columns.append(
                    Column(col.name, col.type, ForeignKey(fk_target), 
                           primary_key=col.primary_key, nullable=col.nullable)
                )
            else:
                columns.append(
                    Column(col.name, col.type, 
                           primary_key=col.primary_key, nullable=col.nullable)
                )

        Table(table_name, group_metadata, *columns)

    return group_metadata


def generate_group_diagrams(output_dir: Path):
    """Generate ER diagrams for each group."""
    output_dir.mkdir(parents=True, exist_ok=True)

    for group_name, group_config in GROUPS.items():
        print(f"Generating {group_name} diagram...")
        
        try:
            group_metadata = create_group_metadata(group_name, group_config)
            
            # Generate PNG only
            png_path = output_dir / f"er-{group_name}.png"
            
            render_er(group_metadata, str(png_path))
            
            print(f"  Generated {png_path.name}")
        except Exception as e:
            print(f"  Error generating {group_name}: {e}")

    # Also generate the full diagram
    print("Generating full diagram...")
    render_er(Base, str(output_dir / "er-full.png"))
    print("  Generated er-full.png")


if __name__ == "__main__":
    import sys
    # Use project root, not script location
    project_root = Path(__file__).parent.parent.parent.parent
    output_dir = project_root / "docs" / "data-model"
    generate_group_diagrams(output_dir)
