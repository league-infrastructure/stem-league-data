# REST Interface Design

## Overview

The REST API follows a hybrid approach combining standard CRUD operations with application-level operations:

- **CRUD Resources**: Simple entities that can be created, read, updated, and deleted independently
- **Managed Resources**: Complex entities that require orchestration across multiple related objects and are manipulated through application logic

This design ensures data integrity while providing flexibility for both simple data management and complex business operations.

---

## CRUD Resources

These entities have no required outgoing dependencies and can be safely created, updated, and deleted without affecting other objects. Deletion may be restricted if other objects reference them (enforced via database constraints).

| Resource | Description | Delete Behavior |
|----------|-------------|-----------------|
| `Pike13Service` | Pike13 service/class integration records | Safe to delete |
| `P13Location` | Pike13 location records | Safe to delete |
| `Meetup` | Historical Meetup.com event records | Safe to delete |
| `Tag` | Simple tags for categorizing events | Cascade removes from activities |
| `Group` | Base categorization (Program, Track, Category, SubCategory, Topic) | Cascade removes associations; optional Org link set to null |
| `Content` | Base content blocks (title, blurb, description, etc.) | References from Service, Activity, Announcement set to null |
| `Page` | Page-type content (inherits from Content) | Same as Content |
| `Metro` | Metropolitan areas where League operates | Restricted if Venues, Orgs, Persons, or JobPostings reference it |
| `Person` | Individual people in the network | Restricted if Staff, Registrations exist; Visitor references set to null |
| `Flyer` | Marketing flyers for events | Cascade removes activity associations |
| `MarketingStats` | Marketing statistics for events | Safe to delete |
| `Announcement` | Optional `Content` | Time-bounded announcements |
---

## Managed Resources (Require Orchestration)

These entities have dependencies on other objects and typically require application logic to create, update, or delete properly. They may involve creating or updating multiple related records atomically.

### Places

| Resource | Dependencies | Notes |
|----------|--------------|-------|
| `Org` | Requires `Metro` | Organizations that host/deliver events |
| `Venue` | Requires `Metro`; optional `Org` | Physical locations for events |

### People

The API will likely represent `Staff` and `Visitor` as specialized views or subtypes of `Person`. Creating a Staff record can create the underlying Person atomically, or Staff can be added to an existing Person.

| Resource | Dependencies | Notes |
|----------|--------------|-------|
| `Staff` | Requires `Person` | Staff/instructor record extends a Person |
| `Visitor` | Optional `Person`, optional guardian `Person` | Student/participant in events |
| `InstructorEvaluation` | Requires `InstructorAssignment`, `Staff` (evaluator) | Performance evaluations |

### Activities

| Resource | Dependencies | Notes |
|----------|--------------|-------|
| `Service` | Optional `Content`, optional parent `Service`, many-to-many with Topics/Tracks/Categories | Describes educational content |
| `Activity` | Requires `Venue`, `Service`; optional `Org`, multiple `Content` refs, many-to-many with Programs/Tracks/Categories/Topics/Tags | Scheduled delivery of a Service |
| `Occurrence` | Requires `Activity` | Specific time slot of an Activity |

**Typical Activity Creation Flow:**
1. Ensure `Metro` exists
2. Ensure `Venue` exists (create if needed)
3. Ensure or create `Content` records for service description, activity details, enrollment info, CTA
4. Ensure or create category records (Program, Track, Category, Topic)
5. Create or update `Service` with content and category links
6. Create `Activity` linking Service, Venue, Content, and categories
7. Create `Occurrence` records for specific time slots

### Registrations

| Resource | Dependencies | Notes |
|----------|--------------|-------|
| `Registration` | Requires `Activity`, `Person` | A person's registration for an activity |
| `RSVP` | Requires `Registration`, `Activity`, `Visitor`; optional guardian `Person` | Individual attendee on a registration |

### Jobs

| Resource | Dependencies | Notes |
|----------|--------------|-------|
| `JobPosting` | Requires `Org`, `Metro` | Job listings |
| `InstructorAssignment` | Requires `Activity`, `Staff`; optional employer `Org` | Staff assigned to teach an activity |

---

## Next Steps

- Define specific API endpoints for CRUD resources
- Design operation endpoints for complex Activity workflows
- Document validation rules and error responses
- Define bulk operation patterns for data imports
