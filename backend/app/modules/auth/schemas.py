from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Literal


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    role: Literal["worker", "employer"]


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    email: EmailStr
    role: str
    email_verified_at: datetime | None


class MessageOut(BaseModel):
    message: str


class ResendVerificationRequest(BaseModel):
    email: EmailStr
