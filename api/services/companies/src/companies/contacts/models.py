from datetime import datetime

from pydantic import BaseModel, HttpUrl
from pydantic.networks import EmailStr
from pydantic_extra_types.phone_numbers import PhoneNumber

__all__ = [
    "Contact",
]


class Contact(BaseModel, frozen=True):
    id: str
    name: str
    title: str | None
    picture: HttpUrl
    email: EmailStr | None
    phone: PhoneNumber | None
    created_at: datetime
    updated_at: datetime | None
