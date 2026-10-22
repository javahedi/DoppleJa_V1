"""Safe presentation data for a signed-in user's matches and conversations."""
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models import Job, Match, Message, User
from backend.app.models.employer import EmployerProfile
from backend.app.models.worker import WorkerProfile
from backend.app.modules.auth.router import current_user

router = APIRouter(prefix='/api/match-summaries', tags=['Match Summaries'])


class LastMessage(BaseModel):
    content: str
    sender_id: UUID
    created_at: datetime


class MatchSummary(BaseModel):
    match_id: UUID
    job_id: UUID
    job_title: str
    city: str
    other_party_name: str
    matched_at: datetime
    has_messages: bool
    last_message: LastMessage | None = None


@router.get('', response_model=list[MatchSummary])
def summaries(user: User = Depends(current_user), db: Session = Depends(get_db)):
    query = select(Match, Job).join(Job, Job.id == Match.job_id)
    if user.role == 'worker':
        query = query.where(Match.worker_id == user.id)
    elif user.role == 'employer':
        query = query.where(Job.employer_id == user.id)
    else:
        raise HTTPException(status_code=403, detail='Invalid role')

    pairs = db.execute(query.order_by(Match.created_at.desc(), Match.id.desc()).limit(200)).all()
    result = []
    for match, job in pairs:
        if user.role == 'worker':
            employer = db.get(EmployerProfile, job.employer_id)
            other_name = employer.display_name if employer else 'Arbeitgeber'
        else:
            worker = db.get(WorkerProfile, match.worker_id)
            other_name = worker.display_name if worker else 'Arbeitsuchend'
        last = db.scalar(
            select(Message).where(Message.match_id == match.id)
            .order_by(Message.created_at.desc(), Message.id.desc()).limit(1)
        )
        result.append(MatchSummary(
            match_id=match.id,
            job_id=job.id,
            job_title=job.title,
            city=job.city,
            other_party_name=other_name,
            matched_at=match.created_at,
            has_messages=last is not None,
            last_message=LastMessage(
                content=last.content, sender_id=last.sender_id, created_at=last.created_at
            ) if last else None,
        ))
    return result
