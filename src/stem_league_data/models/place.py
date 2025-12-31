"""Place-related models: Metro, Venue, Org, Flyer."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text, Integer, Boolean, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship

from stem_league_data.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from stem_league_data.models.people import Person
    from stem_league_data.models.events import Activity
    from stem_league_data.models.jobs import JobPosting


class Metro(Base, TimestampMixin):
    """A metropolitan area where League operates."""

    __tablename__ = "metros"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    short_url_domain: Mapped[str | None] = mapped_column(String(255))

    timezone: Mapped[str | None] = mapped_column(String(100))

    # Relationships
    venues: Mapped[list["Venue"]] = relationship(back_populates="metro")
    orgs: Mapped[list["Org"]] = relationship(back_populates="metro")
    persons: Mapped[list["Person"]] = relationship(back_populates="metro")
    job_postings: Mapped[list["JobPosting"]] = relationship(back_populates="metro")


class Org(Base, TimestampMixin):
    """An organization that can host or deliver events."""

    __tablename__ = "orgs"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    org_type: Mapped[str | None] = mapped_column(String(50))  # enum: school, company, nonprofit, etc.
    website: Mapped[str | None] = mapped_column(String(500))
    contact_email: Mapped[str | None] = mapped_column(String(255))
    can_deliver_events: Mapped[bool] = mapped_column(Boolean, default=False)
    can_host_events: Mapped[bool] = mapped_column(Boolean, default=False)

    metro_id: Mapped[int] = mapped_column(ForeignKey("metros.id", ondelete="RESTRICT"), nullable=False)

    # Relationships
    metro: Mapped["Metro"] = relationship(back_populates="orgs")
    venues: Mapped[list["Venue"]] = relationship(back_populates="org")
    events: Mapped[list["Activity"]] = relationship(back_populates="org")
    job_postings: Mapped[list["JobPosting"]] = relationship(back_populates="org")


class Venue(Base, TimestampMixin):
    """A physical location where events can be held."""

    __tablename__ = "venues"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str | None] = mapped_column(String(500))
    parking_instructions: Mapped[str | None] = mapped_column(Text)
    building_entry_instructions: Mapped[str | None] = mapped_column(Text)
    capacity: Mapped[int | None] = mapped_column(Integer)
    has_computers: Mapped[bool] = mapped_column(Boolean, default=False)

    metro_id: Mapped[int] = mapped_column(ForeignKey("metros.id", ondelete="CASCADE"), nullable=False)
    org_id: Mapped[int | None] = mapped_column(ForeignKey("orgs.id", ondelete="SET NULL"))

    # Relationships
    metro: Mapped["Metro"] = relationship(back_populates="venues")
    org: Mapped["Org | None"] = relationship(back_populates="venues")
    events: Mapped[list["Activity"]] = relationship(back_populates="venue")


class Flyer(Base, TimestampMixin):
    """A marketing flyer for events."""

    __tablename__ = "flyers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    distribution_date: Mapped[Date | None] = mapped_column(Date)
    distribution_count: Mapped[int | None] = mapped_column(Integer)
    design_file: Mapped[str | None] = mapped_column(String(500))  # media URL
    utm_source: Mapped[str | None] = mapped_column(String(100))
    utm_campaign: Mapped[str | None] = mapped_column(String(100))
    total_reach: Mapped[int | None] = mapped_column(Integer)

    # Many-to-many with Activity defined in events.py
    events: Mapped[list["Activity"]] = relationship(
        secondary="flyer_events", back_populates="flyers"
    )
