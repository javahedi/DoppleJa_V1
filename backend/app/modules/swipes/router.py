from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models import Job, Swipe, User, WorkerProfile
from backend.app.modules.matching.service import reconcile_pair
from backend.app.modules.auth.router import current_user
from backend.app.modules.jobs.schemas import JobOut
from backend.app.modules.swipes.schemas import CandidateOut, SwipeInput, SwipeOut

router = APIRouter(prefix='/api', tags=['Swipe Discovery'])

@router.get('/discovery/jobs', response_model=list[JobOut])
def discover_jobs(city: str | None = Query(None, max_length=100),
                  category_id: int | None = Query(None),
                  user: User = Depends(current_user), db: Session = Depends(get_db)):
    if user.role != 'worker':
        raise HTTPException(403, 'Worker account required')
    already_swiped = select(Swipe.job_id).where(Swipe.worker_id == user.id, Swipe.actor_role == 'worker')
    query = select(Job).where(Job.is_active.is_(True), Job.id.not_in(already_swiped))
    if city:
        query = query.where(Job.city.ilike(city.strip()))
    if category_id is not None:
        query = query.where(Job.category_id == category_id)
    return db.scalars(query.order_by(Job.created_at.desc(), Job.id).limit(50)).all()

@router.get('/discovery/workers', response_model=list[CandidateOut])
def discover_workers(job_id: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if user.role != 'employer':
        raise HTTPException(403, 'Employer account required')
    job = db.get(Job, job_id)
    if job is None or job.employer_id != user.id:
        raise HTTPException(404, 'Job not found')
    if not job.is_active:
        raise HTTPException(409, 'Job is inactive')
    already_swiped = select(Swipe.worker_id).where(Swipe.job_id == job_id, Swipe.actor_role == 'employer')
    query = select(WorkerProfile).where(WorkerProfile.user_id.not_in(already_swiped))
    return db.scalars(query.order_by(WorkerProfile.created_at.desc(), WorkerProfile.user_id).limit(50)).all()

@router.post('/swipes', response_model=SwipeOut, status_code=201)
def swipe(body: SwipeInput, user: User = Depends(current_user), db: Session = Depends(get_db)):
    job = db.get(Job, body.job_id)
    if job is None or not job.is_active:
        raise HTTPException(404, 'Active job not found')
    if user.role == 'worker':
        if body.worker_id is not None and body.worker_id != user.id:
            raise HTTPException(403, 'Cannot swipe as another worker')
        if db.get(WorkerProfile, user.id) is None:
            raise HTTPException(400, 'Create your worker profile first')
        worker_id = user.id
    elif user.role == 'employer':
        if job.employer_id != user.id:
            raise HTTPException(403, 'Not your job')
        if body.worker_id is None:
            raise HTTPException(422, 'worker_id required for employer swipe')
        worker_id = body.worker_id
        if db.get(WorkerProfile, worker_id) is None:
            raise HTTPException(404, 'Worker profile not found')
    else:
        raise HTTPException(403, 'Invalid account role')

    # Serialize swipes for the same worker-job pair (including concurrent likes).
    # PostgreSQL transaction advisory lock is automatically released on commit.
    pair_key = f'{body.job_id}:{worker_id}'
    db.execute(select(func.pg_advisory_xact_lock(func.hashtextextended(pair_key, 0))))

    existing = db.scalar(select(Swipe).where(
        Swipe.job_id == body.job_id,
        Swipe.worker_id == worker_id,
        Swipe.actor_role == user.role,
    ))
    if existing and existing.action != body.action:
        raise HTTPException(409, 'Already swiped this card')

    value = existing
    if value is None:
        value = Swipe(job_id=body.job_id, worker_id=worker_id,
                      actor_role=user.role, action=body.action)
        db.add(value)
        db.flush()

    # Reconciliation also works on identical replays, repairing missing matches.
    match = reconcile_pair(db, body.job_id, worker_id) if body.action == 'like' else None
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, 'Already swiped this card')
    db.refresh(value)
    return SwipeOut.model_validate(value).model_copy(update={
        'match_id': match.id if match else None,
        'is_match': match is not None,
    })
