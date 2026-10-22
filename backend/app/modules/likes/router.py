"""Workers can revisit previously liked jobs, including inactive/archived ones."""
from datetime import datetime
from uuid import UUID
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models import Job, JobCategory, Match, Swipe, User
from backend.app.modules.auth.router import current_user

router = APIRouter(prefix="/api/workers", tags=["Worker Likes"])

class LikedJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    job_id: UUID
    title: str
    city: str
    category: str
    work_type: str
    description: str | None
    hourly_pay_min: float | None
    hourly_pay_max: float | None
    liked_at: datetime
    status: Literal['pending', 'matched', 'unavailable']
    match_id: UUID | None = None

@router.get('/me/likes', response_model=list[LikedJobOut])
def my_likes(
    status: Literal['pending', 'matched', 'unavailable'] | None = Query(default=None),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    if user.role != 'worker':
        raise HTTPException(status_code=403, detail='Worker account required')

    # Do not filter inactive/archived jobs: users need to see their history.
    records = db.execute(
        select(Swipe, Job, JobCategory, Match)
        .join(Job, Job.id == Swipe.job_id)
        .join(JobCategory, JobCategory.id == Job.category_id)
        .outerjoin(Match, (Match.job_id == Swipe.job_id) & (Match.worker_id == Swipe.worker_id))
        .where(Swipe.worker_id == user.id, Swipe.actor_role == 'worker', Swipe.action == 'like')
        .order_by(Swipe.created_at.desc(), Swipe.id.desc())
        .limit(200)
    ).all()
    result = []
    for swipe, job, category, match in records:
        # Unavailable has priority when a matched job is later paused/archived.
        current_status = ('unavailable' if (not job.is_active or job.archived_at is not None)
                          else 'matched' if match is not None else 'pending')
        if status and status != current_status:
            continue
        result.append(LikedJobOut(
            job_id=job.id, title=job.title, city=job.city,
            category=category.name, work_type=job.work_type,
            description=job.description,
            hourly_pay_min=float(job.hourly_pay_min) if job.hourly_pay_min is not None else None,
            hourly_pay_max=float(job.hourly_pay_max) if job.hourly_pay_max is not None else None,
            liked_at=swipe.created_at,
            status=current_status,
            match_id=match.id if match is not None else None,
        ))
    return result
