"""Event-related models: Event, EventPrototype, Tag, Registration, RSVP."""

from datetime import date, time, datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text, Integer, Boolean, Date, Time, DateTime, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship

from stem_league_data.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from stem_league_data.models.content import Content
    from stem_league_data.models.place import Metro, Venue, Org, Flyer
    from stem_league_data.models.people import Person
    from stem_league_data.models.jobs import InstructorAssignment


# Association tables
flyer_events = Table(
    "flyer_events",
    Base.metadata,
    Column("flyer_id", ForeignKey("flyers.id", ondelete="CASCADE"), primary_key=True),
    Column("event_id", ForeignKey("events.id", ondelete="CASCADE"), primary_key=True),
)

event_tags = Table(
    "event_tags",
    Base.metadata,
    Column("event_id", ForeignKey("events.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Event(Base, TimestampMixin):
    """An event in the League STEM network."""

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    start_dt: Mapped[datetime | None] = mapped_column(DateTime)
    end_dt: Mapped[datetime | None] = mapped_column(DateTime)

    capacity: Mapped[int | None] = mapped_column(Integer)

    registration_type: Mapped[str | None] = mapped_column(String(50))  # enum: open, closed, waitlist, invite_only
    status: Mapped[str | None] = mapped_column(String(50))  # enum: draft, published, cancelled, completed
    walk_in_count: Mapped[int] = mapped_column(Integer, default=0)
    page_views: Mapped[int] = mapped_column(Integer, default=0)
    register_clicks: Mapped[int] = mapped_column(Integer, default=0)
    reference: Mapped[str | None] = mapped_column(String(255))  # optional external reference ID

    metro_id: Mapped[int] = mapped_column(ForeignKey("metros.id", ondelete="RESTRICT"), nullable=False)
    venue_id: Mapped[int] = mapped_column(ForeignKey("venues.id", ondelete="RESTRICT"), nullable=False)
    org_id: Mapped[int | None] = mapped_column(ForeignKey("orgs.id", ondelete="SET NULL"))
    prototype_id: Mapped[int | None] = mapped_column(ForeignKey("event_prototypes.id", ondelete="SET NULL"))
    content_id: Mapped[int | None] = mapped_column(ForeignKey("contents.id", ondelete="SET NULL"))

    # Relationships
    metro: Mapped["Metro"] = relationship(back_populates="events")
    venue: Mapped["Venue"] = relationship(back_populates="events")
    org: Mapped["Org | None"] = relationship(back_populates="events")
    prototype: Mapped["EventPrototype | None"] = relationship(back_populates="events")
    content: Mapped["Content | None"] = relationship()
    flyers: Mapped[list["Flyer"]] = relationship(
        secondary=flyer_events, back_populates="events"
    )
    tags: Mapped[list["Tag"]] = relationship(
        secondary=event_tags, back_populates="events"
    )
    registrations: Mapped[list["Registration"]] = relationship(back_populates="event")
    rsvps: Mapped[list["RSVP"]] = relationship(back_populates="event")
    instructor_assignments: Mapped[list["InstructorAssignment"]] = relationship(
        back_populates="event"
    )


class EventPrototype(Base, TimestampMixin):
    """A template for creating events."""

    __tablename__ = "event_prototypes"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    default_capacity: Mapped[int | None] = mapped_column(Integer)
    registration_type: Mapped[str | None] = mapped_column(String(50))
    content_id: Mapped[int | None] = mapped_column(ForeignKey("contents.id", ondelete="SET NULL"))

    # Relationships
    events: Mapped[list["Event"]] = relationship(back_populates="prototype")
    content: Mapped["Content | None"] = relationship()


class Tag(Base):
    """A tag for categorizing events."""

    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    # Relationships
    events: Mapped[list["Event"]] = relationship(
        secondary=event_tags, back_populates="tags"
    )


class Registration(Base, TimestampMixin):
    """A registration for an event."""

    __tablename__ = "registrations"

    id: Mapped[int] = mapped_column(primary_key=True)
    registration_source: Mapped[str | None] = mapped_column(String(50))  # enum: web, phone, walk_in, partner
    utm_source: Mapped[str | None] = mapped_column(String(100))
    utm_campaign: Mapped[str | None] = mapped_column(String(100))
    notes: Mapped[str | None] = mapped_column(Text)

    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    registrant_id: Mapped[int] = mapped_column(ForeignKey("persons.id", ondelete="CASCADE"), nullable=False)

    # Relationships
    event: Mapped["Event"] = relationship(back_populates="registrations")
    registrant: Mapped["Person"] = relationship(back_populates="registrations")
    rsvps: Mapped[list["RSVP"]] = relationship(back_populates="registration")


class RSVP(Base, TimestampMixin):
    """An RSVP for an event registration."""

    __tablename__ = "rsvps"

    id: Mapped[int] = mapped_column(primary_key=True)
    role: Mapped[str | None] = mapped_column(String(50))  # enum: student, chaperone, volunteer
    attendee_relationship: Mapped[str | None] = mapped_column(String(50))  # enum: self, parent, guardian, sibling
    attended: Mapped[bool] = mapped_column(Boolean, default=False)
    checked_in_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)

    registration_id: Mapped[int] = mapped_column(ForeignKey("registrations.id", ondelete="CASCADE"), nullable=False)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    attendee_id: Mapped[int] = mapped_column(ForeignKey("persons.id", ondelete="CASCADE"), nullable=False)
    guardian_id: Mapped[int | None] = mapped_column(ForeignKey("persons.id", ondelete="SET NULL"))

    # Relationships
    registration: Mapped["Registration"] = relationship(back_populates="rsvps")
    event: Mapped["Event"] = relationship(back_populates="rsvps")
    attendee: Mapped["Person"] = relationship(
        back_populates="rsvps", foreign_keys=[attendee_id]
    )
    guardian: Mapped["Person | None"] = relationship(
        back_populates="guardian_rsvps", foreign_keys=[guardian_id]
    )
