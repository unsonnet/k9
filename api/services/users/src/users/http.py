from __future__ import annotations

from pydantic import BaseModel, Field, HttpUrl, StrictBool, field_validator
from shared.config import missing
from shared.helpers import validate_name, validate_user_id
from shared.http import Role
from shared.http.requests import Body, Path, Query

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
        name: Body[str]
        role: Body[Role]
        enabled: Body[StrictBool] = True

        @field_validator("name")
        @classmethod
        def validate_name(cls, value: str) -> str:
            return validate_name(value)

    class Read(BaseModel, frozen=True):
        id: Path[str]

        @field_validator("id")
        @classmethod
        def validate_id(cls, value: str) -> str:
            return value if value == "me" else validate_user_id(value)

    class Update(BaseModel, frozen=True):
        id: Path[str]
        name: Body[str | missing] = missing
        picture: Body[None | missing] = missing
        role: Body[Role | missing] = missing
        enabled: Body[StrictBool | missing] = missing

        @field_validator("id")
        @classmethod
        def validate_id(cls, value: str) -> str:
            return value if value == "me" else validate_user_id(value)

        @field_validator("name")
        @classmethod
        def validate_name(cls, value: str) -> str | missing:
            return validate_name(value)

    class Delete(BaseModel, frozen=True):
        id: Path[str]

        @field_validator("id")
        @classmethod
        def validate_id(cls, value: str) -> str:
            return validate_user_id(value)

    class Picture(BaseModel, frozen=True):
        id: Path[str]

        @field_validator("id")
        @classmethod
        def validate_id(cls, value: str) -> str:
            return value if value == "me" else validate_user_id(value)

    class Reset(BaseModel, frozen=True):
        id: Path[str]

        @field_validator("id")
        @classmethod
        def validate_id(cls, value: str) -> str:
            return value if value == "me" else validate_user_id(value)


# ──── Response Payloads ───────────────────────────────────────────────────────────────


class Response:
    class User(BaseModel, frozen=True, from_attributes=True):
        id: str
        name: str
        picture: HttpUrl
        role: Role
        enabled: StrictBool

    class UserIndex(BaseModel, frozen=True, from_attributes=True):
        id: str
        name: str
        picture: HttpUrl

    class Page(BaseModel, frozen=True, from_attributes=True):
        users: list[Response.UserIndex]
        cursor: str | None

    class Credentials(BaseModel, frozen=True, from_attributes=True):
        id: str
        name: str
        password: str

    class UploadURL(BaseModel, frozen=True, from_attributes=True):
        url: HttpUrl
        fields: dict[str, str]
