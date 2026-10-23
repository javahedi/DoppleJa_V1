"""Simple job listings and curated categories for DoppleJa V1."""
import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.core.database import Base

class JobCategory(Base):
    __tablename__ = "job_categories"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        CheckConstraint("work_type IN ('minijob', 'part_time', 'full_time', 'temporary')", name="ck_jobs_work_type"),
        CheckConstraint("hourly_pay_min IS NULL OR hourly_pay_min >= 0", name="ck_jobs_min_pay"),
        CheckConstraint("hourly_pay_max IS NULL OR hourly_pay_max >= 0", name="ck_jobs_max_pay"),
        CheckConstraint("hourly_pay_min IS NULL OR hourly_pay_max IS NULL OR hourly_pay_max >= hourly_pay_min", name="ck_jobs_pay_range"),
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('employer_profiles.user_id', ondelete='CASCADE'), nullable=False, index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey('job_categories.id'), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    work_type: Mapped[str] = mapped_column(String(20), nullable=False)
    hourly_pay_min: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    hourly_pay_max: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    is_active: Mapped[bool] = mapped_column(Boolean, server_default='true', default=True, nullable=False)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
