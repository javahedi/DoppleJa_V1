"""Employer's own positive swipes, restricted to jobs owned by the authenticated employer."""
from datetime import datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models import Job, Match, Swipe, User
from backend.app.models.worker import WorkerProfile
from backend.app.modules.auth.router import current_user

router = APIRouter(prefix='/api/employers', tags=['Employer Likes'])

class EmployerLikedWorker(BaseModel):
    worker_id: UUID
    worker_name: str
    profession: str | None = None
    city: str | None = None
    job_id: UUID
    job_title: str
    liked_at: datetime
    status: Literal['pending', 'matched']
    match_id: UUID | None = None

@router.get('/me/likes', response_model=list[EmployerLikedWorker])
def employer_likes(user: User = Depends(current_user), db: Session = Depends(get_db)):
    if user.role != 'employer':
        raise HTTPException(status_code=403, detail='Employer account required')
    records = db.execute(
        select(Swipe, Job, WorkerProfile, Match)
        .join(Job, Job.id == Swipe.job_id)
        .join(WorkerProfile, WorkerProfile.user_id == Swipe.worker_id)
        .outerjoin(Match, (Match.job_id == Swipe.job_id) & (Match.worker_id == Swipe.worker_id))
        .where(Job.employer_id == user.id, Swipe.actor_role == 'employer', Swipe.action == 'like')
        .order_by(Swipe.created_at.desc(), Swipe.id.desc())
        .limit(200)
    ).all()
    return [EmployerLikedWorker(
        worker_id=swipe.worker_id,
        worker_name=worker.display_name,
        profession=worker.profession,
        city=worker.city,
        job_id=job.id,
        job_title=job.title,
        liked_at=swipe.created_at,
        status='matched' if match else 'pending',
        match_id=match.id if match else None,
    ) for swipe, job, worker, match in records]
