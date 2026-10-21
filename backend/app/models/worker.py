import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime, ForeignKey, String, Text, func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.core.database import Base


class WorkerProfile(Base):
    __tablename__ = "worker_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )

    display_name: Mapped[str] = mapped_column(
        String(100), nullable=False
    )

    photo_url: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )

    bio: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    city: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )

    availability: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
