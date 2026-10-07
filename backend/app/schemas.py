from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

# E.164 style: a leading '+', a country code starting 1-9, then up to 14 digits.
PHONE_NUMBER_PATTERN = r"^\+[1-9]\d{1,14}$"


@field_validator("name", "phone_number")
@classmethod
def strip_whitespace(cls, value):
    return value.strip() if isinstance(value, str) else value


class ContactBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    phone_number: str = Field(..., pattern=PHONE_NUMBER_PATTERN)
    email: Optional[EmailStr] = None
    address: Optional[str] = None


class ContactCreate(ContactBase):
    """Payload for creating a contact."""


class ContactUpdate(BaseModel):
    """Payload for updating a contact. Only fields that are explicitly
    provided are changed; omitted fields keep their current value."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    phone_number: Optional[str] = Field(None, pattern=PHONE_NUMBER_PATTERN)
    email: Optional[EmailStr] = None
    address: Optional[str] = None


class ContactResponse(ContactBase):
    """Contact as returned by the API."""

    id: int
    created_at: datetime

    model_config = {"from_attributes": True}
