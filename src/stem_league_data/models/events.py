"""Event-related models: Service, Activity, Registration, RSVP."""

from datetime import date, time, datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text, Integer, Boolean, Date, Time, DateTime, Table, Column
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from stem_league_data.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from stem_league_data.models.content import Content
    from stem_league_data.models.place import Metro, Venue, Org, Flyer
    from stem_league_data.models.people import Person, Visitor
    from stem_league_data.models.jobs import InstructorAssignment
    from stem_league_data.models.categories import Program, Track, Category, SubCategory, Topic, Tag


# Association tables for Activity
activity_programs = Table(
    "activity_programs",
    Base.metadata,
    Column("activity_id", ForeignKey("activities.id", ondelete="CASCADE"), primary_key=True),
    Column("program_id", ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True),
)

activity_tracks = Table(
    "activity_tracks",
    Base.metadata,
    Column("activity_id", ForeignKey("activities.id", ondelete="CASCADE"), primary_key=True),
    Column("track_id", ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True),
)

activity_categories = Table(
    "activity_categories",
    Base.metadata,
    Column("activity_id", ForeignKey("activities.id", ondelete="CASCADE"), primary_key=True),
    Column("category_id", ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True),
)

activity_topics = Table(
    "activity_topics",
    Base.metadata,
    Column("activity_id", ForeignKey("activities.id", ondelete="CASCADE"), primary_key=True),
    Column("topic_id", ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True),
)

activity_subcategories = Table(
    "activity_subcategories",
    Base.metadata,
    Column("activity_id", ForeignKey("activities.id", ondelete="CASCADE"), primary_key=True),
    Column("subcategory_id", ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True),
)

# Association tables for Event
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


class Service(Base, TimestampMixin):
    """Describes the educational content of a class, course or event. Similar to a Pike13 Service, 
    but only describes the content, not scheduling or location."""

    __tablename__ = "services"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    content_id: Mapped[int | None] = mapped_column(ForeignKey("contents.id", ondelete="SET NULL"))
    content: Mapped["Content | None"] = relationship()

    grade: Mapped[str | None] = mapped_column(String(50))
    level: Mapped[str | None] = mapped_column(String(50))
    topics: Mapped[list["Topic"]] = relationship(secondary=activity_topics)
    
    tracks: Mapped[list["Track"]] = relationship(secondary=activity_tracks)
    categories: Mapped[list["Category"]] = relationship(secondary=activity_categories)
    subcategories: Mapped[list["SubCategory"]] = relationship(secondary=activity_subcategories)

    curriculum_link: Mapped[str | None] = mapped_column(String(500))
    
    subordinate_to: Mapped[list["Service"]] = relationship(back_populates="superior_to")
    activities: Mapped[list["Activity"]] = relationship(back_populates="service")


class Activity(Base, TimestampMixin):
    """An activity is a scheduled delivery of a service, and is specialized to 
    a class ( fixed recuring schedule), a course (limited number of scheduled
    dates), an Event (single date), or an appointment ( Scheduled slots, but
    must be booked to actually be on a schedule)"""

    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(primary_key=True)

    type: Mapped[str | None] = mapped_column(String(50)  )  # enum: class, course, event, appointment
    status: Mapped[str | None] = mapped_column(String(50))  # enum: draft, published, cancelled, completed

    service_id: Mapped[int | None] = mapped_column(ForeignKey("services.id", ondelete="SET NULL"))
    service: Mapped["Service | None"] = relationship(back_populates="activities")

    # Content about this activity; there is also content in the service
    content_id: Mapped[int | None] = mapped_column(ForeignKey("contents.id", ondelete="SET NULL"))
    content: Mapped["Content | None"] = relationship()

    # Schedule. These values here must match with type
    start_dt: Mapped[datetime | None] = mapped_column(DateTime)
    end_dt: Mapped[datetime | None] = mapped_column(DateTime)
    day_numbers: Mapped[list[int] | None] = mapped_column(ARRAY(Integer))  # 0=Mon, 6=Sun
    rrule: Mapped[str | None] = mapped_column(String(500))  # iCal recurrence rule

    # Location and sponsor
    venue_id: Mapped[int] = mapped_column( ForeignKey("venues.id", ondelete="RESTRICT"), nullable=False)
    venue: Mapped["Venue"] = relationship(back_populates="events")

    org_id: Mapped[int | None] = mapped_column( ForeignKey("orgs.id", ondelete="SET NULL"))
    org: Mapped["Org | None"] = relationship(back_populates="events")

    # Enrollment
    enrollment_opens: Mapped[datetime | None] = mapped_column(DateTime)
    enrollment_closes: Mapped[datetime | None] = mapped_column(DateTime)
    enrollment_id: Mapped[int | None] = mapped_column(ForeignKey("contents.id", ondelete="SET NULL"))
    enrollment: Mapped["Content | None"] = relationship(foreign_keys="[Activity.enrollment_id]")
    schedule_link: Mapped[str | None] = mapped_column(String(500))

    cta_id: Mapped[int | None] = mapped_column(ForeignKey("contents.id", ondelete="SET NULL"))
    cta: Mapped["Content | None"] = relationship(foreign_keys="[Activity.cta_id]")

    active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Taxonomy

    programs: Mapped[list["Program"]] = relationship(secondary=activity_programs)
    tracks: Mapped[list["Track"]] = relationship(secondary=activity_tracks)
    categories: Mapped[list["Category"]] = relationship(secondary=activity_categories)
    subcategories: Mapped[list["SubCategory"]] = relationship(secondary=activity_subcategories)

    capacity: Mapped[int | None] = mapped_column(Integer)

    registration_type: Mapped[str | None] = mapped_column( String(50) )  # enum: open, closed, waitlist, invite_only
    registrations: Mapped[list["Registration"]] = relationship(back_populates="event")

    rsvps: Mapped[list["RSVP"]] = relationship(back_populates="event")
    instructor_assignments: Mapped[list["InstructorAssignment"]] = relationship(
        back_populates="activity"
    )

class MarketingStats(Base, TimestampMixin):
    """Marketing statistics for events."""

    __tablename__ = "marketingstats"

    id: Mapped[int] = mapped_column(primary_key=True)
    walk_in_count: Mapped[int] = mapped_column(Integer, default=0)
    page_views: Mapped[int] = mapped_column(Integer, default=0)
    register_clicks: Mapped[int] = mapped_column(Integer, default=0)
    reference: Mapped[str | None] = mapped_column(String(255))  # optional external reference ID

    # Relationships

    flyers: Mapped[list["Flyer"]] = relationship(
        secondary=flyer_events, back_populates="events"
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
    event: Mapped["Activity"] = relationship(back_populates="registrations")
    registrant: Mapped["Person"] = relationship(back_populates="registrations")
    rsvps: Mapped[list["RSVP"]] = relationship(back_populates="registration")


class RSVP(Base, TimestampMixin):
    """An RSVP for an event registration."""

    __tablename__ = "rsvps"

    id: Mapped[int] = mapped_column(primary_key=True)
    role: Mapped[str | None] = mapped_column(String(50))  # enum: student, chaperone, volunteer
    visitor_relationship: Mapped[str | None] = mapped_column(String(50))  # enum: self, parent, guardian, sibling
    attended: Mapped[bool] = mapped_column(Boolean, default=False)
    checked_in_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)

    registration_id: Mapped[int] = mapped_column(ForeignKey("registrations.id", ondelete="CASCADE"), nullable=False)
    event_id: Mapped[int] = mapped_column(ForeignKey("activities.id", ondelete="CASCADE"), nullable=False)
    visitor_id: Mapped[int] = mapped_column(ForeignKey("visitors.id", ondelete="CASCADE"), nullable=False)
    guardian_id: Mapped[int | None] = mapped_column(ForeignKey("persons.id", ondelete="SET NULL"))

    # Relationships
    registration: Mapped["Registration"] = relationship(back_populates="rsvps")
    event: Mapped["Activity"] = relationship(back_populates="rsvps")
    visitor: Mapped["Visitor"] = relationship(
        back_populates="rsvps", foreign_keys=[visitor_id]
    )
    guardian: Mapped["Person | None"] = relationship(
        back_populates="guardian_rsvps", foreign_keys=[guardian_id]
    )



