from datetime import datetime
from uuid import UUID
from typing import Literal
from pydantic import BaseModel, ConfigDict

class SwipeInput(BaseModel):
    job_id: UUID
    action: Literal['like', 'pass']
    worker_id: UUID | None = None  # Required only when the employer swipes

class SwipeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    job_id: UUID
    worker_id: UUID
    actor_role: str
    action: str
    created_at: datetime
    match_id: UUID | None = None
    is_match: bool = False

class CandidateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user_id: UUID
    display_name: str
    profession: str | None
    city: str | None
    availability: str | None
    bio: str | None
    photo_url: str | None
