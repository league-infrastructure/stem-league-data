"""Schemas for Category models: Group, Program, Track, Category, SubCategory, Topic, Tag."""

from stem_league_data.schemas.base import BaseSchema, TimestampSchema


# Group Schemas (base for all category types)
class GroupBase(BaseSchema):
    """Base Group schema."""
    slug: str
    name: str
    where: str | None = None
    color: str | None = None


class GroupCreate(GroupBase):
    """Schema for creating a Group."""
    group_type: str = "group"
    org_id: int | None = None
    content_id: int | None = None


class GroupUpdate(BaseSchema):
    """Schema for updating a Group."""
    slug: str | None = None
    name: str | None = None
    where: str | None = None
    color: str | None = None
    org_id: int | None = None
    content_id: int | None = None


class GroupResponse(GroupBase, TimestampSchema):
    """Schema for Group response."""
    id: int
    group_type: str
    org_id: int | None = None
    content_id: int | None = None


# Program Schemas
class ProgramBase(GroupBase):
    """Base Program schema."""
    pass


class ProgramCreate(ProgramBase):
    """Schema for creating a Program."""
    org_id: int | None = None
    content_id: int | None = None


class ProgramUpdate(GroupUpdate):
    """Schema for updating a Program."""
    pass


class ProgramResponse(GroupResponse):
    """Schema for Program response."""
    pass


# Track Schemas
class TrackBase(GroupBase):
    """Base Track schema."""
    pass


class TrackCreate(TrackBase):
    """Schema for creating a Track."""
    org_id: int | None = None
    content_id: int | None = None


class TrackUpdate(GroupUpdate):
    """Schema for updating a Track."""
    pass


class TrackResponse(GroupResponse):
    """Schema for Track response."""
    pass


# Category Schemas
class CategoryBase(GroupBase):
    """Base Category schema."""
    pass


class CategoryCreate(CategoryBase):
    """Schema for creating a Category."""
    org_id: int | None = None
    content_id: int | None = None


class CategoryUpdate(GroupUpdate):
    """Schema for updating a Category."""
    pass


class CategoryResponse(GroupResponse):
    """Schema for Category response."""
    pass


# SubCategory Schemas
class SubCategoryBase(GroupBase):
    """Base SubCategory schema."""
    pass


class SubCategoryCreate(SubCategoryBase):
    """Schema for creating a SubCategory."""
    org_id: int | None = None
    content_id: int | None = None


class SubCategoryUpdate(GroupUpdate):
    """Schema for updating a SubCategory."""
    pass


class SubCategoryResponse(GroupResponse):
    """Schema for SubCategory response."""
    pass


# Topic Schemas
class TopicBase(GroupBase):
    """Base Topic schema."""
    pass


class TopicCreate(TopicBase):
    """Schema for creating a Topic."""
    org_id: int | None = None
    content_id: int | None = None


class TopicUpdate(GroupUpdate):
    """Schema for updating a Topic."""
    pass


class TopicResponse(GroupResponse):
    """Schema for Topic response."""
    pass


# Tag Schemas (separate from Group hierarchy)
class TagBase(BaseSchema):
    """Base Tag schema."""
    name: str
    slug: str


class TagCreate(TagBase):
    """Schema for creating a Tag."""
    pass


class TagUpdate(BaseSchema):
    """Schema for updating a Tag."""
    name: str | None = None
    slug: str | None = None


class TagResponse(TagBase):
    """Schema for Tag response."""
    id: int
