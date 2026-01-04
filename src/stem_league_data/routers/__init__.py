"""API routers for STEM League Data."""

from stem_league_data.routers.crud import (
    metro_router, org_router, venue_router, flyer_router,
    person_router, staff_router, visitor_router,
    content_router, announcement_router,
    service_router, activity_router, occurrence_router, registration_router, rsvp_router,
    group_router, program_router, track_router, category_router, subcategory_router, topic_router, tag_router,
    meetup_router, pike13_service_router, p13_location_router,
    job_posting_router, instructor_assignment_router, instructor_evaluation_router,
)
from stem_league_data.routers.people import router as people_router
from stem_league_data.routers.events import router as events_router
from stem_league_data.routers.admin import router as admin_router

__all__ = [
    "metro_router", "org_router", "venue_router", "flyer_router",
    "person_router", "staff_router", "visitor_router",
    "content_router", "announcement_router",
    "service_router", "activity_router", "occurrence_router", "registration_router", "rsvp_router",
    "group_router", "program_router", "track_router", "category_router", "subcategory_router", "topic_router", "tag_router",
    "meetup_router", "pike13_service_router", "p13_location_router",
    "job_posting_router", "instructor_assignment_router", "instructor_evaluation_router",
    "people_router",
    "events_router",
    "admin_router",
]
