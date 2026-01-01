"""Event-related models: Service, Activity, Registration, RSVP."""

from datetime import date, time, datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text, Integer, Boolean, Date, Time, DateTime, Table, Column
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship, composite

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

# Association tables for Service
service_topics = Table(
    "service_topics",
    Base.metadata,
    Column("service_id", ForeignKey("services.id", ondelete="CASCADE"), primary_key=True),
    Column("topic_id", ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True),
)

service_tracks = Table(
    "service_tracks",
    Base.metadata,
    Column("service_id", ForeignKey("services.id", ondelete="CASCADE"), primary_key=True),
    Column("track_id", ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True),
)

service_categories = Table(
    "service_categories",
    Base.metadata,
    Column("service_id", ForeignKey("services.id", ondelete="CASCADE"), primary_key=True),
    Column("category_id", ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True),
)

service_subcategories = Table(
    "service_subcategories",
    Base.metadata,
    Column("service_id", ForeignKey("services.id", ondelete="CASCADE"), primary_key=True),
    Column("subcategory_id", ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True),
)

# Association tables for Activity
flyer_activities = Table(
    "flyer_activities",
    Base.metadata,
    Column("flyer_id", ForeignKey("flyers.id", ondelete="CASCADE"), primary_key=True),
    Column("activity_id", ForeignKey("activities.id", ondelete="CASCADE"), primary_key=True),
)

activity_tags = Table(
    "activity_tags",
    Base.metadata,
    Column("activity_id", ForeignKey("activities.id", ondelete="CASCADE"), primary_key=True),
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

    pike13_service_id: Mapped[int | None] = mapped_column(Integer)

    grade: Mapped[str | None] = mapped_column(String(50))
    level: Mapped[str | None] = mapped_column(String(50))
    topics: Mapped[list["Topic"]] = relationship(secondary=service_topics)
    
    tracks: Mapped[list["Track"]] = relationship(secondary=service_tracks)
    categories: Mapped[list["Category"]] = relationship(secondary=service_categories)
    subcategories: Mapped[list["SubCategory"]] = relationship(secondary=service_subcategories)

    curriculum_link: Mapped[str | None] = mapped_column(String(500))
    
    # Self-referential relationship for service hierarchy
    parent_service_id: Mapped[int | None] = mapped_column(ForeignKey("services.id", ondelete="SET NULL"))
    subordinate_to: Mapped["Service | None"] = relationship(
        back_populates="superior_to", remote_side="Service.id"
    )
    superior_to: Mapped[list["Service"]] = relationship(back_populates="subordinate_to")
    
    activities: Mapped[list["Activity"]] = relationship(back_populates="service")


class RRule:
    """Recurrence rule for scheduling activities.

    This is a composite value object (not a separate table) - its fields are
    embedded directly in the parent table (e.g., Activity).

    Supported shapes:

    - Single (non-recurring) events: frequency == "ONCE" (no RRULE is emitted).
    - Weekly recurring events: frequency == "WEEKLY" and days contains 1+ weekdays.
    - Monthly "Nth weekday" events: frequency == "MONTHLY" with exactly one
      weekday in days and setpos indicating the Nth occurrence (e.g., 4 for
      "4th", -1 for "last").

    Weekday numbering uses Mon=0 .. Sun=6.

    Notes:
    - `count` represents RRULE COUNT (total number of occurrences). If you need
      an UNTIL boundary, derive it from occurrences externally; storing UNTIL
      is intentionally omitted to avoid redundancy.
    """

    def __init__(
        self,
        frequency: str | None = "ONCE",
        interval: int | None = 1,
        days: list[int] | None = None,
        setpos: int | None = 0,
        count: int | None = None,
    ):
        self.frequency = frequency or "ONCE"
        self.interval = interval or 1
        self.days = days
        self.setpos = setpos or 0
        self.count = count

    def __composite_values__(self):
        return self.frequency, self.interval, self.days, self.setpos, self.count

    def __repr__(self):
        return (
            f"RRule(frequency={self.frequency!r}, interval={self.interval}, "
            f"days={self.days}, setpos={self.setpos}, count={self.count})"
        )

    def __eq__(self, other):
        if not isinstance(other, RRule):
            return False
        return (
            self.frequency == other.frequency
            and self.interval == other.interval
            and self.days == other.days
            and self.setpos == other.setpos
            and self.count == other.count
        )

    def __ne__(self, other):
        return not self.__eq__(other)

    # --- RRULE serialization ---

    _WKDAY_TOKENS = ("MO", "TU", "WE", "TH", "FR", "SA", "SU")

    def to_ical_rrule(self) -> str | None:
        """Return an iCalendar RRULE line for this recurrence, or None for ONCE.

        Examples:
            - WEEKLY on Wed/Fri for 6 occurrences:
              RRULE:FREQ=WEEKLY;INTERVAL=1;BYDAY=WE,FR;COUNT=6

            - MONTHLY on the 4th Tuesday:
              RRULE:FREQ=MONTHLY;INTERVAL=1;BYDAY=TU;BYSETPOS=4

        Validation is strict for the supported shapes and will raise ValueError
        if the stored fields are inconsistent.
        """

        freq = (self.frequency or "").upper()

        if freq == "ONCE":
            return None

        if freq not in {"WEEKLY", "MONTHLY"}:
            raise ValueError(f"Unsupported frequency: {self.frequency!r}")

        interval = int(self.interval or 1)
        if interval < 1:
            raise ValueError("interval must be >= 1")

        days = list(self.days or [])
        if freq == "WEEKLY":
            if not days:
                raise ValueError("WEEKLY rules require at least one weekday in days")
            if self.setpos not in (0, None):
                raise ValueError("WEEKLY rules must not set setpos")

        if freq == "MONTHLY":
            if len(days) != 1:
                raise ValueError("MONTHLY rules require exactly one weekday in days")
            if self.setpos == 0:
                raise ValueError(
                    "MONTHLY rules require setpos (e.g., 4 for 4th, -1 for last)"
                )

        # Validate weekday integers and map to iCal tokens
        tokens: list[str] = []
        for d in days:
            if not isinstance(d, int):
                raise ValueError("days must be a list of integers")
            if d < 0 or d > 6:
                raise ValueError("weekday values must be in range 0..6 (Mon..Sun)")
            tokens.append(self._WKDAY_TOKENS[d])

        parts: list[str] = [f"FREQ={freq}", f"INTERVAL={interval}"]

        if tokens:
            parts.append("BYDAY=" + ",".join(tokens))

        if freq == "MONTHLY":
            parts.append(f"BYSETPOS={int(self.setpos)}")

        if self.count is not None:
            count_val = int(self.count)
            if count_val < 1:
                raise ValueError("count (COUNT) must be >= 1")
            parts.append(f"COUNT={count_val}")

        return "RRULE:" + ";".join(parts)

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
    content: Mapped["Content | None"] = relationship(foreign_keys="[Activity.content_id]")

    # Schedule - embedded RRule composite (columns stored directly in activities table)
    start_dt: Mapped[datetime | None] = mapped_column(DateTime)
    end_dt: Mapped[datetime | None] = mapped_column(DateTime)
    
    # RRule fields (embedded as columns with schedule_ prefix)
    schedule_frequency: Mapped[str | None] = mapped_column(String(16), default="ONCE")
    schedule_interval: Mapped[int | None] = mapped_column(Integer, default=1)
    schedule_days: Mapped[list[int] | None] = mapped_column(ARRAY(Integer))
    schedule_setpos: Mapped[int | None] = mapped_column(Integer, default=0)
    schedule_count: Mapped[int | None] = mapped_column(Integer)

    schedule: Mapped[RRule | None] = composite(
        RRule,
        schedule_frequency,
        schedule_interval,
        schedule_days,
        schedule_setpos,
        schedule_count,
    )

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
    topics: Mapped[list["Topic"]] = relationship(secondary=activity_topics)

    capacity: Mapped[int | None] = mapped_column(Integer)

    registration_type: Mapped[str | None] = mapped_column( String(50) )  # enum: open, closed, waitlist, invite_only
    registrations: Mapped[list["Registration"]] = relationship(back_populates="activity")

    rsvps: Mapped[list["RSVP"]] = relationship(back_populates="activity")
    instructor_assignments: Mapped[list["InstructorAssignment"]] = relationship(
        back_populates="activity"
    )
    occurrences: Mapped[list["Occurrence"]] = relationship(back_populates="activity")
    flyers: Mapped[list["Flyer"]] = relationship(
        secondary=flyer_activities, back_populates="activities"
    )


class Occurrence(Base, TimestampMixin):
    """A specific time occurrence of an Activity."""

    __tablename__ = "occurrences"

    id: Mapped[int] = mapped_column(primary_key=True)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    rsvp_count: Mapped[int] = mapped_column(Integer, default=0)
    visitor_count: Mapped[int] = mapped_column(Integer, default=0)
    walk_in_count: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str | None] = mapped_column(Text)

    activity_id: Mapped[int] = mapped_column(ForeignKey("activities.id", ondelete="CASCADE"), nullable=False)

    # Relationships
    activity: Mapped["Activity"] = relationship(back_populates="occurrences")


class MarketingStats(Base, TimestampMixin):
    """Marketing statistics for events."""

    __tablename__ = "marketingstats"

    id: Mapped[int] = mapped_column(primary_key=True)
    walk_in_count: Mapped[int] = mapped_column(Integer, default=0)
    page_views: Mapped[int] = mapped_column(Integer, default=0)
    register_clicks: Mapped[int] = mapped_column(Integer, default=0)
    reference: Mapped[str | None] = mapped_column(String(255))  # optional external reference ID


class Registration(Base, TimestampMixin):
    """A registration for an event."""

    __tablename__ = "registrations"

    id: Mapped[int] = mapped_column(primary_key=True)
    registration_source: Mapped[str | None] = mapped_column(String(50))  # enum: web, phone, walk_in, partner
    utm_source: Mapped[str | None] = mapped_column(String(100))
    utm_campaign: Mapped[str | None] = mapped_column(String(100))
    notes: Mapped[str | None] = mapped_column(Text)

    event_id: Mapped[int] = mapped_column(ForeignKey("activities.id", ondelete="CASCADE"), nullable=False)
    registrant_id: Mapped[int] = mapped_column(ForeignKey("persons.id", ondelete="CASCADE"), nullable=False)

    # Relationships
    activity: Mapped["Activity"] = relationship(back_populates="registrations")
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
    activity: Mapped["Activity"] = relationship(back_populates="rsvps")
    visitor: Mapped["Visitor"] = relationship(
        back_populates="rsvps", foreign_keys=[visitor_id]
    )
    guardian: Mapped["Person | None"] = relationship(
        back_populates="guardian_rsvps", foreign_keys=[guardian_id]
    )



