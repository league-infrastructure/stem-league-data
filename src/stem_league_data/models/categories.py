"""Category-related models: Group, Program, Track, Category, SubCategory, Topic."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from stem_league_data.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from stem_league_data.models.place import Org


class Group(Base, TimestampMixin):
    """Base class for categorization groups."""

    __tablename__ = "groups"

    slug: Mapped[str] = mapped_column(String(100), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    blurb: Mapped[str | None] = mapped_column(Text)
    where: Mapped[str | None] = mapped_column(String(255))
    color: Mapped[str | None] = mapped_column(String(50))
    group_type: Mapped[str] = mapped_column(String(50), nullable=False)  # discriminator

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
