"""Authenticated photo abuse reports. No machine-generated content judgments."""
from __future__ import annotations

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models import User
from backend.app.modules.auth.router import current_user
from backend.app.modules.media.security import IDENT, PREFIX

router = APIRouter(prefix='/api/moderation', tags=['Photo reports'])
REASONS = frozenset({'sexual_content', 'violence', 'hate', 'impersonation', 'privacy', 'other'})

class PhotoReportIn(BaseModel):
    photo_url: str = Field(min_length=1, max_length=200)
    reason: str = Field(min_length=1, max_length=32)
    explanation: str | None = Field(default=None, max_length=500)


def photo_identifier(photo_url: str) -> str:
    if not photo_url.startswith(PREFIX) or not photo_url.endswith('.webp'):
        raise HTTPException(422, 'Invalid DoppleJa photo URL')
    name = photo_url[len(PREFIX):-5]
    if not IDENT.fullmatch(name):
        raise HTTPException(422, 'Invalid DoppleJa photo URL')
    return name

@router.post('/photo-reports', status_code=201)
def report_photo(body: PhotoReportIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if body.reason not in REASONS:
        raise HTTPException(422, 'Unsupported report reason')
    name = photo_identifier(body.photo_url)
    # Lock by reporting account so rapid simultaneous requests cannot evade daily quota.
    db.execute(text('SELECT pg_advisory_xact_lock(hashtext(:uid))'), {'uid': str(user.id)})
    owner = db.execute(text('''
        SELECT user_id FROM worker_profiles WHERE photo_url = :url
        UNION ALL
        SELECT user_id FROM employer_profiles WHERE photo_url = :url
        LIMIT 1
    '''), {'url': body.photo_url}).scalar_one_or_none()
    if owner is None:
        db.rollback()
        raise HTTPException(404, 'Profile photo not found')
    if str(owner) == str(user.id):
        db.rollback()
        raise HTTPException(400, 'Cannot report your own profile photo')
    count = db.execute(text('''
        SELECT count(*) FROM photo_reports WHERE reporter_id = :uid
        AND created_at >= now() - interval '24 hours'
    '''), {'uid': user.id}).scalar_one()
    if count >= 5:
        db.rollback()
        raise HTTPException(429, 'Too many reports; try again later')
    existing = db.execute(text('''
        SELECT 1 FROM photo_reports WHERE reporter_id = :uid AND photo_name = :name
    '''), {'uid': user.id, 'name': name}).scalar_one_or_none()
    if existing:
        db.rollback()
        return {'message': 'Report already received'}
    try:
        db.execute(text('''
            INSERT INTO photo_reports(reporter_id, owner_id, photo_name, reason, explanation)
            VALUES (:reporter, :owner, :name, :reason, :explanation)
        '''), {'reporter': user.id, 'owner': owner, 'name': name,
               'reason': body.reason, 'explanation': body.explanation})
        db.commit()
    except IntegrityError:
        db.rollback()
        return {'message': 'Report already received'}
    return {'message': 'Report received for review'}
