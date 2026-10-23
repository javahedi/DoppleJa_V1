"""One immutable 1–5 star review per participant and completed match."""
import uuid
from datetime import datetime
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.core.database import Base

class Review(Base):
    __tablename__ = 'reviews'
    __table_args__ = (
        UniqueConstraint('match_id','reviewer_id',name='uq_reviews_match_reviewer'),
        CheckConstraint('stars >= 1 AND stars <= 5',name='ck_reviews_stars'),
        CheckConstraint('reviewer_id <> reviewee_id',name='ck_reviews_distinct_users'),
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    match_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),ForeignKey('matches.id',ondelete='CASCADE'),nullable=False,index=True)
    reviewer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),ForeignKey('users.id',ondelete='CASCADE'),nullable=False)
    reviewee_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),ForeignKey('users.id',ondelete='CASCADE'),nullable=False,index=True)
    stars: Mapped[int] = mapped_column(Integer,nullable=False)
    comment: Mapped[str | None] = mapped_column(String(1000),nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),server_default=func.now(),nullable=False)
