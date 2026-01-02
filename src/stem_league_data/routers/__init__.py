"""API routers for STEM League Data."""

from stem_league_data.routers.crud import create_crud_router
from stem_league_data.routers.places import router as places_router
from stem_league_data.routers.people import router as people_router
from stem_league_data.routers.content import router as content_router
from stem_league_data.routers.categories import router as categories_router
from stem_league_data.routers.events import router as events_router
from stem_league_data.routers.jobs import router as jobs_router
from stem_league_data.routers.ext_services import router as ext_services_router
from stem_league_data.routers.admin import router as admin_router

__all__ = [
    "create_crud_router",
    "places_router",
    "people_router",
    "content_router",
    "categories_router",
    "events_router",
    "jobs_router",
    "ext_services_router",
    "admin_router",
]
