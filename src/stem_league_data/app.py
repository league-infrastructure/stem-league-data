"""FastAPI application for STEM League Data."""

# Apply patches for library compatibility before importing routers
from stem_league_data.patches import patch_fastapi_crudrouter_pydantic_v2
patch_fastapi_crudrouter_pydantic_v2()

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from stem_league_data.database import create_tables
from stem_league_data.routers import (
    metro_router, org_router, venue_router, flyer_router,
    person_router, staff_router, visitor_router,
    content_router, announcement_router,
    service_router, activity_router, occurrence_router, registration_router, rsvp_router,
    group_router, program_router, track_router, category_router, subcategory_router, topic_router, tag_router,
    meetup_router, pike13_service_router, p13_location_router,
    job_posting_router, instructor_assignment_router, instructor_evaluation_router,
    people_router,
    events_router,
    admin_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Lifespan context manager for startup/shutdown events."""
    # Startup
    create_tables()
    yield
    # Shutdown (nothing to do)


app = FastAPI(
    title="STEM League Data",
    description="Data model and API for the League STEM network",
    version="0.1.0",
    lifespan=lifespan,
)

# Include all CRUD routers with /api prefix
app.include_router(metro_router, prefix="/api")
app.include_router(org_router, prefix="/api")
app.include_router(venue_router, prefix="/api")
app.include_router(flyer_router, prefix="/api")
app.include_router(person_router, prefix="/api")
app.include_router(staff_router, prefix="/api")
app.include_router(visitor_router, prefix="/api")
app.include_router(content_router, prefix="/api")
app.include_router(announcement_router, prefix="/api")
app.include_router(service_router, prefix="/api")
app.include_router(activity_router, prefix="/api")
app.include_router(occurrence_router, prefix="/api")
app.include_router(registration_router, prefix="/api")
app.include_router(rsvp_router, prefix="/api")
app.include_router(group_router, prefix="/api")
app.include_router(program_router, prefix="/api")
app.include_router(track_router, prefix="/api")
app.include_router(category_router, prefix="/api")
app.include_router(subcategory_router, prefix="/api")
app.include_router(topic_router, prefix="/api")
app.include_router(tag_router, prefix="/api")
app.include_router(meetup_router, prefix="/api")
app.include_router(pike13_service_router, prefix="/api")
app.include_router(p13_location_router, prefix="/api")
app.include_router(job_posting_router, prefix="/api")
app.include_router(instructor_assignment_router, prefix="/api")
app.include_router(instructor_evaluation_router, prefix="/api")

# Include specialized routers
app.include_router(people_router, prefix="/api")
app.include_router(events_router, prefix="/api")
app.include_router(admin_router, prefix="/api")


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {"message": "Welcome to STEM League Data API"}


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}
