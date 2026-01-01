# API Use Cases

## Overview

This document describes the use cases at the API level—what operations the
web application performs against the REST API. These use cases focus on
**Managed Resources** that require orchestration across multiple entities.
CRUD resources are excluded as they follow standard create/read/update/delete
patterns.

See [rest_interface.md](rest_interface.md) for the resource classification
and [toplevel_use_cases.md](toplevel_use_cases.md) for end-user use cases.

---

## 1. PLACES

### UC-API-1.1: Create Organization

**Trigger:** Admin creates a new partner organization or hosting entity

**Preconditions:**
- Metro must exist

**Request:**
- Org details (name, type, website, contact_email, can_deliver_events,
  can_host_events)
- metro_id (required)

**Processing:**
1. Validate Metro exists
2. Create Org record

**Response:** Created Org with ID

---

### UC-API-1.2: Create Venue

**Trigger:** Admin adds a new event location

**Preconditions:**
- Metro must exist
- Org should exist if venue belongs to an organization

**Request:**
- Venue details (name, address, parking_instructions,
  building_entry_instructions, capacity, has_computers)
- metro_id (required)
- org_id (optional)

**Processing:**
1. Validate Metro exists
2. Validate Org exists (if provided)
3. Create Venue record

**Response:** Created Venue with ID

---

## 2. PEOPLE

### UC-API-2.1: Create Staff Member

**Trigger:** Admin registers a new instructor, volunteer, or staff member

**Variants:**

**A. Create Staff with new Person (atomic):**
- Person details (first_name, last_name, email, phone, etc.)
- Staff details (role, bio, photo, is_adult, background_check_status,
  volunteer_tier, specializations)

**B. Add Staff role to existing Person:**
- person_id (existing)
- Staff details only

**Processing:**
1. If creating new Person:
   - Validate email uniqueness (if provided)
   - Create Person record
2. Validate Person doesn't already have Staff record
3. Create Staff record linked to Person

**Response:** Created Staff with embedded Person details

---

### UC-API-2.2: Create Visitor (Student/Participant)

**Trigger:** Registration process creates visitor records for students

**Request:**
- Visitor details (grade, school)
- person_id (optional - link to existing Person)
- guardian_id (optional - link to guardian Person)

**Processing:**
1. If person_id provided, validate Person exists
2. If guardian_id provided, validate guardian Person exists
3. Create Visitor record

**Response:** Created Visitor with ID

**Note:** Visitors are often created as part of the Registration flow
(see UC-API-4.1), not standalone.

---

### UC-API-2.3: Record Instructor Evaluation

**Trigger:** Lead instructor or coordinator evaluates staff member after event

**Preconditions:**
- InstructorAssignment must exist (staff was assigned to activity)
- Evaluator must be Staff

**Request:**
- instructor_assignment_id (required)
- evaluator_id (Staff ID, required)
- Ratings (technical_skills, teaching_ability, reliability,
  student_engagement) - 1-5 scale
- notes (text feedback)
- potential_hire (boolean)

**Processing:**
1. Validate InstructorAssignment exists
2. Validate evaluator Staff exists
3. Create InstructorEvaluation record

**Response:** Created InstructorEvaluation with ID

---

## 3. ACTIVITIES

This is the most complex area, requiring coordination between Service, Activity,
and Occurrence.

### UC-API-3.1: Create Activity with New Service

**Trigger:** Coordinator creates a brand new class/event type that doesn't
exist yet

**Request:**
```json
{
  "service": {
    "slug": "python-game-dev-101",
    "content": {
      "title": "Python Game Development",
      "blurb": "Learn to build games with Python"
    },
    "grade": "6-8",
    "level": "beginner",
    "topics": ["python", "game-dev"],
    "tracks": ["coding"],
    "categories": ["programming"]
  },
  "activity": {
    "type": "class",
    "status": "draft",
    "venue_id": 123,
    "org_id": 456,
    "content": {
      "title": "Spring Python Games",
      "description": "Wednesday/Friday session details..."
    },
    "enrollment_id": 789,
    "cta": {
      "label": "Register Now",
      "link": "https://..."
    },
    "start_dt": "2026-01-15T16:00:00",
    "end_dt": "2026-03-15T17:30:00",
    "schedule": {
      "frequency": "WEEKLY",
      "days": [2, 4]
    },
    "capacity": 20,
    "registration_type": "open",
    "programs": ["after-school"],
    "tags": ["spring-2026"]
  }
}
```

Note: This example shows inline `service`, inline `content` and `cta` objects
(which will be created), while using `venue_id`, `org_id`, and `enrollment_id`
to reference existing records.

**Processing:**
1. Validate Venue exists
2. Validate Org exists (if provided)
3. Resolve or create Content records (service content, activity content,
   enrollment, cta)
4. Resolve category references (topics, tracks, categories, programs, tags)
5. Create Service record with content and category links
6. Create Activity record linked to Service
7. Generate Occurrences from schedule (see UC-API-3.4)

**Response:** Created Activity with Service and Occurrences

---

### UC-API-3.2: Create Activity from Existing Service

**Trigger:** Coordinator schedules another instance of an existing class type

**Request:**
```json
{
  "service_id": 789,
  "activity": {
    "type": "class",
    "venue_id": 123,
    "start_dt": "2026-04-01T16:00:00",
    "end_dt": "2026-06-01T17:30:00",
    "schedule": {
      "frequency": "WEEKLY",
      "days": [1, 3]
    },
    "capacity": 15
  }
}
```

**Processing:**
1. Validate Service exists
2. Validate Venue exists
3. Create Activity record linked to existing Service
4. Generate Occurrences from schedule

**Response:** Created Activity with Occurrences (Service unchanged)

---

### UC-API-3.3: Create Activity with Manual Occurrences

**Trigger:** Coordinator creates an activity with irregular schedule
(e.g., monthly meetups)

**Request:**
```json
{
  "service_id": 789,
  "activity": {
    "type": "event",
    "venue_id": 123,
    "schedule": null,
    "capacity": 30
  },
  "occurrences": [
    { "start_time": "2026-01-18T14:00:00", "end_time": "2026-01-18T16:00:00" },
    { "start_time": "2026-02-15T14:00:00", "end_time": "2026-02-15T16:00:00" },
    { "start_time": "2026-03-22T14:00:00", "end_time": "2026-03-22T16:00:00" }
  ]
}
```

**Processing:**
1. Create Activity without schedule fields
2. Create each Occurrence record manually

**Response:** Created Activity with specified Occurrences

**Use Case:** Meetups, special events, irregular workshops

---

### UC-API-3.4: Generate Occurrences from Schedule

**Trigger:** Internal operation when Activity has a schedule

**Inputs:**
- start_dt: First occurrence start datetime (includes time of day)
- end_dt: Series end date (occurrences stop after this)
- schedule: RRule object defining the recurrence pattern

**Logic:**

**Case A: schedule is null (manual)**
- No automatic generation; occurrences must be added manually via the request
  or later through UC-API-3.5

**Case B: schedule.frequency == "ONCE"**
- Create single Occurrence from start_dt to end_dt

**Case C: schedule.frequency == "WEEKLY"**
1. Extract time-of-day and duration from start_dt/end_dt
2. For each weekday in schedule.days:
   - Generate all matching dates from start_dt to end_dt
   - Apply interval (every N weeks)
3. Create Occurrence for each generated date
4. Stop at schedule.count if specified

**Case D: schedule.frequency == "MONTHLY"**
1. Extract time-of-day and duration from start_dt/end_dt
2. For each month from start_dt to end_dt:
   - Find the Nth (setpos) occurrence of the weekday (days[0])
   - Apply interval (every N months)
3. Create Occurrence for each generated date
4. Stop at schedule.count if specified

**Example (WEEKLY):**
```
start_dt: 2026-01-15T16:00:00  (Wednesday)
end_dt: 2026-01-31T17:30:00
schedule: { frequency: "WEEKLY", days: [2, 4] }  (Wed=2, Fri=4)

Generated Occurrences:
- 2026-01-15 16:00-17:30 (Wed)
- 2026-01-17 16:00-17:30 (Fri)
- 2026-01-22 16:00-17:30 (Wed)
- 2026-01-24 16:00-17:30 (Fri)
- 2026-01-29 16:00-17:30 (Wed)
- 2026-01-31 16:00-17:30 (Fri)
```

**Example (MONTHLY):**
```
start_dt: 2026-01-01T14:00:00
end_dt: 2026-06-30T16:00:00
schedule: { frequency: "MONTHLY", days: [1], setpos: 4 }  (4th Tuesday)

Generated Occurrences:
- 2026-01-28 14:00-16:00 (4th Tue of Jan)
- 2026-02-25 14:00-16:00 (4th Tue of Feb)
- 2026-03-25 14:00-16:00 (4th Tue of Mar)
- 2026-04-22 14:00-16:00 (4th Tue of Apr)
- 2026-05-27 14:00-16:00 (4th Tue of May)
- 2026-06-23 14:00-16:00 (4th Tue of Jun)
```

---

### UC-API-3.5: Add Occurrence to Activity

**Trigger:** Coordinator adds a one-off date to an existing activity

**Request:**
- activity_id (required)
- start_time (required)
- end_time (required)
- notes (optional)

**Processing:**
1. Validate Activity exists
2. Create Occurrence record

**Response:** Created Occurrence with ID

**Use Case:** Adding makeup sessions, extra dates

---

### UC-API-3.6: Create One-Off Event

**Trigger:** Coordinator creates a single standalone event

**Approach A: Activity with single Occurrence**
```json
{
  "service_id": 789,
  "activity": {
    "type": "event",
    "venue_id": 123
  },
  "occurrences": [
    { "start_time": "2026-02-14T10:00:00", "end_time": "2026-02-14T12:00:00" }
  ]
}
```

**Approach B: Activity using start_dt as single occurrence**
```json
{
  "service_id": 789,
  "activity": {
    "type": "event",
    "venue_id": 123,
    "start_dt": "2026-02-14T10:00:00",
    "end_dt": "2026-02-14T12:00:00"
  }
}
```

**Processing:**
- When start_dt and end_dt are same day and no day_numbers/rrule,
  treat as single occurrence

---

### UC-API-3.7: Clone Activity to New Schedule

**Trigger:** Coordinator wants to repeat a past activity in a new time slot

**Request:**
- source_activity_id (activity to clone)
- New schedule fields (start_dt, end_dt, day_numbers, venue_id, etc.)

**Processing:**
1. Copy Activity fields (except schedule and IDs)
2. Link to same Service
3. Create new Activity record
4. Generate new Occurrences

**Response:** New Activity with new Occurrences

---

### UC-API-3.8: Update Activity Schedule

**Trigger:** Coordinator changes the schedule of an existing activity

**Variants:**

**A. Regenerate all occurrences:**
- Delete existing occurrences (if no attendance recorded)
- Update Activity schedule fields
- Regenerate occurrences

**B. Update future occurrences only:**
- Delete occurrences after cutoff date
- Update Activity schedule fields
- Regenerate occurrences from cutoff

**C. Reschedule specific occurrence:**
- Update single Occurrence record

**Business Rules:**
- Cannot delete Occurrence with attendance (rsvp_count > 0 or
  visitor_count > 0)
- Warn if RSVPs exist for occurrences being modified

---

## 4. REGISTRATIONS

### UC-API-4.1: Register for Activity

**Trigger:** Parent registers children for an event
(see UC-1.2 in toplevel_use_cases.md)

**Request:**
```json
{
  "activity_id": 123,
  "registrant": {
    "first_name": "Jane",
    "last_name": "Smith",
    "email": "jane@example.com",
    "phone": "555-1234"
  },
  "create_account": false,
  "visitors": [
    { "first_name": "Alex", "age": 12 },
    { "first_name": "Sam", "age": 10 }
  ],
  "utm_source": "facebook",
  "utm_campaign": "spring-2026"
}
```

**Processing:**
1. Find or create Person for registrant (match by email)
2. Create Registration record with marketing attribution
3. For each visitor:
   - Create Person record (first_name, derived birth year from age)
   - Create Visitor record linked to Person, with guardian
   - Create RSVP linking Registration, Activity, Visitor
4. Update Activity capacity tracking
5. Send confirmation email (async)

**Response:**
```json
{
  "registration_id": 456,
  "registrant_id": 789,
  "rsvps": [
    { "rsvp_id": 101, "visitor_id": 201, "visitor_name": "Alex" },
    { "rsvp_id": 102, "visitor_id": 202, "visitor_name": "Sam" }
  ],
  "status": "confirmed"
}
```

---

### UC-API-4.2: Register Returning User

**Trigger:** Logged-in user registers for another event

**Request:**
```json
{
  "activity_id": 123,
  "registrant_id": 789,
  "visitor_ids": [201, 202],
  "new_visitors": [
    { "first_name": "Taylor", "age": 8 }
  ]
}
```

**Processing:**
1. Validate registrant Person exists
2. Validate existing Visitors exist and belong to registrant
3. Create Registration record
4. Create RSVPs for existing visitors
5. Create new Visitors and RSVPs if provided
6. Update capacity tracking

---

### UC-API-4.3: Check In Attendees

**Trigger:** Staff checks in students at event

**Request:**
```json
{
  "occurrence_id": 555,
  "check_ins": [
    { "rsvp_id": 101, "attended": true },
    { "rsvp_id": 102, "attended": true }
  ],
  "walk_ins": 3
}
```

**Processing:**
1. For each RSVP: set attended=true, checked_in_at=now
2. Update Occurrence.visitor_count
3. Update Occurrence.walk_in_count

---

### UC-API-4.4: Cancel Registration

**Trigger:** Registrant cancels their registration

**Request:**
- registration_id

**Processing:**
1. Mark RSVPs as cancelled
2. Update capacity tracking
3. Process waitlist if applicable (promote next person)
4. Send cancellation confirmation

---

## 5. JOBS & ASSIGNMENTS

### UC-API-5.1: Post Job Opening

**Trigger:** Partner organization posts instructor position

**Preconditions:**
- Org must exist
- Metro must exist

**Request:**
- Job details (title, description, hourly_rate, hours_per_week, requirements)
- org_id (required)
- metro_id (required)

**Processing:**
1. Validate Org and Metro exist
2. Create JobPosting record

**Response:** Created JobPosting with ID

---

### UC-API-5.2: Assign Instructor to Activity

**Trigger:** Coordinator assigns staff member to teach

**Request:**
```json
{
  "activity_id": 123,
  "staff_id": 456,
  "role": "lead",
  "employment_type": "contractor",
  "hourly_rate": 35.00,
  "employer_id": 789
}
```

**Processing:**
1. Validate Activity exists
2. Validate Staff exists
3. Validate employer Org exists (if provided)
4. Create InstructorAssignment record
5. Notify instructor (async)

**Response:** Created InstructorAssignment with ID

---

### UC-API-5.3: Confirm Assignment

**Trigger:** Instructor confirms they can teach assigned activity

**Request:**
- instructor_assignment_id
- confirmed: true/false

**Processing:**
1. Update InstructorAssignment.confirmed

---

### UC-API-5.4: Record Hours Worked

**Trigger:** After activity, record actual hours for payment

**Request:**
- instructor_assignment_id
- hours_worked: decimal

**Processing:**
1. Update InstructorAssignment.hours_worked

---

## Design Notes

### Activity Scheduling with RRule

Activity scheduling is controlled by an embedded `schedule` object (RRule) that
supports four patterns. The schedule is validated before occurrence generation.

#### Scheduling Patterns

**1. Manual (no automatic occurrences)**
```json
{
  "activity": {
    "schedule": null
  },
  "occurrences": [
    { "start_time": "2026-01-18T14:00:00", "end_time": "2026-01-18T16:00:00" },
    { "start_time": "2026-02-15T14:00:00", "end_time": "2026-02-15T16:00:00" }
  ]
}
```
Use for: Meetups, irregular events, one-off workshops. Occurrences are
specified explicitly in the request or added later.

**2. Single Occurrence (ONCE)**
```json
{
  "activity": {
    "start_dt": "2026-02-14T10:00:00",
    "end_dt": "2026-02-14T12:00:00",
    "schedule": { "frequency": "ONCE" }
  }
}
```
Use for: One-time events. A single occurrence is generated from start_dt/end_dt.

**3. Weekly Recurring (WEEKLY)**
```json
{
  "activity": {
    "start_dt": "2026-01-15T16:00:00",
    "end_dt": "2026-03-15T17:30:00",
    "schedule": {
      "frequency": "WEEKLY",
      "days": [2, 4],
      "interval": 1
    }
  }
}
```
- `days`: Weekdays to recur on (Mon=0, Tue=1, Wed=2, Thu=3, Fri=4, Sat=5, Sun=6)
- `interval`: Every N weeks (default 1)
- `count`: Optional max number of occurrences

Use for: Regular weekly classes. Example above generates Wed/Fri occurrences
from Jan 15 to Mar 15.

**4. Monthly Nth Weekday (MONTHLY)**
```json
{
  "activity": {
    "start_dt": "2026-01-01T14:00:00",
    "end_dt": "2026-12-31T16:00:00",
    "schedule": {
      "frequency": "MONTHLY",
      "days": [5],
      "setpos": -1,
      "interval": 1
    }
  }
}
```
- `days`: Exactly one weekday
- `setpos`: Which occurrence (1-5 for 1st-5th, -1 for last)
- `interval`: Every N months (default 1)

Use for: Monthly events like "4th Tuesday" or "last Saturday" of each month.

#### Schedule Validation Rules

| Frequency | days | setpos | interval | count |
|-----------|------|--------|----------|-------|
| null (manual) | must be empty | must be empty | ignored | ignored |
| ONCE | must be empty | must be empty | ignored | ignored |
| WEEKLY | 1+ weekdays (0-6) | must be empty | >= 1 | optional |
| MONTHLY | exactly 1 weekday | 1-5 or -1 | >= 1 | optional |

#### Occurrence Generation

When an Activity is created with a schedule:

1. **start_dt** provides:
   - The first possible occurrence date
   - The time-of-day for all occurrences

2. **end_dt** provides:
   - The last possible occurrence date
   - The duration (end_dt time minus start_dt time)

3. **schedule** controls:
   - Which dates within the range get occurrences
   - For WEEKLY: all matching weekdays between start_dt and end_dt
   - For MONTHLY: all matching Nth weekdays between start_dt and end_dt
   - For ONCE: just start_dt itself
   - For manual (null): no automatic generation

### Content Resolution

When creating Service or Activity, content can be provided as:
- `content_id`: Reference to existing Content record
- `content: { ... }`: Inline object, creates new Content record
- Omitted: No content for that field

This allows reuse of content blocks while supporting quick inline creation.

### Object Reference Convention

Throughout the API, when an object links to another object, you can either:

1. **Reference an existing object** by specifying `<field>_id`:
   ```json
   { "venue_id": 123, "service_id": 456 }
   ```

2. **Create a new object inline** by specifying `<field>` with an object:
   ```json
   { "venue_id": 123, "service": { "slug": "new-service", ... } }
   ```

The API resolves these as follows:
- If `<field>_id` is provided, validate the referenced object exists
- If `<field>` object is provided, create the new object first
- If both are provided, `<field>_id` takes precedence (inline object ignored)
- If neither is provided and the field is required, return validation error

This pattern applies to: `service`/`service_id`, `content`/`content_id`,
`venue`/`venue_id`, `org`/`org_id`, `person`/`person_id`, etc.

### Idempotency Considerations

For Activity creation, consider supporting idempotency keys to prevent
duplicate activities from retry scenarios. The slug on Service provides
natural idempotency for services.

