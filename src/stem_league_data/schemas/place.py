"""Schemas for Place models: Metro, Org, Venue, Flyer."""

from datetime import date

from pydantic import Field

from stem_league_data.schemas.base import BaseSchema, TimestampSchema


# Metro Schemas
class MetroBase(BaseSchema):
    """Base Metro schema."""
    name: str
    slug: str
    short_url_domain: str | None = None
    timezone: str | None = None


class MetroCreate(MetroBase):
    """Schema for creating a Metro."""
    pass


class MetroUpdate(BaseSchema):
    """Schema for updating a Metro."""
    name: str | None = None
    slug: str | None = None
    short_url_domain: str | None = None
    timezone: str | None = None


class MetroResponse(MetroBase, TimestampSchema):
    """Schema for Metro response."""
    id: int


# Org Schemas
class OrgBase(BaseSchema):
    """Base Org schema."""
    name: str
    org_type: str | None = None
    website: str | None = None
    contact_email: str | None = None
    can_deliver_events: bool = False
    can_host_events: bool = False


class OrgCreate(OrgBase):
    """Schema for creating an Org."""
    metro_id: int


class OrgUpdate(BaseSchema):
    """Schema for updating an Org."""
    name: str | None = None
    org_type: str | None = None
    website: str | None = None
    contact_email: str | None = None
    can_deliver_events: bool | None = None
    can_host_events: bool | None = None
    metro_id: int | None = None


class OrgResponse(OrgBase, TimestampSchema):
    """Schema for Org response."""
    id: int
    metro_id: int


# Venue Schemas
class VenueBase(BaseSchema):
    """Base Venue schema."""
    name: str
    address: str | None = None
    parking_instructions: str | None = None
    building_entry_instructions: str | None = None
    capacity: int | None = None
    has_computers: bool = False


class VenueCreate(VenueBase):
    """Schema for creating a Venue."""
    metro_id: int
    org_id: int | None = None


class VenueUpdate(BaseSchema):
    """Schema for updating a Venue."""
    name: str | None = None
    address: str | None = None
    parking_instructions: str | None = None
    building_entry_instructions: str | None = None
    capacity: int | None = None
    has_computers: bool | None = None
    metro_id: int | None = None
    org_id: int | None = None


class VenueResponse(VenueBase, TimestampSchema):
    """Schema for Venue response."""
    id: int
    metro_id: int
    org_id: int | None = None


# Flyer Schemas
class FlyerBase(BaseSchema):
    """Base Flyer schema."""
    name: str
    distribution_date: date | None = None
    distribution_count: int | None = None
    design_file: str | None = None
    utm_source: str | None = None
    utm_campaign: str | None = None
    total_reach: int | None = None


class FlyerCreate(FlyerBase):
    """Schema for creating a Flyer."""
    pass


class FlyerUpdate(BaseSchema):
    """Schema for updating a Flyer."""
    name: str | None = None
    distribution_date: date | None = None
    distribution_count: int | None = None
    design_file: str | None = None
    utm_source: str | None = None
    utm_campaign: str | None = None
    total_reach: int | None = None


class FlyerResponse(FlyerBase, TimestampSchema):
    """Schema for Flyer response."""
    id: int
