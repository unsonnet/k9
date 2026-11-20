from __future__ import annotations

from k9.resolvers.http.requests import Body, Path
from k9.types.common import DateID, ResourceID, missing
from pydantic import BaseModel, Field

from .provider import EmailStr, PhoneNumber

__all__ = [
    "Create",
    "Delete",
    "Update",
]


class Create(BaseModel, frozen=True):
    id: Path[ResourceID]
    date: Path[DateID]
    scope: Body[ResourceID | None]
    company: Body[ResourceID | None]
    title: Body[str]
    email: Body[EmailStr | None]
    phone: Body[PhoneNumber | None]


class Update(BaseModel, frozen=True):
    id: Path[ResourceID]
    date: Path[DateID]
    scope: Body[ResourceID | None | missing] = missing
    company: Body[ResourceID | None | missing] = missing
    title: Body[str | missing] = Field(missing, min_length=1)
    email: Body[EmailStr | None | missing] = missing
    phone: Body[PhoneNumber | None | missing] = missing


class Delete(BaseModel, frozen=True):
    id: Path[ResourceID]
    date: Path[DateID]
