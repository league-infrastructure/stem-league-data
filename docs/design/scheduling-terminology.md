# Scheduling System Terminology

This document defines the core objects in our scheduling system.

---

## Service

A **Service** defines the content of what you're offering—the topic, description, skill level, prerequisites, and enrollment information.

A Service is reusable. The same Service can be delivered as a Class, Course, or Event without duplicating the content definition.

**Examples:**
- "Introduction to Python"
- "Robotics Fundamentals"
- "Game Development with Unity"

**Key attributes:**
- Name
- Description
- Skill level / prerequisites
- Target audience
- Learning objectives

---

## Activity

An **Activity** is a scheduled delivery of a Service. It defines *how* and *when* a Service will be taught.

Activity is an abstract superclass with four concrete types:

| Type | Sessions | Description |
|------|----------|-------------|
| **Class** | Unlimited | Ongoing series with no end date; flexible attendance |
| **Course** | Limited | Fixed number of sessions; students enroll for the full run |
| **Event** | One | Single standalone session |
| **Appointment** | One | One-on-one session booked into instructor availability |

**Common attributes (all Activity types):**
- Links to a Service (the content)
- Location
- Instructor(s)
- Capacity
- Pricing

---

## Class

A **Class** is an Activity with unlimited sessions. It runs on a recurring schedule with no predetermined end date.

Students can drop in, miss sessions, or enroll on an ongoing basis. Attendance is flexible.

**Typical use:** Weekly robotics club, ongoing Python practice sessions, open lab time.

**Additional attributes:**
- Schedule (day of week, time)
- Rolling enrollment allowed

---

## Course

A **Course** is an Activity with a limited number of sessions. It has a defined start date, end date, and session count.

Students enroll in the full run and are expected to attend all sessions. Enrollment typically happens before the Course begins.

**Typical use:** 8-week beginner series, summer camps, structured curriculum progressions.

**Additional attributes:**
- Start date / end date
- Number of sessions
- Schedule (day of week, time)

---

## Event

An **Event** is an Activity with a single session. It's a standalone offering—each Event is independent.

The same Service can be delivered as multiple Events at different times. Students register for individual Events.

**Typical use:** Workshops, one-off demonstrations, guest speaker sessions, tournament days.

**Additional attributes:**
- Date and time
- (No recurrence—each Event is scheduled individually)

---

## Appointment

An **Appointment** is an Activity for one-on-one or small-group sessions booked into an instructor's availability.

Unlike Class, Course, or Event, Appointments don't have a fixed schedule. Instead, clients browse available time slots (based on instructor availability) and book into them. An Occurrence is created when booked.

**Typical use:** Private tutoring, one-on-one mentoring, individual project help.

**Additional attributes:**
- Duration
- Instructor availability windows
- (Schedule determined by booking, not predefined)

---

## Occurrence

An **Occurrence** is a single scheduled meeting on a specific date and time. It's the atomic unit that appears on a calendar.

- A **Class** generates many Occurrences (one per session, ongoing)
- A **Course** generates a fixed number of Occurrences (one per session in the series)
- An **Event** has exactly one Occurrence
- An **Appointment** has exactly one Occurrence (created when booked)

**Key attributes:**
- `start_at` / `end_at` — the specific date and time
- `location` — where it takes place
- `instructor` — who is teaching
- `state` — active, canceled, etc.
- `capacity_remaining` — spots left

---

## Visit

A **Visit** records a person's attendance at a specific Occurrence. It's the join between a Person and an Occurrence.

**Key attributes:**
- Registration status: registered, completed, cancelled, noshow
- Payment status
- Timestamps

---

## Object Relationships

```
Service (content: "Introduction to Python")
    │
    ├── Class ("Tuesday 4pm ongoing")
    │       └── Occurrence (each Tuesday)
    │               └── Visit (per attendee)
    │
    ├── Course ("Summer 2025, 8 weeks")
    │       └── Occurrence (8 total)
    │               └── Visit (per enrolled student)
    │
    ├── Event ("Robot Riot Demo Day")
    │       └── Occurrence (just one)
    │               └── Visit (per attendee)
    │
    └── Appointment ("Private Tutoring")
            └── Occurrence (created when client books)
                    └── Visit
```

---

## Comparison to Pike13

| Concept | Pike13 | Our Model |
|---------|--------|-----------|
| Content definition | Service (bundled with type) | **Service** (content only) |
| Scheduled delivery | Event + `service_type` | **Activity** (superclass) |
| Ongoing sessions | `service_type: GroupClass` | **Class** |
| Fixed series | `service_type: Course` | **Course** |
| Single session | (no direct equivalent) | **Event** |
| One-on-one booking | `service_type: Appointment` | **Appointment** |
| Single meeting | EventOccurrence | **Occurrence** |
| Attendance record | Visit | **Visit** |

---

## Summary Table

| Object | What it represents | Sessions |
|--------|-------------------|----------|
| **Service** | The content/curriculum (what you teach) | — |
| **Activity** | Abstract: a scheduled delivery of a Service | — |
| **Class** | Concrete Activity: ongoing, flexible attendance | Unlimited |
| **Course** | Concrete Activity: bounded series, enroll in full | Limited |
| **Event** | Concrete Activity: standalone single session | One |
| **Appointment** | Concrete Activity: one-on-one, booked into availability | One |
| **Occurrence** | A single meeting on a specific date/time | — |
| **Visit** | A person's registration for an Occurrence | — |
