"""Pydantic schemas for API request/response validation."""

from stem_league_data.schemas.base import BaseSchema, TimestampSchema
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
from stem_league_data.schemas.categories import (
    GroupCreate, GroupUpdate, GroupResponse,
    ProgramCreate, ProgramUpdate, ProgramResponse,
    CategoryCreate, CategoryUpdate, CategoryResponse,
    TopicCreate, TopicUpdate, TopicResponse,
    TrackCreate, TrackUpdate, TrackResponse,
    SubCategoryCreate, SubCategoryUpdate, SubCategoryResponse,
    TagCreate, TagUpdate, TagResponse,
)
from stem_league_data.schemas.events import (
    ServiceCreate, ServiceUpdate, ServiceResponse,
    ActivityCreate, ActivityUpdate, ActivityResponse,
    OccurrenceCreate, OccurrenceUpdate, OccurrenceResponse,
    RegistrationCreate, RegistrationUpdate, RegistrationResponse,
    RSVPCreate, RSVPUpdate, RSVPResponse,
    RRuleSchema,
)
from stem_league_data.schemas.jobs import (
    JobPostingCreate, JobPostingUpdate, JobPostingResponse,
    InstructorAssignmentCreate, InstructorAssignmentUpdate, InstructorAssignmentResponse,
    InstructorEvaluationCreate, InstructorEvaluationUpdate, InstructorEvaluationResponse,
)
from stem_league_data.schemas.ext_services import (
    MeetupCreate, MeetupUpdate, MeetupResponse,
    Pike13ServiceCreate, Pike13ServiceUpdate, Pike13ServiceResponse,
    P13LocationCreate, P13LocationUpdate, P13LocationResponse,
)

__all__ = [
    # Base
    "BaseSchema",
    "TimestampSchema",
    # Place
    "MetroCreate", "MetroUpdate", "MetroResponse",
    "OrgCreate", "OrgUpdate", "OrgResponse",
    "VenueCreate", "VenueUpdate", "VenueResponse",
    "FlyerCreate", "FlyerUpdate", "FlyerResponse",
    # People
    "PersonCreate", "PersonUpdate", "PersonResponse",
    "StaffCreate", "StaffUpdate", "StaffResponse",
    "VisitorCreate", "VisitorUpdate", "VisitorResponse",
    # Content
    "ContentCreate", "ContentUpdate", "ContentResponse",
    "AnnouncementCreate", "AnnouncementUpdate", "AnnouncementResponse",
    # Categories
    "GroupCreate", "GroupUpdate", "GroupResponse",
    "ProgramCreate", "ProgramUpdate", "ProgramResponse",
    "CategoryCreate", "CategoryUpdate", "CategoryResponse",
    "TopicCreate", "TopicUpdate", "TopicResponse",
    "TrackCreate", "TrackUpdate", "TrackResponse",
    "SubCategoryCreate", "SubCategoryUpdate", "SubCategoryResponse",
    "TagCreate", "TagUpdate", "TagResponse",
    # Events
    "ServiceCreate", "ServiceUpdate", "ServiceResponse",
    "ActivityCreate", "ActivityUpdate", "ActivityResponse",
    "OccurrenceCreate", "OccurrenceUpdate", "OccurrenceResponse",
    "RegistrationCreate", "RegistrationUpdate", "RegistrationResponse",
    "RSVPCreate", "RSVPUpdate", "RSVPResponse",
    "RRuleSchema",
    # Jobs
    "JobPostingCreate", "JobPostingUpdate", "JobPostingResponse",
    "InstructorAssignmentCreate", "InstructorAssignmentUpdate", "InstructorAssignmentResponse",
    "InstructorEvaluationCreate", "InstructorEvaluationUpdate", "InstructorEvaluationResponse",
    # External Services
    "MeetupCreate", "MeetupUpdate", "MeetupResponse",
    "Pike13ServiceCreate", "Pike13ServiceUpdate", "Pike13ServiceResponse",
    "P13LocationCreate", "P13LocationUpdate", "P13LocationResponse",
]
