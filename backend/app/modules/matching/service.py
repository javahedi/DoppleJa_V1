"""Create at most one match after reciprocal likes.

Call inside a transaction after acquiring a pair-specific advisory lock.
"""
import uuid
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from backend.app.models.match import Match
from backend.app.models.swipe import Swipe


def reconcile_pair(db: Session, job_id: UUID, worker_id: UUID) -> Match | None:
    """Create (or find) a match if both parties have liked the same pair.

    The caller must have acquired a transaction-level pair lock before writing
    a swipe. The unique constraint is a second line of defense.
    """
    likes = set(db.scalars(
        select(Swipe.actor_role).where(
            Swipe.job_id == job_id,
            Swipe.worker_id == worker_id,
            Swipe.action == 'like',
        )
    ).all())
    if likes != {'worker', 'employer'}:
        return None

    statement = (
        insert(Match)
        .values(id=uuid.uuid4(), job_id=job_id, worker_id=worker_id)
        .on_conflict_do_nothing(constraint='uq_matches_job_worker')
    )
    db.execute(statement)
    db.flush()
    return db.scalar(select(Match).where(Match.job_id == job_id, Match.worker_id == worker_id))
