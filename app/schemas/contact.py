"""Contact form schemas."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ContactCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    subject: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=2000)


class ContactOut(ContactCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
