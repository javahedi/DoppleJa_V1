from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class MatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    job_id: UUID
    worker_id: UUID
    created_at: datetime
