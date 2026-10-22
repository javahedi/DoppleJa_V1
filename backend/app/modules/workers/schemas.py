from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator

class WorkerProfileInput(BaseModel):
    display_name: str = Field(min_length=2, max_length=100)
    profession: str | None = Field(default=None, max_length=100)
    city: str | None = Field(default=None, max_length=100)
    availability: str | None = Field(default=None, max_length=50)
    bio: str | None = Field(default=None, max_length=500)
    photo_url: str | None = Field(default=None, max_length=500)

    @field_validator("display_name")
    @classmethod
    def non_blank_name(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise ValueError("Name must contain at least 2 characters")
        return value

    @field_validator("profession", "city", "availability", "bio", "photo_url")
    @classmethod
    def normalize_optional(cls, value: str | None) -> str | None:
        return value.strip() or None if value is not None else None

class WorkerProfileOut(WorkerProfileInput):
    model_config = ConfigDict(from_attributes=True)
    user_id: UUID
    created_at: datetime
