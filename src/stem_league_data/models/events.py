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

    Supported scheduling patterns:

    1. **MANUAL** (frequency=None): No automatic scheduling. Occurrences are
       created manually. Use when events happen at irregular times.

    2. **ONCE** (frequency="ONCE"): Single occurrence. The Activity's start_dt
       defines when it happens. No recurrence rule is generated.

    3. **WEEKLY** (frequency="WEEKLY"): Recurring weekly on specific days.
       - days: list of weekdays (Mon=0..Sun=6), e.g., [2, 4] for Wed/Fri
       - interval: every N weeks (default 1)
       - count: total number of occurrences (optional)

    4. **MONTHLY** (frequency="MONTHLY"): Recurring monthly on Nth weekday.
       - days: exactly one weekday, e.g., [1] for Tuesday
       - setpos: which occurrence (1-5 for 1st-5th, -1 for last)
       - interval: every N months (default 1)
       - count: total number of occurrences (optional)

    Weekday numbering: Mon=0, Tue=1, Wed=2, Thu=3, Fri=4, Sat=5, Sun=6

    Date/time fields:
    - start_dt: First occurrence start datetime (includes time of day)
    - end_dt: Series end date (occurrences stop after this date)
    """

    # Valid frequency values
    MANUAL = None
    ONCE = "ONCE"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"

    _VALID_FREQUENCIES = {None, "ONCE", "WEEKLY", "MONTHLY"}
    _WKDAY_TOKENS = ("MO", "TU", "WE", "TH", "FR", "SA", "SU")
    _WKDAY_NAMES = ("Monday", "Tuesday", "Wednesday", "Thursday",
                    "Friday", "Saturday", "Sunday")

    def __init__(
        self,
        frequency: str | None = None,
        interval: int | None = 1,
        days: list[int] | None = None,
        setpos: int | None = None,
        count: int | None = None,
        start_dt: datetime | None = None,
        end_dt: datetime | None = None,
    ):
        self.frequency = frequency
        self.interval = interval if interval is not None else 1
        self.days = days
        self.setpos = setpos
        self.count = count
        self.start_dt = start_dt
        self.end_dt = end_dt

    # --- Factory methods for common patterns ---

    @classmethod
    def manual(
        cls,
        start_dt: datetime | None = None,
        end_dt: datetime | None = None,
    ) -> "RRule":
        """Create a manual schedule (no automatic occurrence generation)."""
        return cls(frequency=None, start_dt=start_dt, end_dt=end_dt)

    @classmethod
    def once(
        cls,
        start_dt: datetime | None = None,
        end_dt: datetime | None = None,
    ) -> "RRule":
        """Create a single-occurrence schedule.
        
        Args:
            start_dt: When the single occurrence starts.
            end_dt: When the single occurrence ends.
        """
        return cls(frequency="ONCE", start_dt=start_dt, end_dt=end_dt)

    @classmethod
    def weekly(
        cls,
        days: list[int],
        interval: int = 1,
        count: int | None = None,
        start_dt: datetime | None = None,
        end_dt: datetime | None = None,
    ) -> "RRule":
        """Create a weekly recurring schedule.

        Args:
            days: Weekdays to recur on (Mon=0..Sun=6). E.g., [2, 4] for Wed/Fri.
            interval: Every N weeks (default 1).
            count: Total number of occurrences (optional).
            start_dt: First occurrence start datetime.
            end_dt: Series end date (occurrences stop after this).

        Example:
            RRule.weekly([2, 4])  # Every Wednesday and Friday
            RRule.weekly([0], interval=2, count=10)  # Every other Monday, 10 times
        """
        return cls(
            frequency="WEEKLY", days=days, interval=interval, count=count,
            start_dt=start_dt, end_dt=end_dt,
        )

    @classmethod
    def monthly_weekday(
        cls,
        weekday: int,
        week: int,
        interval: int = 1,
        count: int | None = None,
        start_dt: datetime | None = None,
        end_dt: datetime | None = None,
    ) -> "RRule":
        """Create a monthly recurring schedule on Nth weekday.

        Args:
            weekday: Day of week (Mon=0..Sun=6).
            week: Which week (1-5 for 1st-5th, -1 for last).
            interval: Every N months (default 1).
            count: Total number of occurrences (optional).
            start_dt: First occurrence start datetime.
            end_dt: Series end date (occurrences stop after this).

        Example:
            RRule.monthly_weekday(1, 4)  # 4th Tuesday of each month
            RRule.monthly_weekday(5, -1)  # Last Saturday of each month
        """
        return cls(
            frequency="MONTHLY",
            days=[weekday],
            setpos=week,
            interval=interval,
            count=count,
            start_dt=start_dt,
            end_dt=end_dt,
        )

    # --- Composite protocol ---

    def __composite_values__(self):
        return (self.frequency, self.interval, self.days, self.setpos, 
                self.count, self.start_dt, self.end_dt)

    def __repr__(self):
        if self.frequency is None:
            return "RRule.manual()"
        if self.frequency == "ONCE":
            return "RRule.once()"
        return (
            f"RRule(frequency={self.frequency!r}, interval={self.interval}, "
            f"days={self.days}, setpos={self.setpos}, count={self.count}, "
            f"start_dt={self.start_dt!r}, end_dt={self.end_dt!r})"
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
            and self.start_dt == other.start_dt
            and self.end_dt == other.end_dt
        )

    def __ne__(self, other):
        return not self.__eq__(other)

    # --- Validation ---

    def validate(self) -> list[str]:
        """Validate the RRule and return a list of error messages.

        Returns an empty list if valid.
        """
        errors: list[str] = []

        # Check frequency
        freq = self.frequency
        if freq is not None:
            freq = freq.upper() if isinstance(freq, str) else freq
        if freq not in self._VALID_FREQUENCIES:
            errors.append(
                f"Invalid frequency '{self.frequency}'. "
                f"Must be one of: None (manual), 'ONCE', 'WEEKLY', 'MONTHLY'."
            )
            return errors  # Can't validate further with invalid frequency

        # MANUAL: all other fields should be empty/default
        if freq is None:
            if self.days:
                errors.append("Manual schedule should not specify days.")
            if self.setpos:
                errors.append("Manual schedule should not specify setpos.")
            if self.count:
                errors.append("Manual schedule should not specify count.")
            return errors

        # ONCE: minimal specification
        if freq == "ONCE":
            if self.days:
                errors.append("Single occurrence should not specify days.")
            if self.setpos:
                errors.append("Single occurrence should not specify setpos.")
            # count is ignored for ONCE
            return errors

        # Validate interval (applies to WEEKLY and MONTHLY)
        if self.interval is not None and self.interval < 1:
            errors.append("Interval must be >= 1.")

        # Validate days array
        if self.days:
            for d in self.days:
                if not isinstance(d, int) or d < 0 or d > 6:
                    errors.append(
                        f"Invalid weekday {d}. Must be integer 0-6 (Mon-Sun)."
                    )

        # Validate count
        if self.count is not None and self.count < 1:
            errors.append("Count must be >= 1.")

        # WEEKLY validation
        if freq == "WEEKLY":
            if not self.days:
                errors.append(
                    "Weekly schedule requires at least one day. "
                    "Use days=[0] for Monday, days=[2,4] for Wed/Fri, etc."
                )
            if self.setpos:
                errors.append("Weekly schedule should not specify setpos.")

        # MONTHLY validation
        if freq == "MONTHLY":
            if not self.days or len(self.days) != 1:
                errors.append(
                    "Monthly schedule requires exactly one weekday. "
                    "Use days=[1] for Tuesday, etc."
                )
            if not self.setpos or self.setpos == 0:
                errors.append(
                    "Monthly schedule requires setpos (which week). "
                    "Use 1-5 for 1st-5th occurrence, or -1 for last."
                )
            elif self.setpos not in {1, 2, 3, 4, 5, -1}:
                errors.append(
                    f"Invalid setpos {self.setpos}. "
                    "Must be 1-5 (1st-5th) or -1 (last)."
                )

        return errors

    def is_valid(self) -> bool:
        """Return True if the RRule is valid."""
        return len(self.validate()) == 0

    def raise_if_invalid(self) -> None:
        """Raise ValueError if the RRule is invalid."""
        errors = self.validate()
        if errors:
            raise ValueError("Invalid RRule: " + "; ".join(errors))

    # --- Human-readable description ---

    def describe(self) -> str:
        """Return a human-readable description of the schedule."""
        if self.frequency is None:
            return "Manual scheduling (no automatic occurrences)"

        if self.frequency == "ONCE":
            return "Single occurrence"

        if self.frequency == "WEEKLY":
            day_names = [self._WKDAY_NAMES[d] for d in (self.days or [])]
            days_str = ", ".join(day_names) if day_names else "no days specified"
            interval_str = (
                "every week" if self.interval == 1
                else f"every {self.interval} weeks"
            )
            count_str = f" ({self.count} times)" if self.count else ""
            return f"Weekly on {days_str}, {interval_str}{count_str}"

        if self.frequency == "MONTHLY":
            day_name = (
                self._WKDAY_NAMES[self.days[0]] if self.days else "unspecified day"
            )
            week_names = {1: "1st", 2: "2nd", 3: "3rd", 4: "4th", 5: "5th", -1: "last"}
            week_str = week_names.get(self.setpos, f"#{self.setpos}")
            interval_str = (
                "every month" if self.interval == 1
                else f"every {self.interval} months"
            )
            count_str = f" ({self.count} times)" if self.count else ""
            return f"{week_str} {day_name} of {interval_str}{count_str}"

        return f"Unknown frequency: {self.frequency}"

    # --- RRULE serialization ---

    def to_ical_rrule(self) -> str | None:
        """Return an iCalendar RRULE string, or None for ONCE/MANUAL.

        Raises ValueError if the rule is invalid.

        Examples:
            - WEEKLY on Wed/Fri for 6 occurrences:
              RRULE:FREQ=WEEKLY;INTERVAL=1;BYDAY=WE,FR;COUNT=6

            - MONTHLY on the 4th Tuesday:
              RRULE:FREQ=MONTHLY;INTERVAL=1;BYDAY=TU;BYSETPOS=4
        """
        self.raise_if_invalid()

        freq = (self.frequency or "").upper() if self.frequency else None

        if freq is None or freq == "ONCE":
            return None

        interval = self.interval or 1
        parts: list[str] = [f"FREQ={freq}", f"INTERVAL={interval}"]

        # Map weekdays to iCal tokens
        if self.days:
            tokens = [self._WKDAY_TOKENS[d] for d in self.days]
            parts.append("BYDAY=" + ",".join(tokens))

        if freq == "MONTHLY" and self.setpos:
            parts.append(f"BYSETPOS={self.setpos}")

        if self.count is not None:
            parts.append(f"COUNT={self.count}")

        return "RRULE:" + ";".join(parts)


class Activity(Base, TimestampMixin):
    """An Activity is an instance of an Service that is scheduled. It can be a
    Class (series of dates), an Event (single date), or an appointment (scheduled
    slots, but must be booked to actually be on a schedule)."""

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
    # RRule fields include start_dt, end_dt, frequency, interval, days, setpos, count
    start_dt: Mapped[datetime | None] = mapped_column(DateTime)
    end_dt: Mapped[datetime | None] = mapped_column(DateTime)

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
        start_dt,
        end_dt,
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



