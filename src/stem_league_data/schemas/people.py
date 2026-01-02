"""Schemas for People models: Person, Staff, Visitor."""

from datetime import date

from stem_league_data.schemas.base import BaseSchema, TimestampSchema


# Person Schemas
class PersonBase(BaseSchema):
    """Base Person schema."""
    first_name: str
    last_name: str
    title: str | None = None
    email: str | None = None
    phone: str | None = None
    date_of_birth: date | None = None
    sex: str | None = None
    login_enabled: bool = False


class PersonCreate(PersonBase):
    """Schema for creating a Person."""
    metro_id: int | None = None


class PersonUpdate(BaseSchema):
    """Schema for updating a Person."""
    first_name: str | None = None
    last_name: str | None = None
    title: str | None = None
    email: str | None = None
    phone: str | None = None
    date_of_birth: date | None = None
    sex: str | None = None
    login_enabled: bool | None = None
    metro_id: int | None = None


class PersonResponse(PersonBase, TimestampSchema):
    """Schema for Person response."""
    id: int
    metro_id: int | None = None


# Staff Schemas
class StaffBase(BaseSchema):
    """Base Staff schema."""
    role: str | None = None
    bio: str | None = None
    photo: str | None = None
    is_adult: bool = True
    background_check_status: str | None = None
    volunteer_tier: str | None = None
    open_to_employment: bool = False
    specializations: list[str] | None = None


class StaffCreate(StaffBase):
    """Schema for creating a Staff record."""
    person_id: int
    

class StaffCreateWithPerson(StaffBase):
    """Schema for creating a Staff record with a new Person."""
    person: PersonCreate


class StaffUpdate(BaseSchema):
    """Schema for updating a Staff record."""
    role: str | None = None
    bio: str | None = None
    photo: str | None = None
    is_adult: bool | None = None
    background_check_status: str | None = None
    volunteer_tier: str | None = None
    open_to_employment: bool | None = None
    specializations: list[str] | None = None


class StaffResponse(StaffBase, TimestampSchema):
    """Schema for Staff response."""
    id: int
    person_id: int
    person: PersonResponse | None = None


# Visitor Schemas
class VisitorBase(BaseSchema):
    """Base Visitor schema."""
    grade: str | None = None
    school: str | None = None


class VisitorCreate(VisitorBase):
    """Schema for creating a Visitor."""
    person_id: int | None = None
    guardian_id: int | None = None


class VisitorUpdate(BaseSchema):
    """Schema for updating a Visitor."""
    grade: str | None = None
    school: str | None = None
    person_id: int | None = None
    guardian_id: int | None = None


class VisitorResponse(VisitorBase, TimestampSchema):
    """Schema for Visitor response."""
    id: int
    person_id: int | None = None
    guardian_id: int | None = None
