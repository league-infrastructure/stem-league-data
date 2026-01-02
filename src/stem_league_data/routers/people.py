"""Router for People resources: Person, Staff, Visitor."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from stem_league_data.database import get_db
from stem_league_data.models import Person, Staff, Visitor, Metro
from stem_league_data.schemas.people import (
    PersonCreate, PersonUpdate, PersonResponse,
    StaffCreate, StaffCreateWithPerson, StaffUpdate, StaffResponse,
    VisitorCreate, VisitorUpdate, VisitorResponse,
)

router = APIRouter()


# ============================================================================
# Person Endpoints
# ============================================================================

@router.get("/persons", response_model=list[PersonResponse], tags=["persons"])
def list_persons(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    metro_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[Any]:
    """List all persons with pagination and optional metro filter."""
    query = db.query(Person)
    if metro_id is not None:
        query = query.filter(Person.metro_id == metro_id)
    return query.offset(skip).limit(limit).all()


@router.get("/persons/count", tags=["persons"])
def count_persons(db: Session = Depends(get_db)) -> dict[str, int]:
    """Get total count of persons."""
    count = db.query(func.count(Person.id)).scalar()
    return {"count": count}


@router.get("/persons/{person_id}", response_model=PersonResponse, tags=["persons"])
def get_person(person_id: int, db: Session = Depends(get_db)) -> Any:
    """Get a single person by ID."""
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return person


@router.post("/persons", response_model=PersonResponse, status_code=201, tags=["persons"])
def create_person(data: PersonCreate, db: Session = Depends(get_db)) -> Any:
    """Create a new person."""
    # Validate metro if provided
    if data.metro_id is not None:
        metro = db.query(Metro).filter(Metro.id == data.metro_id).first()
        if not metro:
            raise HTTPException(status_code=400, detail="Metro not found")
    
    person = Person(**data.model_dump())
    db.add(person)
    db.commit()
    db.refresh(person)
    return person


@router.put("/persons/{person_id}", response_model=PersonResponse, tags=["persons"])
def update_person(
    person_id: int,
    data: PersonUpdate,
    db: Session = Depends(get_db),
) -> Any:
    """Update an existing person."""
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    
    update_data = data.model_dump(exclude_unset=True)
    
    # Validate metro if being updated
    if "metro_id" in update_data and update_data["metro_id"] is not None:
        metro = db.query(Metro).filter(Metro.id == update_data["metro_id"]).first()
        if not metro:
            raise HTTPException(status_code=400, detail="Metro not found")
    
    for field, value in update_data.items():
        setattr(person, field, value)
    
    db.commit()
    db.refresh(person)
    return person


@router.delete("/persons/{person_id}", status_code=204, tags=["persons"])
def delete_person(person_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a person."""
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    
    db.delete(person)
    db.commit()


# ============================================================================
# Staff Endpoints
# ============================================================================

@router.get("/staff", response_model=list[StaffResponse], tags=["staff"])
def list_staff(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> list[Any]:
    """List all staff with pagination."""
    return db.query(Staff).offset(skip).limit(limit).all()


@router.get("/staff/count", tags=["staff"])
def count_staff(db: Session = Depends(get_db)) -> dict[str, int]:
    """Get total count of staff."""
    count = db.query(func.count(Staff.id)).scalar()
    return {"count": count}


@router.get("/staff/{staff_id}", response_model=StaffResponse, tags=["staff"])
def get_staff(staff_id: int, db: Session = Depends(get_db)) -> Any:
    """Get a single staff by ID."""
    staff = db.query(Staff).filter(Staff.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    return staff


@router.post("/staff", response_model=StaffResponse, status_code=201, tags=["staff"])
def create_staff(data: StaffCreate, db: Session = Depends(get_db)) -> Any:
    """Create a new staff record linked to an existing person."""
    # Validate person exists
    person = db.query(Person).filter(Person.id == data.person_id).first()
    if not person:
        raise HTTPException(status_code=400, detail="Person not found")
    
    # Check person doesn't already have staff record
    existing_staff = db.query(Staff).filter(Staff.person_id == data.person_id).first()
    if existing_staff:
        raise HTTPException(status_code=400, detail="Person already has a staff record")
    
    staff = Staff(**data.model_dump())
    db.add(staff)
    db.commit()
    db.refresh(staff)
    return staff


@router.post("/staff/with-person", response_model=StaffResponse, status_code=201, tags=["staff"])
def create_staff_with_person(data: StaffCreateWithPerson, db: Session = Depends(get_db)) -> Any:
    """Create a new staff record with a new person atomically."""
    # Create person first
    person_data = data.person.model_dump()
    
    # Validate metro if provided
    if person_data.get("metro_id") is not None:
        metro = db.query(Metro).filter(Metro.id == person_data["metro_id"]).first()
        if not metro:
            raise HTTPException(status_code=400, detail="Metro not found")
    
    person = Person(**person_data)
    db.add(person)
    db.flush()  # Get person ID
    
    # Create staff
    staff_data = data.model_dump(exclude={"person"})
    staff_data["person_id"] = person.id
    staff = Staff(**staff_data)
    db.add(staff)
    db.commit()
    db.refresh(staff)
    return staff


@router.put("/staff/{staff_id}", response_model=StaffResponse, tags=["staff"])
def update_staff(
    staff_id: int,
    data: StaffUpdate,
    db: Session = Depends(get_db),
) -> Any:
    """Update an existing staff record."""
    staff = db.query(Staff).filter(Staff.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(staff, field, value)
    
    db.commit()
    db.refresh(staff)
    return staff


@router.delete("/staff/{staff_id}", status_code=204, tags=["staff"])
def delete_staff(staff_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a staff record (does not delete the person)."""
    staff = db.query(Staff).filter(Staff.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    
    db.delete(staff)
    db.commit()


# ============================================================================
# Visitor Endpoints
# ============================================================================

@router.get("/visitors", response_model=list[VisitorResponse], tags=["visitors"])
def list_visitors(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> list[Any]:
    """List all visitors with pagination."""
    return db.query(Visitor).offset(skip).limit(limit).all()


@router.get("/visitors/count", tags=["visitors"])
def count_visitors(db: Session = Depends(get_db)) -> dict[str, int]:
    """Get total count of visitors."""
    count = db.query(func.count(Visitor.id)).scalar()
    return {"count": count}


@router.get("/visitors/{visitor_id}", response_model=VisitorResponse, tags=["visitors"])
def get_visitor(visitor_id: int, db: Session = Depends(get_db)) -> Any:
    """Get a single visitor by ID."""
    visitor = db.query(Visitor).filter(Visitor.id == visitor_id).first()
    if not visitor:
        raise HTTPException(status_code=404, detail="Visitor not found")
    return visitor


@router.post("/visitors", response_model=VisitorResponse, status_code=201, tags=["visitors"])
def create_visitor(data: VisitorCreate, db: Session = Depends(get_db)) -> Any:
    """Create a new visitor."""
    # Validate person if provided
    if data.person_id is not None:
        person = db.query(Person).filter(Person.id == data.person_id).first()
        if not person:
            raise HTTPException(status_code=400, detail="Person not found")
    
    # Validate guardian if provided
    if data.guardian_id is not None:
        guardian = db.query(Person).filter(Person.id == data.guardian_id).first()
        if not guardian:
            raise HTTPException(status_code=400, detail="Guardian not found")
    
    visitor = Visitor(**data.model_dump())
    db.add(visitor)
    db.commit()
    db.refresh(visitor)
    return visitor


@router.put("/visitors/{visitor_id}", response_model=VisitorResponse, tags=["visitors"])
def update_visitor(
    visitor_id: int,
    data: VisitorUpdate,
    db: Session = Depends(get_db),
) -> Any:
    """Update an existing visitor."""
    visitor = db.query(Visitor).filter(Visitor.id == visitor_id).first()
    if not visitor:
        raise HTTPException(status_code=404, detail="Visitor not found")
    
    update_data = data.model_dump(exclude_unset=True)
    
    # Validate person if being updated
    if "person_id" in update_data and update_data["person_id"] is not None:
        person = db.query(Person).filter(Person.id == update_data["person_id"]).first()
        if not person:
            raise HTTPException(status_code=400, detail="Person not found")
    
    # Validate guardian if being updated
    if "guardian_id" in update_data and update_data["guardian_id"] is not None:
        guardian = db.query(Person).filter(Person.id == update_data["guardian_id"]).first()
        if not guardian:
            raise HTTPException(status_code=400, detail="Guardian not found")
    
    for field, value in update_data.items():
        setattr(visitor, field, value)
    
    db.commit()
    db.refresh(visitor)
    return visitor


@router.delete("/visitors/{visitor_id}", status_code=204, tags=["visitors"])
def delete_visitor(visitor_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a visitor."""
    visitor = db.query(Visitor).filter(Visitor.id == visitor_id).first()
    if not visitor:
        raise HTTPException(status_code=404, detail="Visitor not found")
    
    db.delete(visitor)
    db.commit()
