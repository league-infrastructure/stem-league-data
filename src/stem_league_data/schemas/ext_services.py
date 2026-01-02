"""Schemas for External Service models: Meetup, Pike13Service, P13Location."""

from datetime import datetime
from typing import Any

from stem_league_data.schemas.base import BaseSchema, TimestampSchema


# Meetup Schemas
class MeetupBase(BaseSchema):
    """Base Meetup schema."""
    title: str | None = None
    date_time: datetime | None = None
    description: str | None = None
    event_url: str | None = None
    status: str | None = None
    meetup_slug: str | None = None
    group: str | None = None
    subgroup: str | None = None
    group_path: str | None = None
    venue_id: str | None = None
    venue_name: str | None = None
    venue_address: str | None = None
    photo_id: str | None = None
    photo_base_url: str | None = None
    title_font_size: str | None = None
    event_hosts: dict[str, Any] | None = None


class MeetupCreate(MeetupBase):
    """Schema for creating a Meetup."""
    id: str  # Meetup event ID


class MeetupUpdate(BaseSchema):
    """Schema for updating a Meetup."""
    title: str | None = None
    date_time: datetime | None = None
    description: str | None = None
    event_url: str | None = None
    status: str | None = None
    meetup_slug: str | None = None
    group: str | None = None
    subgroup: str | None = None
    group_path: str | None = None
    venue_id: str | None = None
    venue_name: str | None = None
    venue_address: str | None = None
    photo_id: str | None = None
    photo_base_url: str | None = None
    title_font_size: str | None = None
    event_hosts: dict[str, Any] | None = None


class MeetupResponse(MeetupBase, TimestampSchema):
    """Schema for Meetup response."""
    id: str


# Pike13Service Schemas
class Pike13ServiceBase(BaseSchema):
    """Base Pike13Service schema."""
    name: str | None = None
    type: str | None = None
    description: str | None = None
    description_short: str | None = None
    instructions: str | None = None
    category_name: str | None = None
    category_id: int | None = None
    category_slug: str | None = None
    price_string: str | None = None
    scheduled_events_count: int | None = None
    duration_in_minutes: int | None = None
    has_waitlist: bool | None = None
    allow_recurring: bool | None = None
    waitlist_only: bool | None = None


class Pike13ServiceCreate(Pike13ServiceBase):
    """Schema for creating a Pike13Service."""
    id: int  # Pike13 service ID (not auto-generated)


class Pike13ServiceUpdate(BaseSchema):
    """Schema for updating a Pike13Service."""
    name: str | None = None
    type: str | None = None
    description: str | None = None
    description_short: str | None = None
    instructions: str | None = None
    category_name: str | None = None
    category_id: int | None = None
    category_slug: str | None = None
    price_string: str | None = None
    scheduled_events_count: int | None = None
    duration_in_minutes: int | None = None
    has_waitlist: bool | None = None
    allow_recurring: bool | None = None
    waitlist_only: bool | None = None


class Pike13ServiceResponse(Pike13ServiceBase, TimestampSchema):
    """Schema for Pike13Service response."""
    id: int


# P13Location Schemas
class P13LocationBase(BaseSchema):
    """Base P13Location schema."""
    code: str | None = None
    name: str | None = None
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    phone: str | None = None
    description: str | None = None
    slug: str | None = None
    position: int | None = None
    hidden_at: datetime | None = None
    formatted_address: str | None = None
    street_address: str | None = None
    street_address2: str | None = None
    city: str | None = None
    state_code: str | None = None
    postal_code: str | None = None
    country_code: str | None = None
    timezone_friendly: str | None = None
    timezone: str | None = None
    type: str | None = None


class P13LocationCreate(P13LocationBase):
    """Schema for creating a P13Location."""
    id: int  # Pike13 location ID (not auto-generated)


class P13LocationUpdate(BaseSchema):
    """Schema for updating a P13Location."""
    code: str | None = None
    name: str | None = None
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    phone: str | None = None
    description: str | None = None
    slug: str | None = None
    position: int | None = None
    hidden_at: datetime | None = None
    formatted_address: str | None = None
    street_address: str | None = None
    street_address2: str | None = None
    city: str | None = None
    state_code: str | None = None
    postal_code: str | None = None
    country_code: str | None = None
    timezone_friendly: str | None = None
    timezone: str | None = None
    type: str | None = None


class P13LocationResponse(P13LocationBase, TimestampSchema):
    """Schema for P13Location response."""
    id: int
