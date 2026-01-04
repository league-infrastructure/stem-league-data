"""Router for specialized People resources: create staff with person."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from stem_league_data.database import get_db
from stem_league_data.models import Person, Staff, Metro
from stem_league_data.schemas.people import StaffCreateWithPerson, StaffResponse

router = APIRouter()


# ============================================================================
# Specialized Staff Endpoint
# ============================================================================

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
