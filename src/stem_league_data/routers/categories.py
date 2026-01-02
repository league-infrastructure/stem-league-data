"""Router for Category resources: Group, Program, Track, Category, SubCategory, Topic, Tag."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from stem_league_data.database import get_db
from stem_league_data.models import Group, Program, Track, Category, SubCategory, Topic, Tag
from stem_league_data.schemas.categories import (
    GroupCreate, GroupUpdate, GroupResponse,
    ProgramCreate, ProgramUpdate, ProgramResponse,
    CategoryCreate, CategoryUpdate, CategoryResponse,
    TopicCreate, TopicUpdate, TopicResponse,
    TrackCreate, TrackUpdate, TrackResponse,
    SubCategoryCreate, SubCategoryUpdate, SubCategoryResponse,
    TagCreate, TagUpdate, TagResponse,
)

router = APIRouter()


# ============================================================================
# Group Endpoints (base for all category types)
# ============================================================================

@router.get("/groups", response_model=list[GroupResponse], tags=["groups"])
def list_groups(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    group_type: str | None = None,
    db: Session = Depends(get_db),
) -> list[Any]:
    """List all groups with pagination and optional type filter."""
    query = db.query(Group)
    if group_type is not None:
        query = query.filter(Group.group_type == group_type)
    return query.offset(skip).limit(limit).all()


@router.get("/groups/count", tags=["groups"])
def count_groups(db: Session = Depends(get_db)) -> dict[str, int]:
    """Get total count of groups."""
    count = db.query(func.count(Group.id)).scalar()
    return {"count": count}


@router.get("/groups/{group_id}", response_model=GroupResponse, tags=["groups"])
def get_group(group_id: int, db: Session = Depends(get_db)) -> Any:
    """Get a single group by ID."""
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group


# ============================================================================
# Program Endpoints
# ============================================================================

@router.get("/programs", response_model=list[ProgramResponse], tags=["programs"])
def list_programs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> list[Any]:
    """List all programs with pagination."""
    return db.query(Program).offset(skip).limit(limit).all()


@router.get("/programs/count", tags=["programs"])
def count_programs(db: Session = Depends(get_db)) -> dict[str, int]:
    """Get total count of programs."""
    count = db.query(func.count(Program.id)).scalar()
    return {"count": count}


@router.get("/programs/{program_id}", response_model=ProgramResponse, tags=["programs"])
def get_program(program_id: int, db: Session = Depends(get_db)) -> Any:
    """Get a single program by ID."""
    program = db.query(Program).filter(Program.id == program_id).first()
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    return program


@router.post("/programs", response_model=ProgramResponse, status_code=201, tags=["programs"])
def create_program(data: ProgramCreate, db: Session = Depends(get_db)) -> Any:
    """Create a new program."""
    program = Program(group_type="program", **data.model_dump())
    db.add(program)
    db.commit()
    db.refresh(program)
    return program


@router.put("/programs/{program_id}", response_model=ProgramResponse, tags=["programs"])
def update_program(
    program_id: int,
    data: ProgramUpdate,
    db: Session = Depends(get_db),
) -> Any:
    """Update an existing program."""
    program = db.query(Program).filter(Program.id == program_id).first()
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(program, field, value)
    
    db.commit()
    db.refresh(program)
    return program


@router.delete("/programs/{program_id}", status_code=204, tags=["programs"])
def delete_program(program_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a program."""
    program = db.query(Program).filter(Program.id == program_id).first()
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    
    db.delete(program)
    db.commit()


# ============================================================================
# Track Endpoints
# ============================================================================

@router.get("/tracks", response_model=list[TrackResponse], tags=["tracks"])
def list_tracks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> list[Any]:
    """List all tracks with pagination."""
    return db.query(Track).offset(skip).limit(limit).all()


@router.get("/tracks/count", tags=["tracks"])
def count_tracks(db: Session = Depends(get_db)) -> dict[str, int]:
    """Get total count of tracks."""
    count = db.query(func.count(Track.id)).scalar()
    return {"count": count}


@router.get("/tracks/{track_id}", response_model=TrackResponse, tags=["tracks"])
def get_track(track_id: int, db: Session = Depends(get_db)) -> Any:
    """Get a single track by ID."""
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    return track


@router.post("/tracks", response_model=TrackResponse, status_code=201, tags=["tracks"])
def create_track(data: TrackCreate, db: Session = Depends(get_db)) -> Any:
    """Create a new track."""
    track = Track(group_type="track", **data.model_dump())
    db.add(track)
    db.commit()
    db.refresh(track)
    return track


@router.put("/tracks/{track_id}", response_model=TrackResponse, tags=["tracks"])
def update_track(
    track_id: int,
    data: TrackUpdate,
    db: Session = Depends(get_db),
) -> Any:
    """Update an existing track."""
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(track, field, value)
    
    db.commit()
    db.refresh(track)
    return track


@router.delete("/tracks/{track_id}", status_code=204, tags=["tracks"])
def delete_track(track_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a track."""
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    db.delete(track)
    db.commit()


# ============================================================================
# Category Endpoints
# ============================================================================

@router.get("/categories", response_model=list[CategoryResponse], tags=["categories"])
def list_categories(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> list[Any]:
    """List all categories with pagination."""
    return db.query(Category).offset(skip).limit(limit).all()


@router.get("/categories/count", tags=["categories"])
def count_categories(db: Session = Depends(get_db)) -> dict[str, int]:
    """Get total count of categories."""
    count = db.query(func.count(Category.id)).scalar()
    return {"count": count}


@router.get("/categories/{category_id}", response_model=CategoryResponse, tags=["categories"])
def get_category(category_id: int, db: Session = Depends(get_db)) -> Any:
    """Get a single category by ID."""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@router.post("/categories", response_model=CategoryResponse, status_code=201, tags=["categories"])
def create_category(data: CategoryCreate, db: Session = Depends(get_db)) -> Any:
    """Create a new category."""
    category = Category(group_type="category", **data.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.put("/categories/{category_id}", response_model=CategoryResponse, tags=["categories"])
def update_category(
    category_id: int,
    data: CategoryUpdate,
    db: Session = Depends(get_db),
) -> Any:
    """Update an existing category."""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(category, field, value)
    
    db.commit()
    db.refresh(category)
    return category


@router.delete("/categories/{category_id}", status_code=204, tags=["categories"])
def delete_category(category_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a category."""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    db.delete(category)
    db.commit()


# ============================================================================
# SubCategory Endpoints
# ============================================================================

@router.get("/subcategories", response_model=list[SubCategoryResponse], tags=["subcategories"])
def list_subcategories(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> list[Any]:
    """List all subcategories with pagination."""
    return db.query(SubCategory).offset(skip).limit(limit).all()


@router.get("/subcategories/count", tags=["subcategories"])
def count_subcategories(db: Session = Depends(get_db)) -> dict[str, int]:
    """Get total count of subcategories."""
    count = db.query(func.count(SubCategory.id)).scalar()
    return {"count": count}


@router.get("/subcategories/{subcategory_id}", response_model=SubCategoryResponse, tags=["subcategories"])
def get_subcategory(subcategory_id: int, db: Session = Depends(get_db)) -> Any:
    """Get a single subcategory by ID."""
    subcategory = db.query(SubCategory).filter(SubCategory.id == subcategory_id).first()
    if not subcategory:
        raise HTTPException(status_code=404, detail="SubCategory not found")
    return subcategory


@router.post("/subcategories", response_model=SubCategoryResponse, status_code=201, tags=["subcategories"])
def create_subcategory(data: SubCategoryCreate, db: Session = Depends(get_db)) -> Any:
    """Create a new subcategory."""
    subcategory = SubCategory(group_type="subcategory", **data.model_dump())
    db.add(subcategory)
    db.commit()
    db.refresh(subcategory)
    return subcategory


@router.put("/subcategories/{subcategory_id}", response_model=SubCategoryResponse, tags=["subcategories"])
def update_subcategory(
    subcategory_id: int,
    data: SubCategoryUpdate,
    db: Session = Depends(get_db),
) -> Any:
    """Update an existing subcategory."""
    subcategory = db.query(SubCategory).filter(SubCategory.id == subcategory_id).first()
    if not subcategory:
        raise HTTPException(status_code=404, detail="SubCategory not found")
    
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(subcategory, field, value)
    
    db.commit()
    db.refresh(subcategory)
    return subcategory


@router.delete("/subcategories/{subcategory_id}", status_code=204, tags=["subcategories"])
def delete_subcategory(subcategory_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a subcategory."""
    subcategory = db.query(SubCategory).filter(SubCategory.id == subcategory_id).first()
    if not subcategory:
        raise HTTPException(status_code=404, detail="SubCategory not found")
    
    db.delete(subcategory)
    db.commit()


# ============================================================================
# Topic Endpoints
# ============================================================================

@router.get("/topics", response_model=list[TopicResponse], tags=["topics"])
def list_topics(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> list[Any]:
    """List all topics with pagination."""
    return db.query(Topic).offset(skip).limit(limit).all()


@router.get("/topics/count", tags=["topics"])
def count_topics(db: Session = Depends(get_db)) -> dict[str, int]:
    """Get total count of topics."""
    count = db.query(func.count(Topic.id)).scalar()
    return {"count": count}


@router.get("/topics/{topic_id}", response_model=TopicResponse, tags=["topics"])
def get_topic(topic_id: int, db: Session = Depends(get_db)) -> Any:
    """Get a single topic by ID."""
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic


@router.post("/topics", response_model=TopicResponse, status_code=201, tags=["topics"])
def create_topic(data: TopicCreate, db: Session = Depends(get_db)) -> Any:
    """Create a new topic."""
    topic = Topic(group_type="topic", **data.model_dump())
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return topic


@router.put("/topics/{topic_id}", response_model=TopicResponse, tags=["topics"])
def update_topic(
    topic_id: int,
    data: TopicUpdate,
    db: Session = Depends(get_db),
) -> Any:
    """Update an existing topic."""
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(topic, field, value)
    
    db.commit()
    db.refresh(topic)
    return topic


@router.delete("/topics/{topic_id}", status_code=204, tags=["topics"])
def delete_topic(topic_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a topic."""
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    db.delete(topic)
    db.commit()


# ============================================================================
# Tag Endpoints
# ============================================================================

@router.get("/tags", response_model=list[TagResponse], tags=["tags"])
def list_tags(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> list[Any]:
    """List all tags with pagination."""
    return db.query(Tag).offset(skip).limit(limit).all()


@router.get("/tags/count", tags=["tags"])
def count_tags(db: Session = Depends(get_db)) -> dict[str, int]:
    """Get total count of tags."""
    count = db.query(func.count(Tag.id)).scalar()
    return {"count": count}


@router.get("/tags/{tag_id}", response_model=TagResponse, tags=["tags"])
def get_tag(tag_id: int, db: Session = Depends(get_db)) -> Any:
    """Get a single tag by ID."""
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return tag


@router.post("/tags", response_model=TagResponse, status_code=201, tags=["tags"])
def create_tag(data: TagCreate, db: Session = Depends(get_db)) -> Any:
    """Create a new tag."""
    tag = Tag(**data.model_dump())
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag


@router.put("/tags/{tag_id}", response_model=TagResponse, tags=["tags"])
def update_tag(
    tag_id: int,
    data: TagUpdate,
    db: Session = Depends(get_db),
) -> Any:
    """Update an existing tag."""
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(tag, field, value)
    
    db.commit()
    db.refresh(tag)
    return tag


@router.delete("/tags/{tag_id}", status_code=204, tags=["tags"])
def delete_tag(tag_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a tag."""
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    db.delete(tag)
    db.commit()
