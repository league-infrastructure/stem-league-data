"""Content-related models: Content, Page, Class, Enrollment, CTA, Announcement."""

from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, String, Text, Boolean, Table, Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from stem_league_data.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from stem_league_data.models.categories import Category, Topic


# Association tables
class_categories = Table(
    "class_categories",
    Base.metadata,
    Column("class_slug", ForeignKey("classes.slug", ondelete="CASCADE"), primary_key=True),
    Column("category_slug", ForeignKey("groups.slug", ondelete="CASCADE"), primary_key=True),
)

class_topics = Table(
    "class_topics",
    Base.metadata,
    Column("class_slug", ForeignKey("classes.slug", ondelete="CASCADE"), primary_key=True),
    Column("topic_slug", ForeignKey("groups.slug", ondelete="CASCADE"), primary_key=True),
)

class_ctas = Table(
    "class_ctas",
    Base.metadata,
    Column("class_slug", ForeignKey("classes.slug", ondelete="CASCADE"), primary_key=True),
    Column("cta_slug", ForeignKey("ctas.slug", ondelete="CASCADE"), primary_key=True),
)

class_enrollments = Table(
    "class_enrollments",
    Base.metadata,
    Column("class_slug", ForeignKey("classes.slug", ondelete="CASCADE"), primary_key=True),
    Column("enrollment_slug", ForeignKey("enrollments.slug", ondelete="CASCADE"), primary_key=True),
)


class Content(Base, TimestampMixin):
    """Base content model with common fields."""

    __tablename__ = "contents"

    slug: Mapped[str] = mapped_column(String(255), primary_key=True)
    title: Mapped[str | None] = mapped_column(String(255))
    blurb: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    eyebrow: Mapped[str | None] = mapped_column(Text)
    body: Mapped[str | None] = mapped_column(Text)
    enrollment: Mapped[str | None] = mapped_column(Text)
    instructions: Mapped[str | None] = mapped_column(Text)
    cta_label: Mapped[str | None] = mapped_column(String(100))
    other_content: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    image: Mapped[str | None] = mapped_column(String(500))

    source: Mapped[str | None] = mapped_column(String(255))
    for_: Mapped[str | None] = mapped_column("for", String(255))  # 'for' is reserved
    rank: Mapped[int | None] = mapped_column()
    renderers: Mapped[str | None] = mapped_column(String(255))
    comment: Mapped[str | None] = mapped_column(Text)

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


class Class(Base, TimestampMixin):
    """A class offered by the League."""

    __tablename__ = "classes"

    slug: Mapped[str] = mapped_column(String(255), primary_key=True)
    price: Mapped[str | None] = mapped_column(String(50))
    grade: Mapped[str | None] = mapped_column(String(50))
    day: Mapped[str | None] = mapped_column(String(50))
    level: Mapped[str | None] = mapped_column(String(50))
    times: Mapped[str | None] = mapped_column(String(100))
    location_code: Mapped[str | None] = mapped_column(String(50))
    start_date: Mapped[str | None] = mapped_column(String(50))
    end_date: Mapped[str | None] = mapped_column(String(50))
    enrollment_opens: Mapped[str | None] = mapped_column(String(50))
    enrollment_closes: Mapped[str | None] = mapped_column(String(50))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    schedule_link: Mapped[str | None] = mapped_column(String(500))
    enroll_link: Mapped[str | None] = mapped_column(String(500))
    curriculum_link: Mapped[str | None] = mapped_column(String(500))
    proto: Mapped[str | None] = mapped_column(String(255))
    color: Mapped[str | None] = mapped_column(String(50))

    program: Mapped[str | None] = mapped_column(String(100))
    track: Mapped[str | None] = mapped_column(String(100))
    subject: Mapped[str | None] = mapped_column(String(100))
    category: Mapped[str | None] = mapped_column(String(100))

    content_slug: Mapped[str | None] = mapped_column(ForeignKey("contents.slug", ondelete="SET NULL"))

    # Relationships
    content: Mapped["Content | None"] = relationship()
    categories: Mapped[list["Category"]] = relationship(secondary=class_categories)
    topics: Mapped[list["Topic"]] = relationship(secondary=class_topics)
    ctas: Mapped[list["CTA"]] = relationship(secondary=class_ctas)
    enrollments: Mapped[list["Enrollment"]] = relationship(secondary=class_enrollments)


class Enrollment(Base, TimestampMixin):
    """An enrollment component for a class."""

    __tablename__ = "enrollments"

    slug: Mapped[str] = mapped_column(String(255), primary_key=True)
    enrollment_component: Mapped[str | None] = mapped_column(String(255))

    content_slug: Mapped[str | None] = mapped_column(ForeignKey("contents.slug", ondelete="SET NULL"))
    cta_slug: Mapped[str | None] = mapped_column(ForeignKey("ctas.slug", ondelete="SET NULL"))

    # Relationships
    content: Mapped["Content | None"] = relationship()
    cta: Mapped["CTA | None"] = relationship()


class CTA(Base, TimestampMixin):
    """A call-to-action component."""

    __tablename__ = "ctas"

    slug: Mapped[str] = mapped_column(String(255), primary_key=True)
    title: Mapped[str | None] = mapped_column(String(255))
    blurb: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    eyebrow: Mapped[str | None] = mapped_column(Text)
    cta_label: Mapped[str | None] = mapped_column(String(100))

    type: Mapped[str | None] = mapped_column(String(50))
    url: Mapped[str | None] = mapped_column(String(500))


class Announcement(Base, TimestampMixin):
    """An announcement with date range."""

    __tablename__ = "announcements"

    id: Mapped[int] = mapped_column(primary_key=True)
    from_date: Mapped[str | None] = mapped_column("from", String(50))  # 'from' is reserved
    until: Mapped[str | None] = mapped_column(String(50))
    link: Mapped[str | None] = mapped_column(String(500))

    content_slug: Mapped[str | None] = mapped_column(ForeignKey("contents.slug", ondelete="SET NULL"))

    # Relationships
    content: Mapped["Content | None"] = relationship()
