"""External service integration models: Meetup, Pike13Service, P13Location."""

from datetime import datetime

from sqlalchemy import String, Text, Integer, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from stem_league_data.models.base import Base, TimestampMixin


class Meetup(Base, TimestampMixin):
    """A Meetup.com event integration."""

    __tablename__ = "meetups"

    slug: Mapped[str] = mapped_column(String(255), primary_key=True)
    meetup_slug: Mapped[str | None] = mapped_column(String(255))
    group: Mapped[str | None] = mapped_column(String(255))
    subgroup: Mapped[str | None] = mapped_column(String(255))
    emoji: Mapped[str | None] = mapped_column(String(50))
    event_url: Mapped[str | None] = mapped_column(String(500))


class Pike13Service(Base, TimestampMixin):
    """A Pike13 service/class integration."""

    __tablename__ = "pike13_services"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    name: Mapped[str | None] = mapped_column(String(255))
    type: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    description_short: Mapped[str | None] = mapped_column(String(500))
    instructions: Mapped[str | None] = mapped_column(Text)
    category_name: Mapped[str | None] = mapped_column(String(255))
    category_id: Mapped[int | None] = mapped_column(Integer)
    category_slug: Mapped[str | None] = mapped_column(String(255))
    price_string: Mapped[str | None] = mapped_column(String(100))
    scheduled_events_count: Mapped[int | None] = mapped_column(Integer)


class P13Location(Base, TimestampMixin):
    """A Pike13 location."""

    __tablename__ = "p13_locations"

    code: Mapped[str] = mapped_column(String(50), primary_key=True)
    id: Mapped[str | None] = mapped_column(String(100))
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
