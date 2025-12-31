"""Dev test for SQLAlchemy models creation."""

import pytest


def test_all_models_import():
    """Test that all models can be imported without errors."""
    from stem_league_data.models import (
        Base,
        # Place
        Metro,
        Venue,
        Org,
        Flyer,
        # People
        Person,
        # Events
        Event,
        EventPrototype,
        Tag,
        Registration,
        RSVP,
        # Jobs
        JobPosting,
        InstructorAssignment,
        InstructorEvaluation,
        # Categories
        Group,
        Program,
        Track,
        Category,
        SubCategory,
        Topic,
        # Content
        Content,
        Page,
        Class,
        Enrollment,
        CTA,
        Announcement,
        # External Services
        Meetup,
        Pike13Service,
        P13Location,
    )

    # Verify Base is the declarative base
    assert hasattr(Base, "metadata")


def test_base_has_metadata():
    """Test that Base has proper SQLAlchemy metadata."""
    from stem_league_data.models import Base

    assert Base.metadata is not None
    # Check that tables are registered
    assert len(Base.metadata.tables) > 0


def test_model_table_names():
    """Test that models have expected table names."""
    from stem_league_data.models import (
        Metro,
        Venue,
        Org,
        Person,
        Event,
        Registration,
    )

    assert Metro.__tablename__ == "metros"
    assert Venue.__tablename__ == "venues"
    assert Org.__tablename__ == "orgs"
    assert Person.__tablename__ == "persons"
    assert Event.__tablename__ == "events"
    assert Registration.__tablename__ == "registrations"


def test_model_relationships_defined():
    """Test that key relationships are defined on models."""
    from stem_league_data.models import Metro, Event, Person

    # Metro should have relationships to venues, orgs, persons, events
    assert hasattr(Metro, "venues")
    assert hasattr(Metro, "orgs")
    assert hasattr(Metro, "persons")
    assert hasattr(Metro, "events")

    # Event should have relationships
    assert hasattr(Event, "metro")
    assert hasattr(Event, "venue")
    assert hasattr(Event, "registrations")

    # Person should have relationships
    assert hasattr(Person, "metro")
    assert hasattr(Person, "registrations")
    assert hasattr(Person, "rsvps")


def test_group_inheritance():
    """Test that Group subclasses use single-table inheritance."""
    from stem_league_data.models import Group, Program, Track, Category, Topic

    # All should share the same table
    assert Program.__tablename__ == "groups"
    assert Track.__tablename__ == "groups"
    assert Category.__tablename__ == "groups"
    assert Topic.__tablename__ == "groups"

    # Check polymorphic identity
    assert Program.__mapper_args__["polymorphic_identity"] == "program"
    assert Track.__mapper_args__["polymorphic_identity"] == "track"
    assert Category.__mapper_args__["polymorphic_identity"] == "category"
    assert Topic.__mapper_args__["polymorphic_identity"] == "topic"
