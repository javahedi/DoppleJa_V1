"""Only participants in an existing match can read or send messages."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models import Job, Match, Message, User
from backend.app.modules.auth.router import current_user
from backend.app.modules.matching.router import accessible_match
from backend.app.modules.chat.schemas import ChatOut, MessageCreate, MessageOut

router = APIRouter(tags=['Chat'])


def require_match(db: Session, match_id: UUID, user: User) -> Match:
    match = db.get(Match, match_id)
    if match is None or not accessible_match(db, match, user):
        # Do not reveal the existence of private matches to outsiders.
        raise HTTPException(status_code=404, detail='Match not found')
    return match


@router.get('/api/chats', response_model=list[ChatOut])
def my_chats(user: User = Depends(current_user), db: Session = Depends(get_db)):
    query = select(Match)
    if user.role == 'worker':
        query = query.where(Match.worker_id == user.id)
    elif user.role == 'employer':
        query = query.join(Job, Job.id == Match.job_id).where(Job.employer_id == user.id)
    else:
        raise HTTPException(403, 'Invalid role')
    matches = db.scalars(query.order_by(Match.created_at.desc(), Match.id)).all()
    chats = []
    for match in matches:
        last = db.scalar(
            select(Message).where(Message.match_id == match.id)
            .order_by(Message.created_at.desc(), Message.id.desc()).limit(1)
        )
        chats.append(ChatOut(match_id=match.id, job_id=match.job_id,
                             worker_id=match.worker_id,
                             last_message=MessageOut.model_validate(last) if last else None))
    return chats


@router.get('/api/matches/{match_id}/messages', response_model=list[MessageOut])
def list_messages(match_id: UUID,
                  limit: int = Query(50, ge=1, le=100),
                  offset: int = Query(0, ge=0),
                  user: User = Depends(current_user), db: Session = Depends(get_db)):
    require_match(db, match_id, user)
    # Stable oldest-first ordering for a simple initial chat view.
    return db.scalars(
        select(Message).where(Message.match_id == match_id)
        .order_by(Message.created_at.asc(), Message.id.asc())
        .offset(offset).limit(limit)
    ).all()


@router.post('/api/matches/{match_id}/messages', response_model=MessageOut, status_code=201)
def send_message(match_id: UUID, body: MessageCreate,
                 user: User = Depends(current_user), db: Session = Depends(get_db)):
    require_match(db, match_id, user)
    message = Message(match_id=match_id, sender_id=user.id, content=body.content)
    db.add(message)
    db.commit()
    db.refresh(message)
    return message
