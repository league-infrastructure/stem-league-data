"""Schemas for Event models: Service, Activity, Occurrence, Registration, RSVP."""

import json
from datetime import datetime
from typing import Any

from pydantic import Field, field_validator

from stem_league_data.schemas.base import BaseSchema, TimestampSchema
from stem_league_data.schemas.content import ContentCreate, ContentResponse


# RRule Schema for scheduling
class RRuleSchema(BaseSchema):
    """Schema for recurrence rules."""
    frequency: str | None = None  # None (manual), ONCE, WEEKLY, MONTHLY
    interval: int = 1
    days: list[int] | None = None  # 0=Mon, 6=Sun
    setpos: int | None = None  # For MONTHLY: 1-5 or -1 (last)
    count: int | None = None


# Service Schemas
class ServiceBase(BaseSchema):
    """Base Service schema."""
    slug: str
    grade: str | None = None
    level: str | None = None
    curriculum_link: str | None = None


class ServiceCreate(ServiceBase):
    """Schema for creating a Service."""
    content_id: int | None = None
    content: ContentCreate | None = None  # Create content inline
    pike13_service_id: int | None = None
    parent_service_id: int | None = None
    # Many-to-many relationships (by ID)
    topic_ids: list[int] | None = None
    track_ids: list[int] | None = None
    category_ids: list[int] | None = None
    subcategory_ids: list[int] | None = None


class ServiceUpdate(BaseSchema):
    """Schema for updating a Service."""
    slug: str | None = None
    grade: str | None = None
    level: str | None = None
    curriculum_link: str | None = None
    content_id: int | None = None
    pike13_service_id: int | None = None
    parent_service_id: int | None = None
    topic_ids: list[int] | None = None
    track_ids: list[int] | None = None
    category_ids: list[int] | None = None
    subcategory_ids: list[int] | None = None


class ServiceResponse(ServiceBase, TimestampSchema):
    """Schema for Service response."""
    id: int
    content_id: int | None = None
    content: ContentResponse | None = None
    pike13_service_id: int | None = None
    parent_service_id: int | None = None


# Activity Schemas
class ActivityBase(BaseSchema):
    """Base Activity schema."""
    type: str | None = None  # class, course, event, appointment
    status: str | None = None  # draft, published, cancelled, completed
    active: bool = True
    capacity: int | None = None
    registration_type: str | None = None  # open, closed, waitlist, invite_only
    schedule_link: str | None = None


class ActivityCreate(ActivityBase):
    """Schema for creating an Activity."""
    service_id: int | None = None
    service: ServiceCreate | None = None  # Create service inline
    content_id: int | None = None
    content: ContentCreate | None = None  # Create content inline
    venue_id: int
    org_id: int | None = None
    enrollment_opens: datetime | None = None
    enrollment_closes: datetime | None = None
    enrollment_id: int | None = None
    cta_id: int | None = None
    # Schedule fields
    start_dt: datetime | None = None
    end_dt: datetime | None = None
    schedule: RRuleSchema | None = None
    # Many-to-many relationships (by ID)
    program_ids: list[int] | None = None
    track_ids: list[int] | None = None
    category_ids: list[int] | None = None
    subcategory_ids: list[int] | None = None
    topic_ids: list[int] | None = None
    tag_ids: list[int] | None = None


class ActivityUpdate(BaseSchema):
    """Schema for updating an Activity."""
    type: str | None = None
    status: str | None = None
    active: bool | None = None
    capacity: int | None = None
    registration_type: str | None = None
    schedule_link: str | None = None
    service_id: int | None = None
    content_id: int | None = None
    venue_id: int | None = None
    org_id: int | None = None
    enrollment_opens: datetime | None = None
    enrollment_closes: datetime | None = None
    enrollment_id: int | None = None
    cta_id: int | None = None
    start_dt: datetime | None = None
    end_dt: datetime | None = None
    schedule: RRuleSchema | None = None
    program_ids: list[int] | None = None
    track_ids: list[int] | None = None
    category_ids: list[int] | None = None
    subcategory_ids: list[int] | None = None
    topic_ids: list[int] | None = None
    tag_ids: list[int] | None = None


class ActivityResponse(ActivityBase, TimestampSchema):
    """Schema for Activity response."""
    id: int
    service_id: int | None = None
    content_id: int | None = None
    venue_id: int
    org_id: int | None = None
    enrollment_opens: datetime | None = None
    enrollment_closes: datetime | None = None
    enrollment_id: int | None = None
    cta_id: int | None = None
    start_dt: datetime | None = None
    end_dt: datetime | None = None
    schedule_frequency: str | None = None
    schedule_interval: int | None = None
    schedule_days: list[int] | None = None
    schedule_setpos: int | None = None
    schedule_count: int | None = None

    @field_validator("schedule_days", mode="before")
    @classmethod
    def parse_schedule_days(cls, v: Any) -> list[int] | None:
        """Handle ARRAY stored as JSON string in SQLite or corrupted ['n','u','l','l'] data."""
        if v is None:
            return None
        # Handle SQLite ARRAY corruption: ['n','u','l','l'] from "null" string
        if isinstance(v, list) and v == ['n', 'u', 'l', 'l']:
            return None
        if isinstance(v, str):
            if v == "null" or v.lower() == "none":
                return None
            try:
                parsed = json.loads(v)
                return parsed if isinstance(parsed, list) else None
            except (json.JSONDecodeError, TypeError):
                return None
        if isinstance(v, list):
            # Ensure all elements are ints
            try:
                return [int(x) for x in v]
            except (ValueError, TypeError):
                return None
        return None


# Occurrence Schemas
class OccurrenceBase(BaseSchema):
    """Base Occurrence schema."""
    start_time: datetime
    end_time: datetime
    rsvp_count: int = 0
    visitor_count: int = 0
    walk_in_count: int = 0
    notes: str | None = None


class OccurrenceCreate(OccurrenceBase):
    """Schema for creating an Occurrence."""
    activity_id: int


class OccurrenceUpdate(BaseSchema):
    """Schema for updating an Occurrence."""
    start_time: datetime | None = None
    end_time: datetime | None = None
    rsvp_count: int | None = None
    visitor_count: int | None = None
    walk_in_count: int | None = None
    notes: str | None = None


class OccurrenceResponse(OccurrenceBase, TimestampSchema):
    """Schema for Occurrence response."""
    id: int
    activity_id: int


# Registration Schemas
class RegistrationBase(BaseSchema):
    """Base Registration schema."""
    registration_source: str | None = None  # web, phone, walk_in, partner
    utm_source: str | None = None
    utm_campaign: str | None = None
    notes: str | None = None


class RegistrationCreate(RegistrationBase):
    """Schema for creating a Registration."""
    event_id: int
    registrant_id: int


class RegistrationUpdate(BaseSchema):
    """Schema for updating a Registration."""
    registration_source: str | None = None
    utm_source: str | None = None
    utm_campaign: str | None = None
    notes: str | None = None


class RegistrationResponse(RegistrationBase, TimestampSchema):
    """Schema for Registration response."""
    id: int
    event_id: int
    registrant_id: int


# RSVP Schemas
class RSVPBase(BaseSchema):
    """Base RSVP schema."""
    role: str | None = None  # student, chaperone, volunteer
    visitor_relationship: str | None = None  # self, parent, guardian, sibling
    attended: bool = False
    checked_in_at: datetime | None = None
    notes: str | None = None


class RSVPCreate(RSVPBase):
    """Schema for creating an RSVP."""
    registration_id: int
    event_id: int
    visitor_id: int
    guardian_id: int | None = None


class RSVPUpdate(BaseSchema):
    """Schema for updating an RSVP."""
    role: str | None = None
    visitor_relationship: str | None = None
    attended: bool | None = None
    checked_in_at: datetime | None = None
    notes: str | None = None
    guardian_id: int | None = None


class RSVPResponse(RSVPBase, TimestampSchema):
    """Schema for RSVP response."""
    id: int
    registration_id: int
    event_id: int
    visitor_id: int
    guardian_id: int | None = None
