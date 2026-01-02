"""Router for Content resources: Content, Announcement."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from stem_league_data.database import get_db
from stem_league_data.models import Content, Announcement
from stem_league_data.schemas.content import (
    ContentCreate, ContentUpdate, ContentResponse,
    AnnouncementCreate, AnnouncementUpdate, AnnouncementResponse,
)

router = APIRouter()


# ============================================================================
# Content Endpoints
# ============================================================================

@router.get("/contents", response_model=list[ContentResponse], tags=["contents"])
def list_contents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    content_type: str | None = None,
    db: Session = Depends(get_db),
) -> list[Any]:
    """List all contents with pagination and optional type filter."""
    query = db.query(Content)
    if content_type is not None:
        query = query.filter(Content.content_type == content_type)
    return query.offset(skip).limit(limit).all()


@router.get("/contents/count", tags=["contents"])
def count_contents(db: Session = Depends(get_db)) -> dict[str, int]:
    """Get total count of contents."""
    count = db.query(func.count(Content.id)).scalar()
    return {"count": count}


@router.get("/contents/{content_id}", response_model=ContentResponse, tags=["contents"])
def get_content(content_id: int, db: Session = Depends(get_db)) -> Any:
    """Get a single content by ID."""
    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    return content


@router.post("/contents", response_model=ContentResponse, status_code=201, tags=["contents"])
def create_content(data: ContentCreate, db: Session = Depends(get_db)) -> Any:
    """Create a new content."""
    content = Content(**data.model_dump())
    db.add(content)
    db.commit()
    db.refresh(content)
    return content


@router.put("/contents/{content_id}", response_model=ContentResponse, tags=["contents"])
def update_content(
    content_id: int,
    data: ContentUpdate,
    db: Session = Depends(get_db),
) -> Any:
    """Update an existing content."""
    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(content, field, value)
    
    db.commit()
    db.refresh(content)
    return content


@router.delete("/contents/{content_id}", status_code=204, tags=["contents"])
def delete_content(content_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a content."""
    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    db.delete(content)
    db.commit()


# ============================================================================
# Announcement Endpoints
# ============================================================================

@router.get("/announcements", response_model=list[AnnouncementResponse], tags=["announcements"])
def list_announcements(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> list[Any]:
    """List all announcements with pagination."""
    return db.query(Announcement).offset(skip).limit(limit).all()


@router.get("/announcements/count", tags=["announcements"])
def count_announcements(db: Session = Depends(get_db)) -> dict[str, int]:
    """Get total count of announcements."""
    count = db.query(func.count(Announcement.id)).scalar()
    return {"count": count}


@router.get("/announcements/{announcement_id}", response_model=AnnouncementResponse, tags=["announcements"])
def get_announcement(announcement_id: int, db: Session = Depends(get_db)) -> Any:
    """Get a single announcement by ID."""
    announcement = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")
    return announcement


@router.post("/announcements", response_model=AnnouncementResponse, status_code=201, tags=["announcements"])
def create_announcement(data: AnnouncementCreate, db: Session = Depends(get_db)) -> Any:
    """Create a new announcement.
    
    Can optionally create content inline.
    """
    announcement_data = data.model_dump(exclude={"content"})
    
    # Handle inline content creation
    if data.content is not None and data.content_id is None:
        content = Content(**data.content.model_dump())
        db.add(content)
        db.flush()
        announcement_data["content_id"] = content.id
    elif data.content_id is not None:
        # Validate content exists
        content = db.query(Content).filter(Content.id == data.content_id).first()
        if not content:
            raise HTTPException(status_code=400, detail="Content not found")
    
    announcement = Announcement(**announcement_data)
    db.add(announcement)
    db.commit()
    db.refresh(announcement)
    return announcement


@router.put("/announcements/{announcement_id}", response_model=AnnouncementResponse, tags=["announcements"])
def update_announcement(
    announcement_id: int,
    data: AnnouncementUpdate,
    db: Session = Depends(get_db),
) -> Any:
    """Update an existing announcement."""
    announcement = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")
    
    update_data = data.model_dump(exclude_unset=True)
    
    # Validate content if being updated
    if "content_id" in update_data and update_data["content_id"] is not None:
        content = db.query(Content).filter(Content.id == update_data["content_id"]).first()
        if not content:
            raise HTTPException(status_code=400, detail="Content not found")
    
    for field, value in update_data.items():
        setattr(announcement, field, value)
    
    db.commit()
    db.refresh(announcement)
    return announcement


@router.delete("/announcements/{announcement_id}", status_code=204, tags=["announcements"])
def delete_announcement(announcement_id: int, db: Session = Depends(get_db)) -> None:
    """Delete an announcement."""
    announcement = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")
    
    db.delete(announcement)
    db.commit()
