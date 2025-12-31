"""Category-related models: Group, Program, Track, Category, SubCategory, Topic."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from stem_league_data.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from stem_league_data.models.place import Org


class Group(Base, TimestampMixin):
    """Base class for categorization groups.
    
    Uses single-table inheritance. All subtypes (Program, Track, Category,
    SubCategory, Topic) share this table with a `group_type` discriminator.
    """

    __tablename__ = "groups"
    __table_args__ = (
        UniqueConstraint("slug", "group_type", name="uq_groups_slug_group_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    group_type: Mapped[str] = mapped_column(String(50), nullable=False)  # discriminator
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    blurb: Mapped[str | None] = mapped_column(Text)
    where: Mapped[str | None] = mapped_column(String(255))
    color: Mapped[str | None] = mapped_column(String(50))


    org_id: Mapped[int | None] = mapped_column(ForeignKey("orgs.id", ondelete="SET NULL"))

    # Relationships
    org: Mapped["Org | None"] = relationship()

    __mapper_args__ = {
        "polymorphic_on": "group_type",
        "polymorphic_identity": "group",
    }


class Program(Group):
    """A program grouping of classes."""

    __mapper_args__ = {
        "polymorphic_identity": "program",
    }


class Track(Group):
    """A track within a program."""

    __mapper_args__ = {
        "polymorphic_identity": "track",
    }


class Category(Group):
    """A category for classes."""

    __mapper_args__ = {
        "polymorphic_identity": "category",
    }


class SubCategory(Group):
    """A subcategory within a category."""

    __mapper_args__ = {
        "polymorphic_identity": "subcategory",
    }


class Topic(Group):
    """A topic tag for classes."""

    __mapper_args__ = {
        "polymorphic_identity": "topic",
    }


class Tag(Base):
    """A tag for categorizing events."""

    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
