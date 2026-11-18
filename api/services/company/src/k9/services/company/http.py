from __future__ import annotations

from k9.resolvers.http.requests import Body, Path
from k9.types.common import ResourceID, missing
from pydantic import BaseModel, Field

from .provider import HttpUrl, ImageFormat, Industry

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
    website: Body[HttpUrl | None]


class Read(BaseModel, frozen=True):
    id: Path[ResourceID]


class Update(BaseModel, frozen=True):
    id: Path[ResourceID]
    scope: Body[ResourceID | None | missing] = missing
    type: Body[Industry | missing] = missing
    name: Body[str | missing] = Field(missing, min_length=1)
    logo: Body[None | missing] = missing
    website: Body[HttpUrl | None | missing] = missing


class Delete(BaseModel, frozen=True):
    id: Path[ResourceID]


class Upload(BaseModel, frozen=True):
    id: Path[ResourceID]
    format: Body[ImageFormat]
    length: Body[int] = Field(ge=1, le=5 * 1024 * 1024)
