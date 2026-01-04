"""CRUD routers using fastapi-crudrouter for automatic endpoint generation."""

from fastapi_crudrouter import SQLAlchemyCRUDRouter

from stem_league_data.database import get_db
from stem_league_data.models import (
    Metro, Org, Venue, Flyer,
    Person, Staff, Visitor,
    Content, Announcement,
    Service, Activity, Occurrence, Registration, RSVP,
    Group, Program, Track, Category, SubCategory, Topic, Tag,
    Meetup, Pike13Service, P13Location,
    JobPosting, InstructorAssignment, InstructorEvaluation,
)
from stem_league_data.schemas.place import (
    MetroCreate, MetroUpdate, MetroResponse,
    OrgCreate, OrgUpdate, OrgResponse,
    VenueCreate, VenueUpdate, VenueResponse,
    FlyerCreate, FlyerUpdate, FlyerResponse,
)
from stem_league_data.schemas.people import (
    PersonCreate, PersonUpdate, PersonResponse,
    StaffCreate, StaffUpdate, StaffResponse,
    VisitorCreate, VisitorUpdate, VisitorResponse,
)
from stem_league_data.schemas.content import (
    ContentCreate, ContentUpdate, ContentResponse,
    AnnouncementCreate, AnnouncementUpdate, AnnouncementResponse,
)
from stem_league_data.schemas.events import (
    ServiceCreate, ServiceUpdate, ServiceResponse,
    ActivityCreate, ActivityUpdate, ActivityResponse,
    OccurrenceCreate, OccurrenceUpdate, OccurrenceResponse,
    RegistrationCreate, RegistrationUpdate, RegistrationResponse,
    RSVPCreate, RSVPUpdate, RSVPResponse,
)
from stem_league_data.schemas.categories import (
    GroupCreate, GroupUpdate, GroupResponse,
    ProgramCreate, ProgramUpdate, ProgramResponse,
    TrackCreate, TrackUpdate, TrackResponse,
    CategoryCreate, CategoryUpdate, CategoryResponse,
    SubCategoryCreate, SubCategoryUpdate, SubCategoryResponse,
    TopicCreate, TopicUpdate, TopicResponse,
    TagCreate, TagUpdate, TagResponse,
)
from stem_league_data.schemas.ext_services import (
    MeetupCreate, MeetupUpdate, MeetupResponse,
    Pike13ServiceCreate, Pike13ServiceUpdate, Pike13ServiceResponse,
    P13LocationCreate, P13LocationUpdate, P13LocationResponse,
)
from stem_league_data.schemas.jobs import (
    JobPostingCreate, JobPostingUpdate, JobPostingResponse,
    InstructorAssignmentCreate, InstructorAssignmentUpdate, InstructorAssignmentResponse,
    InstructorEvaluationCreate, InstructorEvaluationUpdate, InstructorEvaluationResponse,
)


# ============================================================================
# Place Resources
# ============================================================================

metro_router = SQLAlchemyCRUDRouter(
    schema=MetroResponse,
    create_schema=MetroCreate,
    update_schema=MetroUpdate,
    db_model=Metro,
    db=get_db,
    prefix="/metros",
    tags=["metros"],
)

org_router = SQLAlchemyCRUDRouter(
    schema=OrgResponse,
    create_schema=OrgCreate,
    update_schema=OrgUpdate,
    db_model=Org,
    db=get_db,
    prefix="/orgs",
    tags=["orgs"],
)

venue_router = SQLAlchemyCRUDRouter(
    schema=VenueResponse,
    create_schema=VenueCreate,
    update_schema=VenueUpdate,
    db_model=Venue,
    db=get_db,
    prefix="/venues",
    tags=["venues"],
)

flyer_router = SQLAlchemyCRUDRouter(
    schema=FlyerResponse,
    create_schema=FlyerCreate,
    update_schema=FlyerUpdate,
    db_model=Flyer,
    db=get_db,
    prefix="/flyers",
    tags=["flyers"],
)


# ============================================================================
# People Resources
# ============================================================================

person_router = SQLAlchemyCRUDRouter(
    schema=PersonResponse,
    create_schema=PersonCreate,
    update_schema=PersonUpdate,
    db_model=Person,
    db=get_db,
    prefix="/persons",
    tags=["persons"],
)

staff_router = SQLAlchemyCRUDRouter(
    schema=StaffResponse,
    create_schema=StaffCreate,
    update_schema=StaffUpdate,
    db_model=Staff,
    db=get_db,
    prefix="/staff",
    tags=["staff"],
)

visitor_router = SQLAlchemyCRUDRouter(
    schema=VisitorResponse,
    create_schema=VisitorCreate,
    update_schema=VisitorUpdate,
    db_model=Visitor,
    db=get_db,
    prefix="/visitors",
    tags=["visitors"],
)


# ============================================================================
# Content Resources
# ============================================================================

content_router = SQLAlchemyCRUDRouter(
    schema=ContentResponse,
    create_schema=ContentCreate,
    update_schema=ContentUpdate,
    db_model=Content,
    db=get_db,
    prefix="/contents",
    tags=["contents"],
)

announcement_router = SQLAlchemyCRUDRouter(
    schema=AnnouncementResponse,
    create_schema=AnnouncementCreate,
    update_schema=AnnouncementUpdate,
    db_model=Announcement,
    db=get_db,
    prefix="/announcements",
    tags=["announcements"],
)


# ============================================================================
# Events Resources
# ============================================================================

service_router = SQLAlchemyCRUDRouter(
    schema=ServiceResponse,
    create_schema=ServiceCreate,
    update_schema=ServiceUpdate,
    db_model=Service,
    db=get_db,
    prefix="/services",
    tags=["services"],
)

activity_router = SQLAlchemyCRUDRouter(
    schema=ActivityResponse,
    create_schema=ActivityCreate,
    update_schema=ActivityUpdate,
    db_model=Activity,
    db=get_db,
    prefix="/activities",
    tags=["activities"],
)

occurrence_router = SQLAlchemyCRUDRouter(
    schema=OccurrenceResponse,
    create_schema=OccurrenceCreate,
    update_schema=OccurrenceUpdate,
    db_model=Occurrence,
    db=get_db,
    prefix="/occurrences",
    tags=["occurrences"],
)

registration_router = SQLAlchemyCRUDRouter(
    schema=RegistrationResponse,
    create_schema=RegistrationCreate,
    update_schema=RegistrationUpdate,
    db_model=Registration,
    db=get_db,
    prefix="/registrations",
    tags=["registrations"],
)

rsvp_router = SQLAlchemyCRUDRouter(
    schema=RSVPResponse,
    create_schema=RSVPCreate,
    update_schema=RSVPUpdate,
    db_model=RSVP,
    db=get_db,
    prefix="/rsvps",
    tags=["rsvps"],
)

# ============================================================================
# Categories Resources
# ============================================================================

group_router = SQLAlchemyCRUDRouter(
    schema=GroupResponse,
    create_schema=GroupCreate,
    update_schema=GroupUpdate,
    db_model=Group,
    db=get_db,
    prefix="/groups",
    tags=["groups"],
)

program_router = SQLAlchemyCRUDRouter(
    schema=ProgramResponse,
    create_schema=ProgramCreate,
    update_schema=ProgramUpdate,
    db_model=Program,
    db=get_db,
    prefix="/programs",
    tags=["programs"],
)

track_router = SQLAlchemyCRUDRouter(
    schema=TrackResponse,
    create_schema=TrackCreate,
    update_schema=TrackUpdate,
    db_model=Track,
    db=get_db,
    prefix="/tracks",
    tags=["tracks"],
)

category_router = SQLAlchemyCRUDRouter(
    schema=CategoryResponse,
    create_schema=CategoryCreate,
    update_schema=CategoryUpdate,
    db_model=Category,
    db=get_db,
    prefix="/categories",
    tags=["categories"],
)

subcategory_router = SQLAlchemyCRUDRouter(
    schema=SubCategoryResponse,
    create_schema=SubCategoryCreate,
    update_schema=SubCategoryUpdate,
    db_model=SubCategory,
    db=get_db,
    prefix="/subcategories",
    tags=["subcategories"],
)

topic_router = SQLAlchemyCRUDRouter(
    schema=TopicResponse,
    create_schema=TopicCreate,
    update_schema=TopicUpdate,
    db_model=Topic,
    db=get_db,
    prefix="/topics",
    tags=["topics"],
)

tag_router = SQLAlchemyCRUDRouter(
    schema=TagResponse,
    create_schema=TagCreate,
    update_schema=TagUpdate,
    db_model=Tag,
    db=get_db,
    prefix="/tags",
    tags=["tags"],
)


# ============================================================================
# External Services Resources
# ============================================================================

meetup_router = SQLAlchemyCRUDRouter(
    schema=MeetupResponse,
    create_schema=MeetupCreate,
    update_schema=MeetupUpdate,
    db_model=Meetup,
    db=get_db,
    prefix="/meetups",
    tags=["meetups"],
)

pike13_service_router = SQLAlchemyCRUDRouter(
    schema=Pike13ServiceResponse,
    create_schema=Pike13ServiceCreate,
    update_schema=Pike13ServiceUpdate,
    db_model=Pike13Service,
    db=get_db,
    prefix="/pike13-services",
    tags=["pike13-services"],
)

p13_location_router = SQLAlchemyCRUDRouter(
    schema=P13LocationResponse,
    create_schema=P13LocationCreate,
    update_schema=P13LocationUpdate,
    db_model=P13Location,
    db=get_db,
    prefix="/p13-locations",
    tags=["p13-locations"],
)

# ============================================================================
# Jobs Resources
# ============================================================================

job_posting_router = SQLAlchemyCRUDRouter(
    schema=JobPostingResponse,
    create_schema=JobPostingCreate,
    update_schema=JobPostingUpdate,
    db_model=JobPosting,
    db=get_db,
    prefix="/job-postings",
    tags=["job-postings"],
)

instructor_assignment_router = SQLAlchemyCRUDRouter(
    schema=InstructorAssignmentResponse,
    create_schema=InstructorAssignmentCreate,
    update_schema=InstructorAssignmentUpdate,
    db_model=InstructorAssignment,
    db=get_db,
    prefix="/instructor-assignments",
    tags=["instructor-assignments"],
)

instructor_evaluation_router = SQLAlchemyCRUDRouter(
    schema=InstructorEvaluationResponse,
    create_schema=InstructorEvaluationCreate,
    update_schema=InstructorEvaluationUpdate,
    db_model=InstructorEvaluation,
    db=get_db,
    prefix="/instructor-evaluations",
    tags=["instructor-evaluations"],
)
