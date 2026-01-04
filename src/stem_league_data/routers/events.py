"""Router for specialized Event resources: activity expand parameter."""

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from stem_league_data.database import get_db
from stem_league_data.models import Activity, Service, Content, Venue
from stem_league_data.schemas.events import ActivityResponse

router = APIRouter()

# Valid fields for activity expansion
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
def list_activities_with_expand(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    expand: str | None = Query(None),
    db: Session = Depends(get_db),
) -> list[Any]:
    """List activities with optional expand parameter for nested relations."""
    activities = db.query(Activity).offset(skip).limit(limit).all()
    
    # If no expand parameter, return basic responses
    if not expand:
        return activities
    
    # Parse expansions and build detailed responses
    expansions = _parse_expand_param(expand)
    if not expansions:
        return activities
    
