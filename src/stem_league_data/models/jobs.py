"""Job-related models: JobPosting, InstructorAssignment, InstructorEvaluation."""

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text, Boolean, Date, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from stem_league_data.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from stem_league_data.models.place import Metro, Org
    from stem_league_data.models.people import Staff
    from stem_league_data.models.events import Activity


class JobPosting(Base, TimestampMixin):
    """A job posting from an organization."""

    __tablename__ = "job_postings"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)  # richtext
    hourly_rate: Mapped[str | None] = mapped_column(String(50))
    hours_per_week: Mapped[str | None] = mapped_column(String(50))
    requirements: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str | None] = mapped_column(String(50))  # enum: draft, open, closed, filled
    posted_date: Mapped[date | None] = mapped_column(Date)

    org_id: Mapped[int] = mapped_column(ForeignKey("orgs.id", ondelete="SET NULL"), nullable=False)
    metro_id: Mapped[int] = mapped_column(ForeignKey("metros.id", ondelete="SET NULL"), nullable=False)

    # Relationships
    org: Mapped["Org"] = relationship(back_populates="job_postings")
    metro: Mapped["Metro"] = relationship(back_populates="job_postings")


class InstructorAssignment(Base, TimestampMixin):
    """An assignment of an instructor to an event."""

    __tablename__ = "instructor_assignments"

    id: Mapped[int] = mapped_column(primary_key=True)
    role: Mapped[str | None] = mapped_column(String(50))  # enum: lead, assistant, volunteer
    employment_type: Mapped[str | None] = mapped_column(String(50))  # enum: employee, contractor, volunteer
    hourly_rate: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    is_volunteer: Mapped[bool] = mapped_column(Boolean, default=False)
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    hours_worked: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))

    event_id: Mapped[int] = mapped_column(ForeignKey("activities.id", ondelete="CASCADE"), nullable=False)
    instructor_id: Mapped[int] = mapped_column(ForeignKey("staff.id", ondelete="CASCADE"), nullable=False)
    employer_id: Mapped[int | None] = mapped_column(ForeignKey("orgs.id", ondelete="SET NULL"))

    # Relationships
    activity: Mapped["Activity"] = relationship(back_populates="instructor_assignments")
    instructor: Mapped["Staff"] = relationship(back_populates="instructor_assignments")
    employer: Mapped["Org | None"] = relationship()
    evaluations: Mapped[list["InstructorEvaluation"]] = relationship(
        back_populates="instructor_assignment"
    )


class InstructorEvaluation(Base, TimestampMixin):
    """An evaluation of an instructor's performance."""

    __tablename__ = "instructor_evaluations"

    id: Mapped[int] = mapped_column(primary_key=True)
    technical_skills: Mapped[int | None] = mapped_column(Integer)  # 1-5 rating
    teaching_ability: Mapped[int | None] = mapped_column(Integer)  # 1-5 rating
    reliability: Mapped[int | None] = mapped_column(Integer)  # 1-5 rating
    student_engagement: Mapped[int | None] = mapped_column(Integer)  # 1-5 rating
    notes: Mapped[str | None] = mapped_column(Text)
    potential_hire: Mapped[bool] = mapped_column(Boolean, default=False)

    instructor_assignment_id: Mapped[int] = mapped_column(
        ForeignKey("instructor_assignments.id", ondelete="SET NULL"), nullable=False
    )
    evaluator_id: Mapped[int] = mapped_column(ForeignKey("staff.id", ondelete="SET NULL"), nullable=False)

    # Relationships
    instructor_assignment: Mapped["InstructorAssignment"] = relationship(
        back_populates="evaluations"
    )
    evaluator: Mapped["Staff"] = relationship(back_populates="evaluations_given")
