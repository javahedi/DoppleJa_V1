"""Text-only message in an existing mutual match."""
import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.core.database import Base

class Message(Base):
    __tablename__ = 'messages'
    __table_args__ = (Index('ix_messages_match_created', 'match_id', 'created_at', 'id'),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    match_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('matches.id', ondelete='CASCADE'), nullable=False)
    sender_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    content: Mapped[str] = mapped_column(String(2000), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
