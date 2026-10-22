from uuid import UUID
from datetime import datetime, timezone
from typing import Literal
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models import User, EmployerProfile, Job, JobCategory
from backend.app.modules.auth.router import current_user
from backend.app.modules.jobs.schemas import CategoryOut, JobInput, JobOut

router = APIRouter(prefix='/api', tags=['Jobs'])

def require_employer(user: User = Depends(current_user)) -> User:
    if user.role != 'employer':
        raise HTTPException(403, 'Employer account required')
    return user

def require_worker(user: User = Depends(current_user)) -> User:
    if user.role != 'worker':
        raise HTTPException(403, 'Worker account required')
    return user

@router.get('/categories', response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    return db.scalars(select(JobCategory).order_by(JobCategory.id)).all()

@router.post('/jobs', response_model=JobOut, status_code=201)
def create_job(body: JobInput, user: User = Depends(require_employer), db: Session = Depends(get_db)):
    if db.get(EmployerProfile, user.id) is None:
        raise HTTPException(400, 'Create your employer profile first')
    if db.get(JobCategory, body.category_id) is None:
        raise HTTPException(422, 'Unknown job category')
    job = Job(employer_id=user.id, **body.model_dump())
    db.add(job)
    db.commit()
    db.refresh(job)
    return job

@router.get('/jobs/mine', response_model=list[JobOut])
def my_jobs(user: User = Depends(require_employer), db: Session = Depends(get_db)):
    return db.scalars(select(Job).where(Job.employer_id == user.id).order_by(Job.created_at.desc())).all()

@router.get('/jobs/discover', response_model=list[JobOut])
def discover_jobs(
    city: str | None = Query(default=None, max_length=100),
    category_id: int | None = Query(default=None),
    user: User = Depends(require_worker),
    db: Session = Depends(get_db),
):
    query = select(Job).where(Job.is_active.is_(True), Job.archived_at.is_(None))
    if city:
        query = query.where(Job.city.ilike(city.strip()))
    if category_id is not None:
        query = query.where(Job.category_id == category_id)
    return db.scalars(query.order_by(Job.created_at.desc()).limit(50)).all()

@router.get('/jobs/{job_id}', response_model=JobOut)
def job_details(job_id: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if job is None or ((not job.is_active or job.archived_at is not None) and job.employer_id != user.id):
        raise HTTPException(404, 'Job not found')
    return job

@router.put('/jobs/{job_id}', response_model=JobOut)
def update_job(job_id: UUID, body: JobInput, user: User = Depends(require_employer), db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if job is None or job.employer_id != user.id:
        raise HTTPException(404, 'Job not found')
    if job.archived_at is not None:
        raise HTTPException(409, 'Archived jobs cannot be edited')
    if db.get(JobCategory, body.category_id) is None:
        raise HTTPException(422, 'Unknown job category')
    for field, value in body.model_dump().items():
        setattr(job, field, value)
    db.commit()
    db.refresh(job)
    return job


class JobStatusAction(BaseModel):
    action: Literal['pause', 'reactivate', 'archive']


@router.patch('/jobs/{job_id}/status', response_model=JobOut)
def change_job_status(job_id: UUID, body: JobStatusAction,
                      user: User = Depends(require_employer), db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if job is None or job.employer_id != user.id:
        raise HTTPException(404, 'Job not found')
    if job.archived_at is not None:
        raise HTTPException(409, 'Archived jobs cannot be changed')
    if body.action == 'archive':
        job.archived_at = datetime.now(timezone.utc)
        job.is_active = False
    else:
        job.is_active = body.action == 'reactivate'
    db.commit()
    db.refresh(job)
    return job
