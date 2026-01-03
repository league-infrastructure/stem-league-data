"""Router for Event resources: Service, Activity, Occurrence, Registration, RSVP."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from stem_league_data.database import get_db
from stem_league_data.models import (
    Service, Activity, Occurrence, Registration, RSVP,
    Org, Venue, Person, Content,
)
from stem_league_data.schemas.events import (
    ServiceCreate, ServiceUpdate, ServiceResponse,
    ActivityCreate, ActivityUpdate, ActivityResponse,
    OccurrenceCreate, OccurrenceUpdate, OccurrenceResponse,
    RegistrationCreate, RegistrationUpdate, RegistrationResponse,
    RSVPCreate, RSVPUpdate, RSVPResponse,
)

router = APIRouter()


# ============================================================================
# Service Endpoints
# ============================================================================

@router.get("/services", response_model=list[ServiceResponse], tags=["services"])
def list_services(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    org_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[Any]:
    """List all services with pagination and optional org filter."""
    query = db.query(Service)
    if org_id is not None:
        query = query.filter(Service.org_id == org_id)
    return query.offset(skip).limit(limit).all()


@router.get("/services/count", tags=["services"])
def count_services(db: Session = Depends(get_db)) -> dict[str, int]:
    """Get total count of services."""
    count = db.query(func.count(Service.id)).scalar()
    return {"count": count}


@router.get("/services/{service_id}", response_model=ServiceResponse, tags=["services"])
def get_service(service_id: int, db: Session = Depends(get_db)) -> Any:
    """Get a single service by ID."""
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return service


@router.post("/services", response_model=ServiceResponse, status_code=201, tags=["services"])
def create_service(data: ServiceCreate, db: Session = Depends(get_db)) -> Any:
    """Create a new service."""
    # Validate content_id if provided
    if data.content_id is not None:
        content = db.query(Content).filter(Content.id == data.content_id).first()
        if not content:
            raise HTTPException(status_code=400, detail=f"Content with id {data.content_id} not found")
    
    # Validate parent_service_id if provided
    if data.parent_service_id is not None:
        parent = db.query(Service).filter(Service.id == data.parent_service_id).first()
        if not parent:
            raise HTTPException(status_code=400, detail=f"Parent service with id {data.parent_service_id} not found")
    
    # Handle inline content creation
    service_data = data.model_dump(exclude={"content", "topic_ids", "track_ids", "category_ids", "subcategory_ids"})
    if data.content is not None and data.content_id is None:
        content = Content(**data.content.model_dump())
        db.add(content)
        db.flush()
        service_data["content_id"] = content.id
    
    service = Service(**service_data)
    db.add(service)
    db.commit()
    db.refresh(service)
    return service


@router.put("/services/{service_id}", response_model=ServiceResponse, tags=["services"])
def update_service(
    service_id: int,
    data: ServiceUpdate,
    db: Session = Depends(get_db),
) -> Any:
    """Update an existing service."""
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    update_data = data.model_dump(exclude_unset=True)
    
    # Validate content_id if provided
    if "content_id" in update_data and update_data["content_id"] is not None:
        content = db.query(Content).filter(Content.id == update_data["content_id"]).first()
        if not content:
            raise HTTPException(status_code=400, detail=f"Content with id {update_data['content_id']} not found")
    
    # Validate parent_service_id if provided
    if "parent_service_id" in update_data and update_data["parent_service_id"] is not None:
        parent = db.query(Service).filter(Service.id == update_data["parent_service_id"]).first()
        if not parent:
            raise HTTPException(status_code=400, detail=f"Parent service with id {update_data['parent_service_id']} not found")
    
    # Exclude many-to-many relationship IDs from direct update
    for key in ["topic_ids", "track_ids", "category_ids", "subcategory_ids"]:
        update_data.pop(key, None)
    
    for field, value in update_data.items():
        setattr(service, field, value)
    
    db.commit()
    db.refresh(service)
    return service


@router.delete("/services/{service_id}", status_code=204, tags=["services"])
def delete_service(service_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a service."""
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    db.delete(service)
    db.commit()


# ============================================================================
# Activity Endpoints
# ============================================================================

VALID_ACTIVITY_EXPANSIONS = {"service", "venue", "content", "cta", "enrollment", "all"}


def _parse_expand_param(expand: str | None) -> set[str]:
    """Parse the expand query parameter into a set of field names."""
    if not expand:
        return set()
    fields = {f.strip().lower() for f in expand.split(",")}
    if "all" in fields:
        return VALID_ACTIVITY_EXPANSIONS - {"all"}
    return fields & VALID_ACTIVITY_EXPANSIONS


def _content_to_dict(content: Any) -> dict[str, Any]:
    """Convert a Content model to a dictionary."""
    return {
        "id": content.id,
        "title": content.title,
        "blurb": content.blurb,
        "description": content.description,
        "for": content.for_,
        "requirements": content.requirements,
        "cta_text": content.cta_text,
        "cta_url": content.cta_url,
    }


def _build_detailed_activity(activity: Activity, expansions: set[str], db: Session) -> dict[str, Any]:
    """Build a detailed activity response with expanded relations."""
    from stem_league_data.schemas.events import ActivityResponse
    
    # Start with base activity data
    result = ActivityResponse.model_validate(activity).model_dump()
    
    # Add expanded relations
    if "service" in expansions and activity.service_id:
        service = activity.service or db.query(Service).filter(Service.id == activity.service_id).first()
        if service:
            service_data = {
                "id": service.id,
                "slug": service.slug,
                "grade": service.grade,
                "level": service.level,
                "content": None,
            }
            # Also expand service's content if available
            if service.content_id:
                svc_content = service.content or db.query(Content).filter(Content.id == service.content_id).first()
                if svc_content:
                    service_data["content"] = _content_to_dict(svc_content)
            result["service"] = service_data
    
    if "venue" in expansions and activity.venue_id:
        venue = activity.venue or db.query(Venue).filter(Venue.id == activity.venue_id).first()
        if venue:
            result["venue"] = {
                "id": venue.id,
                "name": venue.name,
                "address": venue.address,
                "city": venue.city,
                "state": venue.state,
                "zip_code": venue.zip_code,
                "capacity": venue.capacity,
                "has_computers": venue.has_computers,
            }
    
    if "content" in expansions and activity.content_id:
        content = activity.content or db.query(Content).filter(Content.id == activity.content_id).first()
        if content:
            result["content"] = _content_to_dict(content)
    
    if "cta" in expansions and activity.cta_id:
        cta = activity.cta or db.query(Content).filter(Content.id == activity.cta_id).first()
        if cta:
            result["cta"] = _content_to_dict(cta)
    
    if "enrollment" in expansions and activity.enrollment_id:
        enrollment = activity.enrollment or db.query(Content).filter(Content.id == activity.enrollment_id).first()
        if enrollment:
            result["enrollment"] = _content_to_dict(enrollment)
    
    return result


@router.get("/activities", response_model=list[ActivityResponse], tags=["activities"])
def list_activities(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    org_id: int | None = None,
    venue_id: int | None = None,
    service_id: int | None = None,
    expand: str | None = Query(None, description="Comma-separated relations to expand: service, venue, content, cta, enrollment, or 'all'"),
    db: Session = Depends(get_db),
) -> Any:
    """List all activities with pagination and optional filters.
    
    Use the `expand` parameter to include related objects in the response.
    Example: ?expand=service,venue or ?expand=all
    """
    query = db.query(Activity)
    if org_id is not None:
        query = query.filter(Activity.org_id == org_id)
    if venue_id is not None:
        query = query.filter(Activity.venue_id == venue_id)
    if service_id is not None:
        query = query.filter(Activity.service_id == service_id)
    
    activities = query.offset(skip).limit(limit).all()
    
    expansions = _parse_expand_param(expand)
    if expansions:
        return [_build_detailed_activity(a, expansions, db) for a in activities]
    
    return activities


@router.get("/activities/count", tags=["activities"])
def count_activities(db: Session = Depends(get_db)) -> dict[str, int]:
    """Get total count of activities."""
    count = db.query(func.count(Activity.id)).scalar()
    return {"count": count}


@router.get("/activities/{activity_id}", tags=["activities"])
def get_activity(
    activity_id: int,
    expand: str | None = Query(None, description="Comma-separated relations to expand: service, venue, content, cta, enrollment, or 'all'"),
    db: Session = Depends(get_db),
) -> Any:
    """Get a single activity by ID.
    
    Use the `expand` parameter to include related objects in the response.
    Example: ?expand=service,venue,content or ?expand=all
    """
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    expansions = _parse_expand_param(expand)
    if expansions:
        return _build_detailed_activity(activity, expansions, db)
    
    return activity


@router.post("/activities", response_model=ActivityResponse, status_code=201, tags=["activities"])
def create_activity(data: ActivityCreate, db: Session = Depends(get_db)) -> Any:
    """Create a new activity."""
    # Validate foreign keys
    if data.org_id is not None:
        org = db.query(Org).filter(Org.id == data.org_id).first()
        if not org:
            raise HTTPException(status_code=400, detail=f"Org with id {data.org_id} not found")
    
    if data.venue_id is not None:
        venue = db.query(Venue).filter(Venue.id == data.venue_id).first()
        if not venue:
            raise HTTPException(status_code=400, detail=f"Venue with id {data.venue_id} not found")
    
    if data.service_id is not None:
        service = db.query(Service).filter(Service.id == data.service_id).first()
        if not service:
            raise HTTPException(status_code=400, detail=f"Service with id {data.service_id} not found")
    
    if data.content_id is not None:
        content = db.query(Content).filter(Content.id == data.content_id).first()
        if not content:
            raise HTTPException(status_code=400, detail=f"Content with id {data.content_id} not found")
    
    # Exclude many-to-many relationship IDs and inline objects from model_dump
    activity_data = data.model_dump(exclude={
        "service", "content", "schedule",
        "program_ids", "track_ids", "category_ids", "subcategory_ids",
        "topic_ids", "tag_ids"
    })
    
    # Handle inline service creation
    if data.service is not None and data.service_id is None:
        service_data = data.service.model_dump(exclude={"content", "topic_ids", "track_ids", "category_ids", "subcategory_ids"})
        service = Service(**service_data)
        db.add(service)
        db.flush()
        activity_data["service_id"] = service.id
    
    # Handle inline content creation
    if data.content is not None and data.content_id is None:
        content = Content(**data.content.model_dump())
        db.add(content)
        db.flush()
        activity_data["content_id"] = content.id
    
    activity = Activity(**activity_data)
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


@router.put("/activities/{activity_id}", response_model=ActivityResponse, tags=["activities"])
def update_activity(
    activity_id: int,
    data: ActivityUpdate,
    db: Session = Depends(get_db),
) -> Any:
    """Update an existing activity."""
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    update_data = data.model_dump(exclude_unset=True)
    
    # Validate foreign keys
    if "org_id" in update_data and update_data["org_id"] is not None:
        org = db.query(Org).filter(Org.id == update_data["org_id"]).first()
        if not org:
            raise HTTPException(status_code=400, detail=f"Org with id {update_data['org_id']} not found")
    
    if "venue_id" in update_data and update_data["venue_id"] is not None:
        venue = db.query(Venue).filter(Venue.id == update_data["venue_id"]).first()
        if not venue:
            raise HTTPException(status_code=400, detail=f"Venue with id {update_data['venue_id']} not found")
    
    if "service_id" in update_data and update_data["service_id"] is not None:
        service = db.query(Service).filter(Service.id == update_data["service_id"]).first()
        if not service:
            raise HTTPException(status_code=400, detail=f"Service with id {update_data['service_id']} not found")
    
    # Exclude many-to-many relationship IDs from direct update
    for key in ["program_ids", "track_ids", "category_ids", "subcategory_ids", "topic_ids", "tag_ids", "schedule"]:
        update_data.pop(key, None)
    
    for field, value in update_data.items():
        setattr(activity, field, value)
    
    db.commit()
    db.refresh(activity)
    return activity


@router.delete("/activities/{activity_id}", status_code=204, tags=["activities"])
def delete_activity(activity_id: int, db: Session = Depends(get_db)) -> None:
    """Delete an activity."""
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    db.delete(activity)
    db.commit()


# ============================================================================
# Occurrence Endpoints
# ============================================================================

@router.get("/occurrences", response_model=list[OccurrenceResponse], tags=["occurrences"])
def list_occurrences(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    activity_id: int | None = None,
    venue_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[Any]:
    """List all occurrences with pagination and optional filters."""
    query = db.query(Occurrence)
    if activity_id is not None:
        query = query.filter(Occurrence.activity_id == activity_id)
    if venue_id is not None:
        query = query.filter(Occurrence.venue_id == venue_id)
    return query.offset(skip).limit(limit).all()


@router.get("/occurrences/count", tags=["occurrences"])
def count_occurrences(db: Session = Depends(get_db)) -> dict[str, int]:
    """Get total count of occurrences."""
    count = db.query(func.count(Occurrence.id)).scalar()
    return {"count": count}


@router.get("/occurrences/{occurrence_id}", response_model=OccurrenceResponse, tags=["occurrences"])
def get_occurrence(occurrence_id: int, db: Session = Depends(get_db)) -> Any:
    """Get a single occurrence by ID."""
    occurrence = db.query(Occurrence).filter(Occurrence.id == occurrence_id).first()
    if not occurrence:
        raise HTTPException(status_code=404, detail="Occurrence not found")
    return occurrence


@router.post("/occurrences", response_model=OccurrenceResponse, status_code=201, tags=["occurrences"])
def create_occurrence(data: OccurrenceCreate, db: Session = Depends(get_db)) -> Any:
    """Create a new occurrence."""
    # Validate foreign keys
    if data.activity_id is not None:
        activity = db.query(Activity).filter(Activity.id == data.activity_id).first()
        if not activity:
            raise HTTPException(status_code=400, detail=f"Activity with id {data.activity_id} not found")
    
    occurrence = Occurrence(**data.model_dump())
    db.add(occurrence)
    db.commit()
    db.refresh(occurrence)
    return occurrence


@router.put("/occurrences/{occurrence_id}", response_model=OccurrenceResponse, tags=["occurrences"])
def update_occurrence(
    occurrence_id: int,
    data: OccurrenceUpdate,
    db: Session = Depends(get_db),
) -> Any:
    """Update an existing occurrence."""
    occurrence = db.query(Occurrence).filter(Occurrence.id == occurrence_id).first()
    if not occurrence:
        raise HTTPException(status_code=404, detail="Occurrence not found")
    
    update_data = data.model_dump(exclude_unset=True)
    
    # Validate foreign keys
    if "activity_id" in update_data and update_data["activity_id"] is not None:
        activity = db.query(Activity).filter(Activity.id == update_data["activity_id"]).first()
        if not activity:
            raise HTTPException(status_code=400, detail=f"Activity with id {update_data['activity_id']} not found")
    
    for field, value in update_data.items():
        setattr(occurrence, field, value)
    
    db.commit()
    db.refresh(occurrence)
    return occurrence


@router.delete("/occurrences/{occurrence_id}", status_code=204, tags=["occurrences"])
def delete_occurrence(occurrence_id: int, db: Session = Depends(get_db)) -> None:
    """Delete an occurrence."""
    occurrence = db.query(Occurrence).filter(Occurrence.id == occurrence_id).first()
    if not occurrence:
        raise HTTPException(status_code=404, detail="Occurrence not found")
    
    db.delete(occurrence)
    db.commit()


# ============================================================================
# Registration Endpoints
# ============================================================================

@router.get("/registrations", response_model=list[RegistrationResponse], tags=["registrations"])
def list_registrations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    activity_id: int | None = None,
    person_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[Any]:
    """List all registrations with pagination and optional filters."""
    query = db.query(Registration)
    if activity_id is not None:
        query = query.filter(Registration.activity_id == activity_id)
    if person_id is not None:
        query = query.filter(Registration.person_id == person_id)
    return query.offset(skip).limit(limit).all()


@router.get("/registrations/count", tags=["registrations"])
def count_registrations(db: Session = Depends(get_db)) -> dict[str, int]:
    """Get total count of registrations."""
    count = db.query(func.count(Registration.id)).scalar()
    return {"count": count}


@router.get("/registrations/{registration_id}", response_model=RegistrationResponse, tags=["registrations"])
def get_registration(registration_id: int, db: Session = Depends(get_db)) -> Any:
    """Get a single registration by ID."""
    registration = db.query(Registration).filter(Registration.id == registration_id).first()
    if not registration:
        raise HTTPException(status_code=404, detail="Registration not found")
    return registration


@router.post("/registrations", response_model=RegistrationResponse, status_code=201, tags=["registrations"])
def create_registration(data: RegistrationCreate, db: Session = Depends(get_db)) -> Any:
    """Create a new registration."""
    # Validate foreign keys
    activity = db.query(Activity).filter(Activity.id == data.activity_id).first()
    if not activity:
        raise HTTPException(status_code=400, detail=f"Activity with id {data.activity_id} not found")
    
    person = db.query(Person).filter(Person.id == data.person_id).first()
    if not person:
        raise HTTPException(status_code=400, detail=f"Person with id {data.person_id} not found")
    
    registration = Registration(**data.model_dump())
    db.add(registration)
    db.commit()
    db.refresh(registration)
    return registration


@router.put("/registrations/{registration_id}", response_model=RegistrationResponse, tags=["registrations"])
def update_registration(
    registration_id: int,
    data: RegistrationUpdate,
    db: Session = Depends(get_db),
) -> Any:
    """Update an existing registration."""
    registration = db.query(Registration).filter(Registration.id == registration_id).first()
    if not registration:
        raise HTTPException(status_code=404, detail="Registration not found")
    
    update_data = data.model_dump(exclude_unset=True)
    
    # Validate foreign keys
    if "activity_id" in update_data:
        activity = db.query(Activity).filter(Activity.id == update_data["activity_id"]).first()
        if not activity:
            raise HTTPException(status_code=400, detail=f"Activity with id {update_data['activity_id']} not found")
    
    if "person_id" in update_data:
        person = db.query(Person).filter(Person.id == update_data["person_id"]).first()
        if not person:
            raise HTTPException(status_code=400, detail=f"Person with id {update_data['person_id']} not found")
    
    for field, value in update_data.items():
        setattr(registration, field, value)
    
    db.commit()
    db.refresh(registration)
    return registration


@router.delete("/registrations/{registration_id}", status_code=204, tags=["registrations"])
def delete_registration(registration_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a registration."""
    registration = db.query(Registration).filter(Registration.id == registration_id).first()
    if not registration:
        raise HTTPException(status_code=404, detail="Registration not found")
    
    db.delete(registration)
    db.commit()


# ============================================================================
# RSVP Endpoints
# ============================================================================

@router.get("/rsvps", response_model=list[RSVPResponse], tags=["rsvps"])
def list_rsvps(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    occurrence_id: int | None = None,
    person_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[Any]:
    """List all RSVPs with pagination and optional filters."""
    query = db.query(RSVP)
    if occurrence_id is not None:
        query = query.filter(RSVP.occurrence_id == occurrence_id)
    if person_id is not None:
        query = query.filter(RSVP.person_id == person_id)
    return query.offset(skip).limit(limit).all()


@router.get("/rsvps/count", tags=["rsvps"])
def count_rsvps(db: Session = Depends(get_db)) -> dict[str, int]:
    """Get total count of RSVPs."""
    count = db.query(func.count(RSVP.id)).scalar()
    return {"count": count}


@router.get("/rsvps/{rsvp_id}", response_model=RSVPResponse, tags=["rsvps"])
def get_rsvp(rsvp_id: int, db: Session = Depends(get_db)) -> Any:
    """Get a single RSVP by ID."""
    rsvp = db.query(RSVP).filter(RSVP.id == rsvp_id).first()
    if not rsvp:
        raise HTTPException(status_code=404, detail="RSVP not found")
    return rsvp


@router.post("/rsvps", response_model=RSVPResponse, status_code=201, tags=["rsvps"])
def create_rsvp(data: RSVPCreate, db: Session = Depends(get_db)) -> Any:
    """Create a new RSVP."""
    # Validate foreign keys
    occurrence = db.query(Occurrence).filter(Occurrence.id == data.occurrence_id).first()
    if not occurrence:
        raise HTTPException(status_code=400, detail=f"Occurrence with id {data.occurrence_id} not found")
    
    person = db.query(Person).filter(Person.id == data.person_id).first()
    if not person:
        raise HTTPException(status_code=400, detail=f"Person with id {data.person_id} not found")
    
    rsvp = RSVP(**data.model_dump())
    db.add(rsvp)
    db.commit()
    db.refresh(rsvp)
    return rsvp


@router.put("/rsvps/{rsvp_id}", response_model=RSVPResponse, tags=["rsvps"])
def update_rsvp(
    rsvp_id: int,
    data: RSVPUpdate,
    db: Session = Depends(get_db),
) -> Any:
    """Update an existing RSVP."""
    rsvp = db.query(RSVP).filter(RSVP.id == rsvp_id).first()
    if not rsvp:
        raise HTTPException(status_code=404, detail="RSVP not found")
    
    update_data = data.model_dump(exclude_unset=True)
    
    # Validate foreign keys
    if "occurrence_id" in update_data:
        occurrence = db.query(Occurrence).filter(Occurrence.id == update_data["occurrence_id"]).first()
        if not occurrence:
            raise HTTPException(status_code=400, detail=f"Occurrence with id {update_data['occurrence_id']} not found")
    
    if "person_id" in update_data:
        person = db.query(Person).filter(Person.id == update_data["person_id"]).first()
        if not person:
            raise HTTPException(status_code=400, detail=f"Person with id {update_data['person_id']} not found")
    
    for field, value in update_data.items():
        setattr(rsvp, field, value)
    
    db.commit()
    db.refresh(rsvp)
    return rsvp


@router.delete("/rsvps/{rsvp_id}", status_code=204, tags=["rsvps"])
def delete_rsvp(rsvp_id: int, db: Session = Depends(get_db)) -> None:
    """Delete an RSVP."""
    rsvp = db.query(RSVP).filter(RSVP.id == rsvp_id).first()
    if not rsvp:
        raise HTTPException(status_code=404, detail="RSVP not found")
    
    db.delete(rsvp)
    db.commit()
