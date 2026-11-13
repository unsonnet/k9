from typing import Literal

from k9.types.common import DateID, ResourceID
from pydantic import BaseModel, EmailStr, Field, HttpUrl
from pydantic_extra_types.phone_numbers import PhoneNumber

__all__ = [
    "Contact",
    "EmailStr",
    "Industry",
    "Job",
    "PhoneNumber",
]


class Job(BaseModel, frozen=True):
    id: DateID
    scope: ResourceID | None
    company: ResourceID
    title: str
    email: EmailStr | None
    phone: PhoneNumber | None


type Industry = Literal["insurance", "manufacturing", "retail"]


class Contact(BaseModel, frozen=True):
    id: ResourceID
    scope: ResourceID | None
    type: Industry
    name: str
    picture: HttpUrl
    email: EmailStr | None
    phone: PhoneNumber | None
    jobs: list[Job] = Field(default_factory=list, alias="$jobs")
