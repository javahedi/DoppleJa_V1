from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models import Job, Match, User
from backend.app.modules.auth.router import current_user
from backend.app.modules.matching.schemas import MatchOut

router = APIRouter(prefix='/api/matches', tags=['Matches'])


def accessible_match(db: Session, match: Match, user: User) -> bool:
    if user.role == 'worker':
        return match.worker_id == user.id
    if user.role == 'employer':
        job = db.get(Job, match.job_id)
        return job is not None and job.employer_id == user.id
    return False


@router.get('', response_model=list[MatchOut])
def my_matches(user: User = Depends(current_user), db: Session = Depends(get_db)):
    query = select(Match)
    if user.role == 'worker':
        query = query.where(Match.worker_id == user.id)
    elif user.role == 'employer':
        query = query.join(Job, Job.id == Match.job_id).where(Job.employer_id == user.id)
    else:
        raise HTTPException(403, 'Invalid role')
    return db.scalars(query.order_by(Match.created_at.desc(), Match.id)).all()


@router.get('/{match_id}', response_model=MatchOut)
def match_detail(match_id: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)):
    match = db.get(Match, match_id)
    if match is None or not accessible_match(db, match, user):
        raise HTTPException(404, 'Match not found')
    return match
