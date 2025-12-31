"""Content-related models: Content, Page, Class, Enrollment, CTA, Announcement."""

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, String, Text, Boolean, Table, Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from stem_league_data.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from stem_league_data.models.categories import Program, Track, Category, SubCategory, Topic


# Association tables
class_programs = Table(
    "class_programs",
    Base.metadata,
    Column("class_id", ForeignKey("classes.id", ondelete="CASCADE"), primary_key=True),
    Column("program_id", ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True),
)

class_tracks = Table(
    "class_tracks",
    Base.metadata,
    Column("class_id", ForeignKey("classes.id", ondelete="CASCADE"), primary_key=True),
    Column("track_id", ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True),
)

class_categories = Table(
    "class_categories",
    Base.metadata,
    Column("class_id", ForeignKey("classes.id", ondelete="CASCADE"), primary_key=True),
    Column("category_id", ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True),
)

class_topics = Table(
    "class_topics",
    Base.metadata,
    Column("class_id", ForeignKey("classes.id", ondelete="CASCADE"), primary_key=True),
    Column("topic_id", ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True),
)

class_subcategories = Table(
    "class_subcategories",
    Base.metadata,
    Column("class_id", ForeignKey("classes.id", ondelete="CASCADE"), primary_key=True),
    Column("subcategory_id", ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True),
)

class_ctas = Table(
    "class_ctas",
    Base.metadata,
    Column("class_id", ForeignKey("classes.id", ondelete="CASCADE"), primary_key=True),
    Column("cta_id", ForeignKey("ctas.id", ondelete="CASCADE"), primary_key=True),
)

class_enrollments = Table(
    "class_enrollments",
    Base.metadata,
    Column("class_id", ForeignKey("classes.id", ondelete="CASCADE"), primary_key=True),
    Column("enrollment_id", ForeignKey("enrollments.id", ondelete="CASCADE"), primary_key=True),
)


class Content(Base, TimestampMixin):
    """Base content model with common fields."""

    __tablename__ = "contents"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
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


class Syllabus(Base, TimestampMixin):
    """Describes the educational content of a class, course or event. """

    __tablename__ = "sullabus"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    grade: Mapped[str | None] = mapped_column(String(50))
    level: Mapped[str | None] = mapped_column(String(50))
    topics: Mapped[list["Topic"]] = relationship(secondary=class_topics)
    
    tracks: Mapped[list["Track"]] = relationship(secondary=class_tracks)
    categories: Mapped[list["Category"]] = relationship(secondary=class_categories)
    subcategories: Mapped[list["SubCategory"]] = relationship(secondary=class_subcategories)

    curriculum_link: Mapped[str | None] = mapped_column(String(500))
    
    content_id: Mapped[int | None] = mapped_column(
        ForeignKey("contents.id", ondelete="SET NULL")
    )
    content: Mapped["Content | None"] = relationship()

    subordinate_to: Mapped[list["Syllabus"]] = relationship(back_populates="superior_to")


class Class(Base, TimestampMixin):
    """A class offered by the League. """

    __tablename__ = "classes"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    # These are content fiels, for display on the website.

    day: Mapped[str | None] = mapped_column(String(50))
    #times: Mapped[str | None] = mapped_column(String(100))
    #price: Mapped[str | None] = mapped_column(String(50))



    # Group relationships
    programs: Mapped[list["Program"]] = relationship(secondary=class_programs)
    tracks: Mapped[list["Track"]] = relationship(secondary=class_tracks)
    categories: Mapped[list["Category"]] = relationship(secondary=class_categories)
    subcategories: Mapped[list["SubCategory"]] = relationship(secondary=class_subcategories)

    
    #start_dt: Mapped[datetime | None] = mapped_column(DateTime)
    #end_dt: Mapped[datetime | None] = mapped_column(DateTime)
    #rrule: Mapped[str | None] = mapped_column(String(200))

    #enrollment_opens: Mapped[datetime | None] = mapped_column(DateTime)
    #enrollment_closes: Mapped[datetime | None] = mapped_column(DateTime)

    #location_code: Mapped[str | None] = mapped_column(String(50))

    active: Mapped[bool] = mapped_column(Boolean, default=True)

    schedule_link: Mapped[str | None] = mapped_column(String(500))
    enroll_link: Mapped[str | None] = mapped_column(String(500))

    proto: Mapped[str | None] = mapped_column(String(255))

    program: Mapped[str | None] = mapped_column(String(100))
    track: Mapped[str | None] = mapped_column(String(100))
    subject: Mapped[str | None] = mapped_column(String(100))
    category: Mapped[str | None] = mapped_column(String(100))

    # Relationships

    ctas: Mapped[list["CTA"]] = relationship(secondary=class_ctas)
    enrollments: Mapped[list["Enrollment"]] = relationship(secondary=class_enrollments)


class Enrollment(Base, TimestampMixin):
    """An enrollment component for a class."""

    __tablename__ = "enrollments"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    enrollment_component: Mapped[str | None] = mapped_column(String(255))

    content_id: Mapped[int | None] = mapped_column(ForeignKey("contents.id", ondelete="SET NULL"))
    cta_id: Mapped[int | None] = mapped_column(ForeignKey("ctas.id", ondelete="SET NULL"))

    # Relationships
    content: Mapped["Content | None"] = relationship()
    cta: Mapped["CTA | None"] = relationship()


class CTA(Base, TimestampMixin):
    """A call-to-action component."""

    __tablename__ = "ctas"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
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
    from_date: Mapped[datetime | None] = mapped_column("from", DateTime)  # 'from' is reserved
    until: Mapped[datetime | None] = mapped_column(DateTime)
    link: Mapped[str | None] = mapped_column(String(500))

    content_slug: Mapped[str | None] = mapped_column(ForeignKey("contents.slug", ondelete="SET NULL"))

    # Relationships
    content: Mapped["Content | None"] = relationship()
