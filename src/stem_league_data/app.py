"""FastAPI application for STEM League Data."""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from stem_league_data.database import create_tables
from stem_league_data.routers import (
    places_router,
    people_router,
    content_router,
    categories_router,
    events_router,
    jobs_router,
    ext_services_router,
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

# Include all routers
app.include_router(places_router, prefix="/api")
app.include_router(people_router, prefix="/api")
app.include_router(content_router, prefix="/api")
app.include_router(categories_router, prefix="/api")
app.include_router(events_router, prefix="/api")
app.include_router(jobs_router, prefix="/api")
app.include_router(ext_services_router, prefix="/api")
app.include_router(admin_router, prefix="/api")


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {"message": "Welcome to STEM League Data API"}


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}
