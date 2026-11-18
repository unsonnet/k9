from __future__ import annotations

from k9.resolvers.http.requests import Body, Path
from k9.types.common import ResourceID, missing
from pydantic import BaseModel, Field

from .provider import EmailStr, ImageFormat, Industry, PhoneNumber

__all__ = [
    "Create",
    "Delete",
    "Read",
    "Update",
    "Upload",
]


class Create(BaseModel, frozen=True):
    scope: Body[ResourceID | None]
    type: Body[Industry]
    name: Body[str] = Field(min_length=1)
    email: Body[EmailStr | None]
    phone: Body[PhoneNumber | None]


class Read(BaseModel, frozen=True):
    id: Path[ResourceID]


class Update(BaseModel, frozen=True):
    id: Path[ResourceID]
    scope: Body[ResourceID | None | missing] = missing
    type: Body[Industry | missing] = missing
    name: Body[str | missing] = Field(missing, min_length=1)
    picture: Body[None | missing] = missing
    email: Body[EmailStr | None | missing] = missing
    phone: Body[PhoneNumber | None | missing] = missing


class Delete(BaseModel, frozen=True):
    id: Path[ResourceID]


class Upload(BaseModel, frozen=True):
    id: Path[ResourceID]
    format: Body[ImageFormat]
    length: Body[int] = Field(ge=1, le=5 * 1024 * 1024)
