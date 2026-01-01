"""External service integration models: Meetup, Pike13Service, P13Location."""

from datetime import datetime

from sqlalchemy import String, Text, Integer, Float, DateTime, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from stem_league_data.models.base import Base, TimestampMixin


class Meetup(Base, TimestampMixin):
    """A Meetup.com event record from past_meetups.json."""

    __tablename__ = "meetups"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)  # Meetup event ID (e.g., "312112859")
    title: Mapped[str | None] = mapped_column(String(500))
    date_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    description: Mapped[str | None] = mapped_column(Text)
    event_url: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str | None] = mapped_column(String(50))  # e.g., "PAST"
    meetup_slug: Mapped[str | None] = mapped_column(String(255))  # e.g., "the-league-tech-club"
    group: Mapped[str | None] = mapped_column(String(255))  # e.g., "tech-club"
    subgroup: Mapped[str | None] = mapped_column(String(255))  # e.g., "video_game", "robot", "brain"
    group_path: Mapped[str | None] = mapped_column(String(255))  # e.g., "tech-club/video_game"
    
    # Venue info (flattened from nested venue object)
    venue_id: Mapped[str | None] = mapped_column(String(50))
    venue_name: Mapped[str | None] = mapped_column(String(255))
    venue_address: Mapped[str | None] = mapped_column(String(500))
    
    # Photo info
    photo_id: Mapped[str | None] = mapped_column(String(50))
    photo_base_url: Mapped[str | None] = mapped_column(String(500))
    
    # Display hint
    title_font_size: Mapped[str | None] = mapped_column(String(20))
    
    # Store event hosts as JSON
    event_hosts: Mapped[dict | None] = mapped_column(JSONB)


class Pike13Service(Base, TimestampMixin):
    """A Pike13 service/class integration."""

    __tablename__ = "pike13_services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    name: Mapped[str | None] = mapped_column(String(255))
    type: Mapped[str | None] = mapped_column(String(100))  # e.g., "Appointment", "GroupClass"
    description: Mapped[str | None] = mapped_column(Text)
    description_short: Mapped[str | None] = mapped_column(String(500))
    instructions: Mapped[str | None] = mapped_column(Text)
    category_name: Mapped[str | None] = mapped_column(String(255))
    category_id: Mapped[int | None] = mapped_column(Integer)
    category_slug: Mapped[str | None] = mapped_column(String(255))
    price_string: Mapped[str | None] = mapped_column(String(100))
    scheduled_events_count: Mapped[int | None] = mapped_column(Integer)
    duration_in_minutes: Mapped[int | None] = mapped_column(Integer)
    has_waitlist: Mapped[bool | None] = mapped_column()
    allow_recurring: Mapped[bool | None] = mapped_column()
    waitlist_only: Mapped[bool | None] = mapped_column()


class P13Location(Base, TimestampMixin):
    """A Pike13 location."""

    __tablename__ = "p13_locations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    code: Mapped[str | None] = mapped_column(String(50), unique=True)
    name: Mapped[str | None] = mapped_column(String(255))
    address: Mapped[str | None] = mapped_column(String(500))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    phone: Mapped[str | None] = mapped_column(String(50))
    description: Mapped[str | None] = mapped_column(Text)
    slug: Mapped[str | None] = mapped_column(String(255))
    position: Mapped[int | None] = mapped_column(Integer)
    hidden_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    formatted_address: Mapped[str | None] = mapped_column(String(500))
    street_address: Mapped[str | None] = mapped_column(String(255))
    street_address2: Mapped[str | None] = mapped_column(String(255))
    city: Mapped[str | None] = mapped_column(String(100))
    state_code: Mapped[str | None] = mapped_column(String(10))
    postal_code: Mapped[str | None] = mapped_column(String(20))
    country_code: Mapped[str | None] = mapped_column(String(10))
    timezone_friendly: Mapped[str | None] = mapped_column(String(100))
    timezone: Mapped[str | None] = mapped_column(String(100))
    type: Mapped[str | None] = mapped_column(String(50))
