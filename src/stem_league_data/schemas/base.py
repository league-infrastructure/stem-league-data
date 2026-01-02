"""Base Pydantic schemas with common configuration."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


class TimestampSchema(BaseSchema):
    """Schema with timestamp fields."""
    
    created_at: datetime | None = None
    updated_at: datetime | None = None


class PaginatedResponse(BaseSchema):
    """Paginated response wrapper."""
    
    items: list[Any]
    total: int
    page: int
    page_size: int
    pages: int
