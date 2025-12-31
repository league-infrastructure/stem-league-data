"""People-related models."""

from datetime import date
from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, String, Text, Boolean, Date, Integer
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from stem_league_data.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from stem_league_data.models.place import Metro
    from stem_league_data.models.events import Registration, RSVP
    from stem_league_data.models.jobs import InstructorAssignment, InstructorEvaluation


class Person(Base, TimestampMixin):
    """A person in the League STEM network."""

    __tablename__ = "persons"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str | None] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    sex: Mapped[str | None] = mapped_column(String(20))  # enum: male, female, other, prefer_not_to_say
    login_enabled: Mapped[bool] = mapped_column(Boolean, default=False)

    metro_id: Mapped[int | None] = mapped_column(ForeignKey("metros.id", ondelete="RESTRICT"))

    # Relationships
    metro: Mapped["Metro | None"] = relationship(back_populates="persons")
    registrations: Mapped[list["Registration"]] = relationship(back_populates="registrant")
    guardian_rsvps: Mapped[list["RSVP"]] = relationship(
        back_populates="guardian", foreign_keys="RSVP.guardian_id"
    )
    staff: Mapped["Staff | None"] = relationship(back_populates="person")
    visitors: Mapped[list["Visitor"]] = relationship(
        back_populates="person", foreign_keys="Visitor.person_id"
    )
    guardian_visitors: Mapped[list["Visitor"]] = relationship(
        back_populates="guardian", foreign_keys="Visitor.guardian_id"
    )


class Staff(Base, TimestampMixin):
    """A staff member, instructor, or volunteer in the League STEM network."""

    __tablename__ = "staff"

    id: Mapped[int] = mapped_column(primary_key=True)
    role: Mapped[str | None] = mapped_column(String(50))  # enum: instructor, volunteer, staff, admin
    bio: Mapped[str | None] = mapped_column(Text)
    photo: Mapped[str | None] = mapped_column(String(500))  # media URL
    is_adult: Mapped[bool] = mapped_column(Boolean, default=True)
    background_check_status: Mapped[str | None] = mapped_column(String(50))  # enum: pending, approved, denied, expired
    volunteer_tier: Mapped[str | None] = mapped_column(String(50))  # enum: bronze, silver, gold, platinum
    open_to_employment: Mapped[bool] = mapped_column(Boolean, default=False)
    specializations: Mapped[list[str] | None] = mapped_column(ARRAY(String))

    person_id: Mapped[int] = mapped_column(ForeignKey("persons.id", ondelete="CASCADE"), nullable=False, unique=True)

    # Relationships
    person: Mapped["Person"] = relationship(back_populates="staff")
    instructor_assignments: Mapped[list["InstructorAssignment"]] = relationship(
        back_populates="instructor"
    )
    evaluations_given: Mapped[list["InstructorEvaluation"]] = relationship(
        back_populates="evaluator"
    )


class Visitor(Base, TimestampMixin):
    """A visitor (student/participant) in the League STEM network."""

    __tablename__ = "visitors"

    id: Mapped[int] = mapped_column(primary_key=True)
    grade: Mapped[str | None] = mapped_column(String(20))
    school: Mapped[str | None] = mapped_column(String(255))

    person_id: Mapped[int | None] = mapped_column(ForeignKey("persons.id", ondelete="SET NULL"))
    guardian_id: Mapped[int | None] = mapped_column(ForeignKey("persons.id", ondelete="SET NULL"))

    # Relationships
    person: Mapped["Person | None"] = relationship(
        back_populates="visitors", foreign_keys=[person_id]
    )
    guardian: Mapped["Person | None"] = relationship(
        back_populates="guardian_visitors", foreign_keys=[guardian_id]
    )
    rsvps: Mapped[list["RSVP"]] = relationship(back_populates="visitor")
