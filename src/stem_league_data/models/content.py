"""Content-related models: Content, Page, Class, Enrollment, CTA, Announcement."""

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, String, Text, Boolean, Table, Column, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from stem_league_data.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    pass


class Content(Base, TimestampMixin):
    """Base content model with common fields."""

    __tablename__ = "contents"

    id: Mapped[int] = mapped_column(primary_key=True)

    title: Mapped[str | None] = mapped_column(String(255))
    eyebrow: Mapped[str | None] = mapped_column(Text)
    label: Mapped[str | None] = mapped_column(Text)
    blurb: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)

    body: Mapped[str | None] = mapped_column(Text)
    instructions: Mapped[str | None] = mapped_column(Text)
    other_content: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    image: Mapped[str | None] = mapped_column(String(500))
    link: Mapped[str | None] = mapped_column(Text)

    source: Mapped[str | None] = mapped_column(String(255))
    for_: Mapped[str | None] = mapped_column("for", String(255))  # 'for' is reserved
    rank: Mapped[int | None] = mapped_column()
    renderer: Mapped[str | None] = mapped_column(String(255)) # Component name for rendering or display
    comment: Mapped[str | None] = mapped_column(Text)
    type: Mapped[str | None] = mapped_column(Text) # Specialization type within content

    data: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    content_type: Mapped[str] = mapped_column(String(50), nullable=False)  # discriminator

    __mapper_args__ = {
        "polymorphic_on": "content_type",
        "polymorphic_identity": "content",
    }


class Page(Content):
    """A page of content."""

    __mapper_args__ = {
        "polymorphic_identity": "page",
    }


class Announcement(Base, TimestampMixin):
    """An announcement with date range."""

    __tablename__ = "announcements"

    id: Mapped[int] = mapped_column(primary_key=True)
    from_date: Mapped[datetime | None] = mapped_column("from", DateTime)  # 'from' is reserved
    until_date: Mapped[datetime | None] = mapped_column(DateTime)

    content_id: Mapped[int | None] = mapped_column(ForeignKey("contents.id", ondelete="SET NULL"))
    content: Mapped["Content | None"] = relationship()
