from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator

class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=2000)

    @field_validator('content')
    @classmethod
    def clean_content(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError('Message cannot be empty')
        return value

class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    match_id: UUID
    sender_id: UUID
    content: str
    created_at: datetime

class ChatOut(BaseModel):
    match_id: UUID
    job_id: UUID
    worker_id: UUID
    last_message: MessageOut | None = None
