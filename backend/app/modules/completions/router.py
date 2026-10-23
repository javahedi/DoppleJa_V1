"""Mutual job completion and one review per side of a matched engagement."""
from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models import Job, Match, User
from backend.app.models.completion import CompletionConfirmation
from backend.app.models.review import Review
from backend.app.modules.auth.router import current_user
from backend.app.modules.matching.router import accessible_match

router = APIRouter(tags=['Completed Jobs & Reviews'])

class ReviewCreate(BaseModel):
    stars: int = Field(ge=1,le=5)
    comment: str | None = Field(default=None,max_length=1000)

class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    match_id: UUID
    reviewer_id: UUID
    reviewee_id: UUID
    stars: int
    comment: str | None
    created_at: datetime

class CompletionStatus(BaseModel):
    match_id: UUID
    confirmed_by_me: bool
    confirmed_by_other: bool
    completed: bool
    my_review: ReviewOut | None = None
    their_review: ReviewOut | None = None

def _participants(db: Session, match_id: UUID, user: User):
    match = db.get(Match, match_id)
    if match is None or not accessible_match(db, match, user):
        raise HTTPException(404,'Match not found')
    job = db.get(Job, match.job_id)
    if job is None:
        raise HTTPException(404,'Job not found')
    return match, job, match.worker_id if user.role == 'employer' else job.employer_id

def _status(db, match, user, other_id):
    confirmations=set(db.scalars(select(CompletionConfirmation.user_id).where(CompletionConfirmation.match_id==match.id)).all())
    reviews=db.scalars(select(Review).where(Review.match_id==match.id)).all()
    mine=next((r for r in reviews if r.reviewer_id==user.id),None)
    theirs=next((r for r in reviews if r.reviewer_id==other_id),None)
    return CompletionStatus(match_id=match.id,confirmed_by_me=user.id in confirmations,
        confirmed_by_other=other_id in confirmations,completed={user.id,other_id}.issubset(confirmations),
        my_review=ReviewOut.model_validate(mine) if mine else None,
        their_review=ReviewOut.model_validate(theirs) if theirs else None)

@router.get('/api/matches/{match_id}/completion',response_model=CompletionStatus)
def completion_status(match_id:UUID,user:User=Depends(current_user),db:Session=Depends(get_db)):
    match,job,other_id=_participants(db,match_id,user)
    return _status(db,match,user,other_id)

@router.post('/api/matches/{match_id}/confirm-completion',response_model=CompletionStatus)
def confirm_completion(match_id:UUID,user:User=Depends(current_user),db:Session=Depends(get_db)):
    match,job,other_id=_participants(db,match_id,user)
    if not db.scalar(select(CompletionConfirmation.id).where(CompletionConfirmation.match_id==match_id,CompletionConfirmation.user_id==user.id)):
        db.add(CompletionConfirmation(match_id=match_id,user_id=user.id))
        try:db.commit()
        except IntegrityError:
            db.rollback() # concurrent confirmation, idempotent
    return _status(db,match,user,other_id)

@router.post('/api/matches/{match_id}/reviews',response_model=ReviewOut,status_code=201)
def create_review(match_id:UUID,body:ReviewCreate,user:User=Depends(current_user),db:Session=Depends(get_db)):
    match,job,other_id=_participants(db,match_id,user)
    status=_status(db,match,user,other_id)
    if not status.completed:
        raise HTTPException(409,'Both participants must confirm job completion before reviewing')
    if status.my_review:
        raise HTTPException(409,'You have already reviewed this engagement')
    comment=body.comment.strip() if body.comment else None
    review=Review(match_id=match_id,reviewer_id=user.id,reviewee_id=other_id,stars=body.stars,comment=comment or None)
    db.add(review)
    try:db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409,'Review already submitted')
    db.refresh(review)
    return review

class RatingSummary(BaseModel):
    user_id: UUID
    average: float | None
    count: int

@router.get('/api/users/{user_id}/rating',response_model=RatingSummary)
def user_rating(user_id:UUID,user:User=Depends(current_user),db:Session=Depends(get_db)):
    if not db.get(User,user_id):raise HTTPException(404,'User not found')
    average,count=db.execute(select(func.avg(Review.stars),func.count(Review.id)).where(Review.reviewee_id==user_id)).one()
    return RatingSummary(user_id=user_id,average=round(float(average),1) if average is not None else None,count=count)


@router.get('/api/users/{user_id}/reviews',response_model=list[ReviewOut])
def received_user_reviews(user_id:UUID,limit:int=20,user:User=Depends(current_user),db:Session=Depends(get_db)):
    """Public-to-signed-in-users received reviews, newest first. Never show reviews given by this user."""
    if not db.get(User,user_id):
        raise HTTPException(404,'User not found')
    if not 1 <= limit <= 50:
        raise HTTPException(422,'limit must be between 1 and 50')
    reviews=db.scalars(select(Review).where(Review.reviewee_id==user_id)
        .order_by(Review.created_at.desc(),Review.id.desc()).limit(limit)).all()
    return [ReviewOut.model_validate(review) for review in reviews]
