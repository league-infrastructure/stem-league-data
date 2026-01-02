"""Schemas for Job models: JobPosting, InstructorAssignment, InstructorEvaluation."""

from datetime import date
from decimal import Decimal

from stem_league_data.schemas.base import BaseSchema, TimestampSchema


# JobPosting Schemas
class JobPostingBase(BaseSchema):
    """Base JobPosting schema."""
    title: str
    description: str | None = None
    hourly_rate: str | None = None
    hours_per_week: str | None = None
    requirements: str | None = None
    status: str | None = None  # draft, open, closed, filled
    posted_date: date | None = None


class JobPostingCreate(JobPostingBase):
    """Schema for creating a JobPosting."""
    org_id: int
    metro_id: int


class JobPostingUpdate(BaseSchema):
    """Schema for updating a JobPosting."""
    title: str | None = None
    description: str | None = None
    hourly_rate: str | None = None
    hours_per_week: str | None = None
    requirements: str | None = None
    status: str | None = None
    posted_date: date | None = None
    org_id: int | None = None
    metro_id: int | None = None


class JobPostingResponse(JobPostingBase, TimestampSchema):
    """Schema for JobPosting response."""
    id: int
    org_id: int
    metro_id: int


# InstructorAssignment Schemas
class InstructorAssignmentBase(BaseSchema):
    """Base InstructorAssignment schema."""
    role: str | None = None  # lead, assistant, volunteer
    employment_type: str | None = None  # employee, contractor, volunteer
    hourly_rate: Decimal | None = None
    is_volunteer: bool = False
    confirmed: bool = False
    hours_worked: Decimal | None = None


class InstructorAssignmentCreate(InstructorAssignmentBase):
    """Schema for creating an InstructorAssignment."""
    event_id: int
    instructor_id: int
    employer_id: int | None = None


class InstructorAssignmentUpdate(BaseSchema):
    """Schema for updating an InstructorAssignment."""
    role: str | None = None
    employment_type: str | None = None
    hourly_rate: Decimal | None = None
    is_volunteer: bool | None = None
    confirmed: bool | None = None
    hours_worked: Decimal | None = None
    employer_id: int | None = None


class InstructorAssignmentResponse(InstructorAssignmentBase, TimestampSchema):
    """Schema for InstructorAssignment response."""
    id: int
    event_id: int
    instructor_id: int
    employer_id: int | None = None


# InstructorEvaluation Schemas
class InstructorEvaluationBase(BaseSchema):
    """Base InstructorEvaluation schema."""
    technical_skills: int | None = None  # 1-5 rating
    teaching_ability: int | None = None  # 1-5 rating
    reliability: int | None = None  # 1-5 rating
    student_engagement: int | None = None  # 1-5 rating
    notes: str | None = None
    potential_hire: bool = False


class InstructorEvaluationCreate(InstructorEvaluationBase):
    """Schema for creating an InstructorEvaluation."""
    instructor_assignment_id: int
    evaluator_id: int


class InstructorEvaluationUpdate(BaseSchema):
    """Schema for updating an InstructorEvaluation."""
    technical_skills: int | None = None
    teaching_ability: int | None = None
    reliability: int | None = None
    student_engagement: int | None = None
    notes: str | None = None
    potential_hire: bool | None = None


class InstructorEvaluationResponse(InstructorEvaluationBase, TimestampSchema):
    """Schema for InstructorEvaluation response."""
    id: int
    instructor_assignment_id: int
    evaluator_id: int
