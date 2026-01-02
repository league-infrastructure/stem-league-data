"""Router for Place resources: Metro, Org, Venue, Flyer."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from stem_league_data.database import get_db
from stem_league_data.models import Metro, Org, Venue, Flyer
from stem_league_data.schemas.place import (
    MetroCreate, MetroUpdate, MetroResponse,
    OrgCreate, OrgUpdate, OrgResponse,
    VenueCreate, VenueUpdate, VenueResponse,
    FlyerCreate, FlyerUpdate, FlyerResponse,
)

router = APIRouter()


# ============================================================================
# Metro Endpoints
# ============================================================================

@router.get("/metros", response_model=list[MetroResponse], tags=["metros"])
def list_metros(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> list[Any]:
    """List all metros with pagination."""
    return db.query(Metro).offset(skip).limit(limit).all()


@router.get("/metros/count", tags=["metros"])
def count_metros(db: Session = Depends(get_db)) -> dict[str, int]:
    """Get total count of metros."""
    count = db.query(func.count(Metro.id)).scalar()
    return {"count": count}


@router.get("/metros/{metro_id}", response_model=MetroResponse, tags=["metros"])
def get_metro(metro_id: int, db: Session = Depends(get_db)) -> Any:
    """Get a single metro by ID."""
    metro = db.query(Metro).filter(Metro.id == metro_id).first()
    if not metro:
        raise HTTPException(status_code=404, detail="Metro not found")
    return metro


@router.post("/metros", response_model=MetroResponse, status_code=201, tags=["metros"])
def create_metro(data: MetroCreate, db: Session = Depends(get_db)) -> Any:
    """Create a new metro."""
    metro = Metro(**data.model_dump())
    db.add(metro)
    db.commit()
    db.refresh(metro)
    return metro


@router.put("/metros/{metro_id}", response_model=MetroResponse, tags=["metros"])
def update_metro(
    metro_id: int,
    data: MetroUpdate,
    db: Session = Depends(get_db),
) -> Any:
    """Update an existing metro."""
    metro = db.query(Metro).filter(Metro.id == metro_id).first()
    if not metro:
        raise HTTPException(status_code=404, detail="Metro not found")
    
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(metro, field, value)
    
    db.commit()
    db.refresh(metro)
    return metro


@router.delete("/metros/{metro_id}", status_code=204, tags=["metros"])
def delete_metro(metro_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a metro."""
    metro = db.query(Metro).filter(Metro.id == metro_id).first()
    if not metro:
        raise HTTPException(status_code=404, detail="Metro not found")
    
    db.delete(metro)
    db.commit()


# ============================================================================
# Org Endpoints
# ============================================================================

@router.get("/orgs", response_model=list[OrgResponse], tags=["orgs"])
def list_orgs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    metro_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[Any]:
    """List all orgs with pagination and optional metro filter."""
    query = db.query(Org)
    if metro_id is not None:
        query = query.filter(Org.metro_id == metro_id)
    return query.offset(skip).limit(limit).all()


@router.get("/orgs/count", tags=["orgs"])
def count_orgs(db: Session = Depends(get_db)) -> dict[str, int]:
    """Get total count of orgs."""
    count = db.query(func.count(Org.id)).scalar()
    return {"count": count}


@router.get("/orgs/{org_id}", response_model=OrgResponse, tags=["orgs"])
def get_org(org_id: int, db: Session = Depends(get_db)) -> Any:
    """Get a single org by ID."""
    org = db.query(Org).filter(Org.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Org not found")
    return org


@router.post("/orgs", response_model=OrgResponse, status_code=201, tags=["orgs"])
def create_org(data: OrgCreate, db: Session = Depends(get_db)) -> Any:
    """Create a new org.
    
    Requires a valid metro_id.
    """
    # Validate metro exists
    metro = db.query(Metro).filter(Metro.id == data.metro_id).first()
    if not metro:
        raise HTTPException(status_code=400, detail="Metro not found")
    
    org = Org(**data.model_dump())
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


@router.put("/orgs/{org_id}", response_model=OrgResponse, tags=["orgs"])
def update_org(
    org_id: int,
    data: OrgUpdate,
    db: Session = Depends(get_db),
) -> Any:
    """Update an existing org."""
    org = db.query(Org).filter(Org.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Org not found")
    
    update_data = data.model_dump(exclude_unset=True)
    
    # Validate metro if being updated
    if "metro_id" in update_data and update_data["metro_id"] is not None:
        metro = db.query(Metro).filter(Metro.id == update_data["metro_id"]).first()
        if not metro:
            raise HTTPException(status_code=400, detail="Metro not found")
    
    for field, value in update_data.items():
        setattr(org, field, value)
    
    db.commit()
    db.refresh(org)
    return org


@router.delete("/orgs/{org_id}", status_code=204, tags=["orgs"])
def delete_org(org_id: int, db: Session = Depends(get_db)) -> None:
    """Delete an org."""
    org = db.query(Org).filter(Org.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Org not found")
    
    db.delete(org)
    db.commit()


# ============================================================================
# Venue Endpoints
# ============================================================================

@router.get("/venues", response_model=list[VenueResponse], tags=["venues"])
def list_venues(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    metro_id: int | None = None,
    org_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[Any]:
    """List all venues with pagination and optional filters."""
    query = db.query(Venue)
    if metro_id is not None:
        query = query.filter(Venue.metro_id == metro_id)
    if org_id is not None:
        query = query.filter(Venue.org_id == org_id)
    return query.offset(skip).limit(limit).all()


@router.get("/venues/count", tags=["venues"])
def count_venues(db: Session = Depends(get_db)) -> dict[str, int]:
    """Get total count of venues."""
    count = db.query(func.count(Venue.id)).scalar()
    return {"count": count}


@router.get("/venues/{venue_id}", response_model=VenueResponse, tags=["venues"])
def get_venue(venue_id: int, db: Session = Depends(get_db)) -> Any:
    """Get a single venue by ID."""
    venue = db.query(Venue).filter(Venue.id == venue_id).first()
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")
    return venue


@router.post("/venues", response_model=VenueResponse, status_code=201, tags=["venues"])
def create_venue(data: VenueCreate, db: Session = Depends(get_db)) -> Any:
    """Create a new venue.
    
    Requires a valid metro_id. Optionally links to an org.
    """
    # Validate metro exists
    metro = db.query(Metro).filter(Metro.id == data.metro_id).first()
    if not metro:
        raise HTTPException(status_code=400, detail="Metro not found")
    
    # Validate org if provided
    if data.org_id is not None:
        org = db.query(Org).filter(Org.id == data.org_id).first()
        if not org:
            raise HTTPException(status_code=400, detail="Org not found")
    
    venue = Venue(**data.model_dump())
    db.add(venue)
    db.commit()
    db.refresh(venue)
    return venue


@router.put("/venues/{venue_id}", response_model=VenueResponse, tags=["venues"])
def update_venue(
    venue_id: int,
    data: VenueUpdate,
    db: Session = Depends(get_db),
) -> Any:
    """Update an existing venue."""
    venue = db.query(Venue).filter(Venue.id == venue_id).first()
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")
    
    update_data = data.model_dump(exclude_unset=True)
    
    # Validate metro if being updated
    if "metro_id" in update_data and update_data["metro_id"] is not None:
        metro = db.query(Metro).filter(Metro.id == update_data["metro_id"]).first()
        if not metro:
            raise HTTPException(status_code=400, detail="Metro not found")
    
    # Validate org if being updated
    if "org_id" in update_data and update_data["org_id"] is not None:
        org = db.query(Org).filter(Org.id == update_data["org_id"]).first()
        if not org:
            raise HTTPException(status_code=400, detail="Org not found")
    
    for field, value in update_data.items():
        setattr(venue, field, value)
    
    db.commit()
    db.refresh(venue)
    return venue


@router.delete("/venues/{venue_id}", status_code=204, tags=["venues"])
def delete_venue(venue_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a venue."""
    venue = db.query(Venue).filter(Venue.id == venue_id).first()
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")
    
    db.delete(venue)
    db.commit()


# ============================================================================
# Flyer Endpoints
# ============================================================================

@router.get("/flyers", response_model=list[FlyerResponse], tags=["flyers"])
def list_flyers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> list[Any]:
    """List all flyers with pagination."""
    return db.query(Flyer).offset(skip).limit(limit).all()


@router.get("/flyers/count", tags=["flyers"])
def count_flyers(db: Session = Depends(get_db)) -> dict[str, int]:
    """Get total count of flyers."""
    count = db.query(func.count(Flyer.id)).scalar()
    return {"count": count}


@router.get("/flyers/{flyer_id}", response_model=FlyerResponse, tags=["flyers"])
def get_flyer(flyer_id: int, db: Session = Depends(get_db)) -> Any:
    """Get a single flyer by ID."""
    flyer = db.query(Flyer).filter(Flyer.id == flyer_id).first()
    if not flyer:
        raise HTTPException(status_code=404, detail="Flyer not found")
    return flyer


@router.post("/flyers", response_model=FlyerResponse, status_code=201, tags=["flyers"])
def create_flyer(data: FlyerCreate, db: Session = Depends(get_db)) -> Any:
    """Create a new flyer."""
    flyer = Flyer(**data.model_dump())
    db.add(flyer)
    db.commit()
    db.refresh(flyer)
    return flyer


@router.put("/flyers/{flyer_id}", response_model=FlyerResponse, tags=["flyers"])
def update_flyer(
    flyer_id: int,
    data: FlyerUpdate,
    db: Session = Depends(get_db),
) -> Any:
    """Update an existing flyer."""
    flyer = db.query(Flyer).filter(Flyer.id == flyer_id).first()
    if not flyer:
        raise HTTPException(status_code=404, detail="Flyer not found")
    
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(flyer, field, value)
    
    db.commit()
    db.refresh(flyer)
    return flyer


@router.delete("/flyers/{flyer_id}", status_code=204, tags=["flyers"])
def delete_flyer(flyer_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a flyer."""
    flyer = db.query(Flyer).filter(Flyer.id == flyer_id).first()
    if not flyer:
        raise HTTPException(status_code=404, detail="Flyer not found")
    
    db.delete(flyer)
    db.commit()
