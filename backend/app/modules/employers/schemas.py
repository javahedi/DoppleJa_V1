from datetime import datetime
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator


class EmployerProfileInput(BaseModel):
    employer_type: Literal["private", "business"]
    display_name: str = Field(min_length=2, max_length=150)
    category: str | None = Field(default=None, max_length=100)
    city: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    photo_url: str | None = Field(default=None, max_length=500)

    @field_validator("display_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Please enter a name of at least two characters")
        return v

    @field_validator("category", "city", "description", "photo_url")
    @classmethod
    def clean_optional(cls, v: str | None) -> str | None:
        return v.strip() or None if v is not None else None


class EmployerProfileOut(EmployerProfileInput):
    model_config = ConfigDict(from_attributes=True)
    user_id: UUID
    created_at: datetime
