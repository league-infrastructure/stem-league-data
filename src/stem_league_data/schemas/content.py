"""Schemas for Content models: Content, Announcement."""

from datetime import datetime
from typing import Any

from stem_league_data.schemas.base import BaseSchema, TimestampSchema


# Content Schemas
class ContentBase(BaseSchema):
    """Base Content schema."""
    title: str | None = None
    eyebrow: str | None = None
    label: str | None = None
    blurb: str | None = None
    description: str | None = None
    body: str | None = None
    instructions: str | None = None
    other_content: dict[str, Any] | None = None
    image: str | None = None
    link: str | None = None
    source: str | None = None
    for_: str | None = None
    rank: int | None = None
    renderer: str | None = None
    comment: str | None = None
    type: str | None = None
    data: dict[str, Any] | None = None


class ContentCreate(ContentBase):
    """Schema for creating Content."""
    content_type: str = "content"


class ContentUpdate(BaseSchema):
    """Schema for updating Content."""
    title: str | None = None
    eyebrow: str | None = None
    label: str | None = None
    blurb: str | None = None
    description: str | None = None
    body: str | None = None
    instructions: str | None = None
    other_content: dict[str, Any] | None = None
    image: str | None = None
    link: str | None = None
    source: str | None = None
    for_: str | None = None
    rank: int | None = None
    renderer: str | None = None
    comment: str | None = None
    type: str | None = None
    data: dict[str, Any] | None = None


class ContentResponse(ContentBase, TimestampSchema):
    """Schema for Content response."""
    id: int
    content_type: str


# Announcement Schemas
class AnnouncementBase(BaseSchema):
    """Base Announcement schema."""
    from_date: datetime | None = None
    until_date: datetime | None = None


class AnnouncementCreate(AnnouncementBase):
    """Schema for creating an Announcement."""
    content_id: int | None = None
    # Optionally create content inline
    content: ContentCreate | None = None


class AnnouncementUpdate(BaseSchema):
    """Schema for updating an Announcement."""
    from_date: datetime | None = None
    until_date: datetime | None = None
    content_id: int | None = None


class AnnouncementResponse(AnnouncementBase, TimestampSchema):
    """Schema for Announcement response."""
    id: int
    content_id: int | None = None
    content: ContentResponse | None = None
