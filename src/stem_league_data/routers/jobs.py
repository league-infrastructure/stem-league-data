"""Router for Job resources: JobPosting, InstructorAssignment, InstructorEvaluation."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from stem_league_data.database import get_db
from stem_league_data.models import (
    JobPosting, InstructorAssignment, InstructorEvaluation,
    Org, Venue, Person, Staff, Activity,
)
from stem_league_data.schemas.jobs import (
    JobPostingCreate, JobPostingUpdate, JobPostingResponse,
    InstructorAssignmentCreate, InstructorAssignmentUpdate, InstructorAssignmentResponse,
    InstructorEvaluationCreate, InstructorEvaluationUpdate, InstructorEvaluationResponse,
)

router = APIRouter()


# ============================================================================
# JobPosting Endpoints
# ============================================================================

@router.get("/job-postings", response_model=list[JobPostingResponse], tags=["job-postings"])
def list_job_postings(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    org_id: int | None = None,
    venue_id: int | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
) -> list[Any]:
    """List all job postings with pagination and optional filters."""
    query = db.query(JobPosting)
    if org_id is not None:
        query = query.filter(JobPosting.org_id == org_id)
    if venue_id is not None:
        query = query.filter(JobPosting.venue_id == venue_id)
    if status is not None:
        query = query.filter(JobPosting.status == status)
    return query.offset(skip).limit(limit).all()


@router.get("/job-postings/count", tags=["job-postings"])
def count_job_postings(db: Session = Depends(get_db)) -> dict[str, int]:
    """Get total count of job postings."""
    count = db.query(func.count(JobPosting.id)).scalar()
    return {"count": count}


@router.get("/job-postings/{job_posting_id}", response_model=JobPostingResponse, tags=["job-postings"])
def get_job_posting(job_posting_id: int, db: Session = Depends(get_db)) -> Any:
    """Get a single job posting by ID."""
    job_posting = db.query(JobPosting).filter(JobPosting.id == job_posting_id).first()
    if not job_posting:
        raise HTTPException(status_code=404, detail="JobPosting not found")
    return job_posting


@router.post("/job-postings", response_model=JobPostingResponse, status_code=201, tags=["job-postings"])
def create_job_posting(data: JobPostingCreate, db: Session = Depends(get_db)) -> Any:
    """Create a new job posting."""
    # Validate foreign keys
    if data.org_id is not None:
        org = db.query(Org).filter(Org.id == data.org_id).first()
        if not org:
            raise HTTPException(status_code=400, detail=f"Org with id {data.org_id} not found")
    
    if data.venue_id is not None:
        venue = db.query(Venue).filter(Venue.id == data.venue_id).first()
        if not venue:
            raise HTTPException(status_code=400, detail=f"Venue with id {data.venue_id} not found")
    
    job_posting = JobPosting(**data.model_dump())
    db.add(job_posting)
    db.commit()
    db.refresh(job_posting)
    return job_posting


@router.put("/job-postings/{job_posting_id}", response_model=JobPostingResponse, tags=["job-postings"])
def update_job_posting(
    job_posting_id: int,
    data: JobPostingUpdate,
    db: Session = Depends(get_db),
) -> Any:
    """Update an existing job posting."""
    job_posting = db.query(JobPosting).filter(JobPosting.id == job_posting_id).first()
    if not job_posting:
        raise HTTPException(status_code=404, detail="JobPosting not found")
    
    update_data = data.model_dump(exclude_unset=True)
    
    # Validate foreign keys
    if "org_id" in update_data and update_data["org_id"] is not None:
        org = db.query(Org).filter(Org.id == update_data["org_id"]).first()
        if not org:
            raise HTTPException(status_code=400, detail=f"Org with id {update_data['org_id']} not found")
    
    if "venue_id" in update_data and update_data["venue_id"] is not None:
        venue = db.query(Venue).filter(Venue.id == update_data["venue_id"]).first()
        if not venue:
            raise HTTPException(status_code=400, detail=f"Venue with id {update_data['venue_id']} not found")
    
    for field, value in update_data.items():
        setattr(job_posting, field, value)
    
    db.commit()
    db.refresh(job_posting)
    return job_posting


@router.delete("/job-postings/{job_posting_id}", status_code=204, tags=["job-postings"])
def delete_job_posting(job_posting_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a job posting."""
    job_posting = db.query(JobPosting).filter(JobPosting.id == job_posting_id).first()
    if not job_posting:
        raise HTTPException(status_code=404, detail="JobPosting not found")
    
    db.delete(job_posting)
    db.commit()


# ============================================================================
# InstructorAssignment Endpoints
# ============================================================================

@router.get("/instructor-assignments", response_model=list[InstructorAssignmentResponse], tags=["instructor-assignments"])
def list_instructor_assignments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    staff_id: int | None = None,
    activity_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[Any]:
    """List all instructor assignments with pagination and optional filters."""
    query = db.query(InstructorAssignment)
    if staff_id is not None:
        query = query.filter(InstructorAssignment.staff_id == staff_id)
    if activity_id is not None:
        query = query.filter(InstructorAssignment.activity_id == activity_id)
    return query.offset(skip).limit(limit).all()


@router.get("/instructor-assignments/count", tags=["instructor-assignments"])
def count_instructor_assignments(db: Session = Depends(get_db)) -> dict[str, int]:
    """Get total count of instructor assignments."""
    count = db.query(func.count(InstructorAssignment.id)).scalar()
    return {"count": count}


@router.get("/instructor-assignments/{assignment_id}", response_model=InstructorAssignmentResponse, tags=["instructor-assignments"])
def get_instructor_assignment(assignment_id: int, db: Session = Depends(get_db)) -> Any:
    """Get a single instructor assignment by ID."""
    assignment = db.query(InstructorAssignment).filter(InstructorAssignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="InstructorAssignment not found")
    return assignment


@router.post("/instructor-assignments", response_model=InstructorAssignmentResponse, status_code=201, tags=["instructor-assignments"])
def create_instructor_assignment(data: InstructorAssignmentCreate, db: Session = Depends(get_db)) -> Any:
    """Create a new instructor assignment."""
    # Validate foreign keys
    staff = db.query(Staff).filter(Staff.id == data.staff_id).first()
    if not staff:
        raise HTTPException(status_code=400, detail=f"Staff with id {data.staff_id} not found")
    
    activity = db.query(Activity).filter(Activity.id == data.activity_id).first()
    if not activity:
        raise HTTPException(status_code=400, detail=f"Activity with id {data.activity_id} not found")
    
    assignment = InstructorAssignment(**data.model_dump())
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


@router.put("/instructor-assignments/{assignment_id}", response_model=InstructorAssignmentResponse, tags=["instructor-assignments"])
def update_instructor_assignment(
    assignment_id: int,
    data: InstructorAssignmentUpdate,
    db: Session = Depends(get_db),
) -> Any:
    """Update an existing instructor assignment."""
    assignment = db.query(InstructorAssignment).filter(InstructorAssignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="InstructorAssignment not found")
    
    update_data = data.model_dump(exclude_unset=True)
    
    # Validate foreign keys
    if "staff_id" in update_data:
        staff = db.query(Staff).filter(Staff.id == update_data["staff_id"]).first()
        if not staff:
            raise HTTPException(status_code=400, detail=f"Staff with id {update_data['staff_id']} not found")
    
    if "activity_id" in update_data:
        activity = db.query(Activity).filter(Activity.id == update_data["activity_id"]).first()
        if not activity:
            raise HTTPException(status_code=400, detail=f"Activity with id {update_data['activity_id']} not found")
    
    for field, value in update_data.items():
        setattr(assignment, field, value)
    
    db.commit()
    db.refresh(assignment)
    return assignment


@router.delete("/instructor-assignments/{assignment_id}", status_code=204, tags=["instructor-assignments"])
def delete_instructor_assignment(assignment_id: int, db: Session = Depends(get_db)) -> None:
    """Delete an instructor assignment."""
    assignment = db.query(InstructorAssignment).filter(InstructorAssignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="InstructorAssignment not found")
    
    db.delete(assignment)
    db.commit()


# ============================================================================
# InstructorEvaluation Endpoints
# ============================================================================

@router.get("/instructor-evaluations", response_model=list[InstructorEvaluationResponse], tags=["instructor-evaluations"])
def list_instructor_evaluations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    staff_id: int | None = None,
    evaluator_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[Any]:
    """List all instructor evaluations with pagination and optional filters."""
    query = db.query(InstructorEvaluation)
    if staff_id is not None:
        query = query.filter(InstructorEvaluation.staff_id == staff_id)
    if evaluator_id is not None:
        query = query.filter(InstructorEvaluation.evaluator_id == evaluator_id)
    return query.offset(skip).limit(limit).all()


@router.get("/instructor-evaluations/count", tags=["instructor-evaluations"])
def count_instructor_evaluations(db: Session = Depends(get_db)) -> dict[str, int]:
    """Get total count of instructor evaluations."""
    count = db.query(func.count(InstructorEvaluation.id)).scalar()
    return {"count": count}


@router.get("/instructor-evaluations/{evaluation_id}", response_model=InstructorEvaluationResponse, tags=["instructor-evaluations"])
def get_instructor_evaluation(evaluation_id: int, db: Session = Depends(get_db)) -> Any:
    """Get a single instructor evaluation by ID."""
    evaluation = db.query(InstructorEvaluation).filter(InstructorEvaluation.id == evaluation_id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="InstructorEvaluation not found")
    return evaluation


@router.post("/instructor-evaluations", response_model=InstructorEvaluationResponse, status_code=201, tags=["instructor-evaluations"])
def create_instructor_evaluation(data: InstructorEvaluationCreate, db: Session = Depends(get_db)) -> Any:
    """Create a new instructor evaluation."""
    # Validate foreign keys
    staff = db.query(Staff).filter(Staff.id == data.staff_id).first()
    if not staff:
        raise HTTPException(status_code=400, detail=f"Staff with id {data.staff_id} not found")
    
    if data.evaluator_id is not None:
        evaluator = db.query(Person).filter(Person.id == data.evaluator_id).first()
        if not evaluator:
            raise HTTPException(status_code=400, detail=f"Person with id {data.evaluator_id} not found")
    
    evaluation = InstructorEvaluation(**data.model_dump())
    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)
    return evaluation


@router.put("/instructor-evaluations/{evaluation_id}", response_model=InstructorEvaluationResponse, tags=["instructor-evaluations"])
def update_instructor_evaluation(
    evaluation_id: int,
    data: InstructorEvaluationUpdate,
    db: Session = Depends(get_db),
) -> Any:
    """Update an existing instructor evaluation."""
    evaluation = db.query(InstructorEvaluation).filter(InstructorEvaluation.id == evaluation_id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="InstructorEvaluation not found")
    
    update_data = data.model_dump(exclude_unset=True)
    
    # Validate foreign keys
    if "staff_id" in update_data:
        staff = db.query(Staff).filter(Staff.id == update_data["staff_id"]).first()
        if not staff:
            raise HTTPException(status_code=400, detail=f"Staff with id {update_data['staff_id']} not found")
    
    if "evaluator_id" in update_data and update_data["evaluator_id"] is not None:
        evaluator = db.query(Person).filter(Person.id == update_data["evaluator_id"]).first()
        if not evaluator:
            raise HTTPException(status_code=400, detail=f"Person with id {update_data['evaluator_id']} not found")
    
    for field, value in update_data.items():
        setattr(evaluation, field, value)
    
    db.commit()
    db.refresh(evaluation)
    return evaluation


@router.delete("/instructor-evaluations/{evaluation_id}", status_code=204, tags=["instructor-evaluations"])
def delete_instructor_evaluation(evaluation_id: int, db: Session = Depends(get_db)) -> None:
    """Delete an instructor evaluation."""
    evaluation = db.query(InstructorEvaluation).filter(InstructorEvaluation.id == evaluation_id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="InstructorEvaluation not found")
    
    db.delete(evaluation)
    db.commit()
