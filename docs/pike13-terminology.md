# Pike13 Scheduling Terminology

This document defines the core objects in Pike13's scheduling system and how they relate to each other.

---

## Service

A **Service** is the top-level definition of something your business offers. It describes *what* you're selling—the name, description, duration, price, and configuration options (capacity limits, enrollment rules, cancellation policies, etc.).

A Service has a **type** that determines its scheduling behavior:

| Service Type | Description |
|--------------|-------------|
| **Appointment** | One-on-one or small-group sessions booked into a staff member's availability |
| **GroupClass** | Recurring group sessions with flexible attendance (drop-ins, makeups allowed) |
| **Course** | A fixed series of sessions; clients enroll in the entire run and pay upfront |

The Service is the template. It does not itself appear on a calendar—Events and EventOccurrences do.

---

## Event

An **Event** is a scheduled instance of a Service. It defines *when* and *where* a Service will be delivered.

For a **GroupClass** or **Course**, the Event contains the recurrence rules (which days, what time, start/end dates) and generates individual EventOccurrences. An Event can have multiple recurrence patterns (e.g., Mondays and Wednesdays at different times).

For an **Appointment**, there is no persistent Event object in the same sense—appointments are created on-demand when a client books into a staff member's available time slot.

**Key attributes:**
- Links to a Service
- Contains scheduling rules (icals/recurrence patterns)
- Has a list of enrolled attendees (for Courses)
- Generates EventOccurrences

---

## EventOccurrence

An **EventOccurrence** is a single scheduled meeting on a specific date and time. It's the atomic unit that appears on a calendar.

Every GroupClass session, every Course meeting, and every booked Appointment is represented as an EventOccurrence.

**Key attributes:**
- `start_at` / `end_at` — the specific date and time
- `location_id` — where it takes place
- `staff_members` — who is teaching/leading
- `state` — active, canceled, reserved, deleted
- `full` — whether capacity has been reached
- `capacity_remaining` — spots left

**Relationship:** An Event (for GroupClass/Course) generates many EventOccurrences. For Appointments, the EventOccurrence is created when a client books.

---

## Visit

A **Visit** records a person's registration for a specific EventOccurrence. It's the join between a Person and an EventOccurrence.

When someone enrolls in a class or books an appointment, a Visit is created. The Visit tracks:
- Registration status: `registered`, `completed`, `cancelled`, `noshow`
- Payment status: whether it's been paid and how (which pass/plan covered it)
- Timestamps: when they registered, attended, cancelled, etc.

**Relationship:** Each EventOccurrence can have many Visits (one per attendee). Each Visit belongs to one Person and one EventOccurrence.

---

## Appointment

An **Appointment** is a Service type designed for one-on-one or small-group sessions scheduled into a staff member's availability windows.

Unlike GroupClass or Course, Appointments don't have a fixed recurring schedule. Instead, clients browse available time slots (based on staff availability) and book into them. When booked, an EventOccurrence is created for that specific time.

**Typical use:** Personal training, private lessons, consultations.

---

## GroupClass

A **GroupClass** is a Service type for recurring group sessions with flexible attendance.

Clients can drop in, make up missed sessions, or enroll on an ongoing basis. The schedule repeats (e.g., every Tuesday at 4pm), and clients are not required to commit to the entire series.

**Typical use:** Yoga classes, group fitness, open gym sessions.

---

## Course

A **Course** is a Service type for a bounded series of sessions that clients must enroll in as a unit.

Clients pay for the entire course upfront and are expected to attend all sessions. They cannot drop in for individual meetings or make up missed sessions (unless you allow it as a policy exception).

**Typical use:** 8-week beginner series, summer camps, certification programs.

---

## Object Relationships

```
Service (defines what you offer)
    │
    ├── type: Appointment
    │       └── Available Slots (from staff availability)
    │               └── EventOccurrence (created when booked)
    │                       └── Visit (the booking record)
    │
    ├── type: GroupClass
    │       └── Event (recurrence rules)
    │               └── EventOccurrence (each scheduled session)
    │                       └── Visit (per attendee)
    │
    └── type: Course
            └── Event (fixed series of dates)
                    └── EventOccurrence (each session in the course)
                            └── Visit (per enrolled student)
```

---

## Summary Table

| Object | What it represents | Created when... |
|--------|-------------------|-----------------|
| **Service** | The definition of an offering (name, price, type, rules) | Business sets up their offerings |
| **Event** | A scheduled delivery of a Service with recurrence rules | Staff creates a class or course schedule |
| **EventOccurrence** | A single meeting on a specific date/time | Generated from Event recurrence, or when Appointment is booked |
| **Visit** | A person's registration for a specific EventOccurrence | Client enrolls or books |
| **Appointment** | Service type: bookable into staff availability | (It's a Service type, not a separate object) |
| **GroupClass** | Service type: recurring with flexible attendance | (It's a Service type, not a separate object) |
| **Course** | Service type: fixed series, enroll in full | (It's a Service type, not a separate object) |
