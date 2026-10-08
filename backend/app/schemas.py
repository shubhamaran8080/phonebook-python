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


class LoginRequest(BaseModel):
    """Login payload. `username` accepts a username or an email address."""

    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class UserResponse(BaseModel):
    """User info returned by the API (never includes the password hash)."""

    id: int
    username: str
    email: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class StatsResponse(BaseModel):
    """Phonebook statistics for the dashboard."""

    total_contacts: int
    recent_contacts: int
    with_email: int
    with_phone: int
    recent_list: list[ContactResponse]
