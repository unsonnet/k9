from __future__ import annotations

from typing import Literal

from k9.resolvers.http.requests import Body, Path, Query
from k9.shared.config import missing
from pydantic import BaseModel, Field

from .provider import HttpUrl, ImageFormat, Name, Password, Role, UserID

__all__ = [
    "Request",
    "Response",
]


# ──── Request Payloads ────────────────────────────────────────────────────────────────


class Request:
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

    class Picture(BaseModel, frozen=True):
        id: Path[UserID | Literal["me"]]
        format: Body[ImageFormat]
        length: Body[int] = Field(ge=1, le=5 * 1024 * 1024)

    class Reset(BaseModel, frozen=True):
        id: Path[UserID | Literal["me"]]


# ──── Response Payloads ───────────────────────────────────────────────────────────────


class Response:
    class User(BaseModel, frozen=True, from_attributes=True):
        id: UserID
        role: Role
        name: Name
        picture: HttpUrl
        enabled: bool

    class Page(BaseModel, frozen=True, from_attributes=True):
        users: list[Response.User]
        cursor: str | None

    class Credentials(BaseModel, frozen=True, from_attributes=True):
        id: UserID
        name: Name
        password: Password

    class Upload(BaseModel, frozen=True, from_attributes=True):
        url: HttpUrl
        headers: dict[str, str]
