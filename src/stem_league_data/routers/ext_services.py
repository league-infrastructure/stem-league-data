"""Router for External Service resources: Meetup, Pike13Service, P13Location."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from stem_league_data.database import get_db
from stem_league_data.models import Meetup, Pike13Service, P13Location, Org, Metro
from stem_league_data.schemas.ext_services import (
    MeetupCreate, MeetupUpdate, MeetupResponse,
    Pike13ServiceCreate, Pike13ServiceUpdate, Pike13ServiceResponse,
    P13LocationCreate, P13LocationUpdate, P13LocationResponse,
)

router = APIRouter()


# ============================================================================
# Meetup Endpoints
# ============================================================================

@router.get("/meetups", response_model=list[MeetupResponse], tags=["meetups"])
def list_meetups(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    metro_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[Any]:
    """List all meetups with pagination and optional metro filter."""
    query = db.query(Meetup)
    if metro_id is not None:
        query = query.filter(Meetup.metro_id == metro_id)
    return query.offset(skip).limit(limit).all()


@router.get("/meetups/count", tags=["meetups"])
def count_meetups(db: Session = Depends(get_db)) -> dict[str, int]:
    """Get total count of meetups."""
    count = db.query(func.count(Meetup.id)).scalar()
    return {"count": count}


@router.get("/meetups/{meetup_id}", response_model=MeetupResponse, tags=["meetups"])
def get_meetup(meetup_id: int, db: Session = Depends(get_db)) -> Any:
    """Get a single meetup by ID."""
    meetup = db.query(Meetup).filter(Meetup.id == meetup_id).first()
    if not meetup:
        raise HTTPException(status_code=404, detail="Meetup not found")
    return meetup


@router.post("/meetups", response_model=MeetupResponse, status_code=201, tags=["meetups"])
def create_meetup(data: MeetupCreate, db: Session = Depends(get_db)) -> Any:
    """Create a new meetup."""
    # Validate foreign keys
    if data.metro_id is not None:
        metro = db.query(Metro).filter(Metro.id == data.metro_id).first()
        if not metro:
            raise HTTPException(status_code=400, detail=f"Metro with id {data.metro_id} not found")
    
    meetup = Meetup(**data.model_dump())
    db.add(meetup)
    db.commit()
    db.refresh(meetup)
    return meetup


@router.put("/meetups/{meetup_id}", response_model=MeetupResponse, tags=["meetups"])
def update_meetup(
    meetup_id: int,
    data: MeetupUpdate,
    db: Session = Depends(get_db),
) -> Any:
    """Update an existing meetup."""
    meetup = db.query(Meetup).filter(Meetup.id == meetup_id).first()
    if not meetup:
        raise HTTPException(status_code=404, detail="Meetup not found")
    
    update_data = data.model_dump(exclude_unset=True)
    
    # Validate foreign keys
    if "metro_id" in update_data and update_data["metro_id"] is not None:
        metro = db.query(Metro).filter(Metro.id == update_data["metro_id"]).first()
        if not metro:
            raise HTTPException(status_code=400, detail=f"Metro with id {update_data['metro_id']} not found")
    
    for field, value in update_data.items():
        setattr(meetup, field, value)
    
    db.commit()
    db.refresh(meetup)
    return meetup


@router.delete("/meetups/{meetup_id}", status_code=204, tags=["meetups"])
def delete_meetup(meetup_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a meetup."""
    meetup = db.query(Meetup).filter(Meetup.id == meetup_id).first()
    if not meetup:
        raise HTTPException(status_code=404, detail="Meetup not found")
    
    db.delete(meetup)
    db.commit()


# ============================================================================
# Pike13Service Endpoints
# ============================================================================

@router.get("/pike13-services", response_model=list[Pike13ServiceResponse], tags=["pike13-services"])
def list_pike13_services(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> list[Any]:
    """List all Pike13 services with pagination."""
    return db.query(Pike13Service).offset(skip).limit(limit).all()


@router.get("/pike13-services/count", tags=["pike13-services"])
def count_pike13_services(db: Session = Depends(get_db)) -> dict[str, int]:
    """Get total count of Pike13 services."""
    count = db.query(func.count(Pike13Service.id)).scalar()
    return {"count": count}


@router.get("/pike13-services/{p13_service_id}", response_model=Pike13ServiceResponse, tags=["pike13-services"])
def get_pike13_service(p13_service_id: int, db: Session = Depends(get_db)) -> Any:
    """Get a single Pike13 service by ID."""
    p13_service = db.query(Pike13Service).filter(Pike13Service.id == p13_service_id).first()
    if not p13_service:
        raise HTTPException(status_code=404, detail="Pike13Service not found")
    return p13_service


@router.post("/pike13-services", response_model=Pike13ServiceResponse, status_code=201, tags=["pike13-services"])
def create_pike13_service(data: Pike13ServiceCreate, db: Session = Depends(get_db)) -> Any:
    """Create a new Pike13 service."""
    p13_service = Pike13Service(**data.model_dump())
    db.add(p13_service)
    db.commit()
    db.refresh(p13_service)
    return p13_service


@router.put("/pike13-services/{p13_service_id}", response_model=Pike13ServiceResponse, tags=["pike13-services"])
def update_pike13_service(
    p13_service_id: int,
    data: Pike13ServiceUpdate,
    db: Session = Depends(get_db),
) -> Any:
    """Update an existing Pike13 service."""
    p13_service = db.query(Pike13Service).filter(Pike13Service.id == p13_service_id).first()
    if not p13_service:
        raise HTTPException(status_code=404, detail="Pike13Service not found")
    
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(p13_service, field, value)
    
    db.commit()
    db.refresh(p13_service)
    return p13_service


@router.delete("/pike13-services/{p13_service_id}", status_code=204, tags=["pike13-services"])
def delete_pike13_service(p13_service_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a Pike13 service."""
    p13_service = db.query(Pike13Service).filter(Pike13Service.id == p13_service_id).first()
    if not p13_service:
        raise HTTPException(status_code=404, detail="Pike13Service not found")
    
    db.delete(p13_service)
    db.commit()


# ============================================================================
# P13Location Endpoints
# ============================================================================

@router.get("/p13-locations", response_model=list[P13LocationResponse], tags=["p13-locations"])
def list_p13_locations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> list[Any]:
    """List all P13 locations with pagination."""
    return db.query(P13Location).offset(skip).limit(limit).all()


@router.get("/p13-locations/count", tags=["p13-locations"])
def count_p13_locations(db: Session = Depends(get_db)) -> dict[str, int]:
    """Get total count of P13 locations."""
    count = db.query(func.count(P13Location.id)).scalar()
    return {"count": count}


@router.get("/p13-locations/{p13_location_id}", response_model=P13LocationResponse, tags=["p13-locations"])
def get_p13_location(p13_location_id: int, db: Session = Depends(get_db)) -> Any:
    """Get a single P13 location by ID."""
    p13_location = db.query(P13Location).filter(P13Location.id == p13_location_id).first()
    if not p13_location:
        raise HTTPException(status_code=404, detail="P13Location not found")
    return p13_location


@router.post("/p13-locations", response_model=P13LocationResponse, status_code=201, tags=["p13-locations"])
def create_p13_location(data: P13LocationCreate, db: Session = Depends(get_db)) -> Any:
    """Create a new P13 location."""
    p13_location = P13Location(**data.model_dump())
    db.add(p13_location)
    db.commit()
    db.refresh(p13_location)
    return p13_location


@router.put("/p13-locations/{p13_location_id}", response_model=P13LocationResponse, tags=["p13-locations"])
def update_p13_location(
    p13_location_id: int,
    data: P13LocationUpdate,
    db: Session = Depends(get_db),
) -> Any:
    """Update an existing P13 location."""
    p13_location = db.query(P13Location).filter(P13Location.id == p13_location_id).first()
    if not p13_location:
        raise HTTPException(status_code=404, detail="P13Location not found")
    
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(p13_location, field, value)
    
    db.commit()
    db.refresh(p13_location)
    return p13_location


@router.delete("/p13-locations/{p13_location_id}", status_code=204, tags=["p13-locations"])
def delete_p13_location(p13_location_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a P13 location."""
    p13_location = db.query(P13Location).filter(P13Location.id == p13_location_id).first()
    if not p13_location:
        raise HTTPException(status_code=404, detail="P13Location not found")
    
    db.delete(p13_location)
    db.commit()
