import uuid
from datetime import datetime
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, UniqueConstraint, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.core.database import Base

class Swipe(Base):
    __tablename__ = 'swipes'
    __table_args__ = (
        CheckConstraint("actor_role IN ('worker','employer')", name='ck_swipes_actor_role'),
        CheckConstraint("action IN ('like','pass')", name='ck_swipes_action'),
        UniqueConstraint('job_id', 'worker_id', 'actor_role', name='uq_swipe_pair_actor'),
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False, index=True)
    worker_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('worker_profiles.user_id', ondelete='CASCADE'), nullable=False, index=True)
    actor_role: Mapped[str] = mapped_column(String(20), nullable=False)
    action: Mapped[str] = mapped_column(String(8), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
