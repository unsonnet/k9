from __future__ import annotations

from typing import Literal

from k9.resolvers.http.requests import Body, ImageFormat, Path, Query
from k9.types.common import Name, Role, UserID, missing
from pydantic import BaseModel, Field

__all__ = [
    "Create",
    "Delete",
    "List",
    "Read",
    "Reset",
    "Update",
    "Upload",
]


class List(BaseModel, frozen=True):
    limit: Query[int] = Field(25, ge=1, le=60)
    cursor: Query[str | missing] = missing


class Create(BaseModel, frozen=True):
    role: Body[Role]
    name: Body[Name]
    enabled: Body[bool] = True


class Read(BaseModel, frozen=True):
    id: Path[UserID | Literal["me"]]


class Update(BaseModel, frozen=True):
    id: Path[UserID | Literal["me"]]
    role: Body[Role | missing] = missing
    name: Body[Name | missing] = missing
    picture: Body[None | missing] = missing
    enabled: Body[bool | missing] = missing


class Delete(BaseModel, frozen=True):
    id: Path[UserID]


class Upload(BaseModel, frozen=True):
    id: Path[UserID | Literal["me"]]
    format: Body[ImageFormat]
    length: Body[int] = Field(ge=1, le=5 * 1024 * 1024)


class Reset(BaseModel, frozen=True):
    id: Path[UserID | Literal["me"]]
