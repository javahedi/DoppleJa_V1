from datetime import datetime
from decimal import Decimal
from uuid import UUID
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

WorkType = Literal['minijob', 'part_time', 'full_time', 'temporary']

class JobInput(BaseModel):
    category_id: int
    title: str = Field(min_length=3, max_length=120)
    description: str | None = Field(default=None, max_length=1500)
    city: str = Field(min_length=2, max_length=100)
    work_type: WorkType
    hourly_pay_min: Decimal | None = Field(default=None, ge=0, max_digits=8, decimal_places=2)
    hourly_pay_max: Decimal | None = Field(default=None, ge=0, max_digits=8, decimal_places=2)
    is_active: bool = True

    @field_validator('title', 'city')
    @classmethod
    def not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError('Must not be blank')
        return value

    @model_validator(mode='after')
    def pay_order(self):
        if self.hourly_pay_min is not None and self.hourly_pay_max is not None and self.hourly_pay_max < self.hourly_pay_min:
            raise ValueError('hourly_pay_max must be >= hourly_pay_min')
        return self

class JobOut(JobInput):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    employer_id: UUID
    archived_at: datetime | None = None
    created_at: datetime

class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    slug: str
    name: str
