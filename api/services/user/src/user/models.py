from datetime import datetime
from typing import Self

from pydantic import BaseModel, HttpUrl, StrictBool, field_validator
from shared.http import ImageMIMEType, Role
from shared.http.requests import Body, Path, Query
from shared.provider.opensearch import sanitize_query
from shared.provider.user import normalize_name, validate_id, validate_name

__all__ = [
    "User",
    "UserSummary",
    "Page",
    "Credentials",
    "UploadForm",
    "Request",
    "Response",
]


class User(BaseModel, frozen=True):
    id: str
    name: str
    picture: HttpUrl
    role: Role
    enabled: bool
    created_at: datetime
    updated_at: datetime | None = None
    last_login_at: datetime | None = None


class UserSummary(BaseModel, frozen=True):
    id: str
    name: str
    picture: HttpUrl


class Page(BaseModel, frozen=True):
    users: list[UserSummary]
    cursor: str | None = None


class Credentials(BaseModel, frozen=True):
    id: str
    name: str
    password: str


class UploadForm(BaseModel, frozen=True):
    url: str
    fields: dict[str, str]


# ──── Request Payloads ────────────────────────────────────────────────────────────────


class Request:
    class List(BaseModel, frozen=True):
        q: Query[str | None] = None
        limit: Query[int | None] = None
        cursor: Query[str | None] = None

        @field_validator("q")
        @classmethod
        def sanitize_q(cls, value: str | None) -> str | None:
            return sanitize_query(normalize_name(value)) if value else None

        @field_validator("limit")
        @classmethod
        def clamp_limit(cls, value: int | None) -> int | None:
            return max(min(value, 60), 1) if value is not None else None

    class Create(BaseModel, frozen=True):
        name: Body[str]
        role: Body[Role]
        enabled: Body[StrictBool] = True

        @field_validator("name")
        @classmethod
        def validate_name(cls, value: str) -> str:
            return validate_name(normalize_name(value))

    class Read(BaseModel, frozen=True):
        id: Path[str]

        @field_validator("id")
        @classmethod
        def validate_id(cls, value: str) -> str:
            return value if value == "me" else validate_id(value)

    class Update(BaseModel, frozen=True):
        id: Path[str]
        name: Body[str | None] = None
        role: Body[Role | None] = None
        enabled: Body[StrictBool | None] = None

        @field_validator("id")
        @classmethod
        def validate_id(cls, value: str) -> str:
            return value if value == "me" else validate_id(value)

        @field_validator("name")
        @classmethod
        def validate_name(cls, value: str | None) -> str | None:
            return validate_name(normalize_name(value)) if value else None

    class Delete(BaseModel, frozen=True):
        id: Path[str]

        @field_validator("id")
        @classmethod
        def validate_id(cls, value: str) -> str:
            return validate_id(value)

    class Picture(BaseModel, frozen=True):
        id: Path[str]
        contentType: Body[ImageMIMEType]

        @field_validator("id")
        @classmethod
        def validate_id(cls, value: str) -> str:
            return value if value == "me" else validate_id(value)

    class Reset(BaseModel, frozen=True):
        id: Path[str]

        @field_validator("id")
        @classmethod
        def validate_id(cls, value: str) -> str:
            return value if value == "me" else validate_id(value)


# ──── Response Payloads ───────────────────────────────────────────────────────────────


class Response:
    class User(BaseModel, frozen=True):
        id: str
        name: str
        picture: HttpUrl
        role: Role
        enabled: StrictBool
        createdAt: datetime
        updatedAt: datetime | None = None
        lastLoginAt: datetime | None = None

        @classmethod
        def pack(cls, user: User) -> Self:
            return cls(
                id=user.id,
                name=user.name,
                picture=user.picture,
                role=user.role,
                enabled=user.enabled,
                createdAt=user.created_at,
                updatedAt=user.updated_at,
                lastLoginAt=user.last_login_at,
            )

    class UserSummary(BaseModel, frozen=True):
        id: str
        name: str
        picture: HttpUrl

        @classmethod
        def pack(cls, user: UserSummary) -> Self:
            return cls(
                id=user.id,
                name=user.name,
                picture=user.picture,
            )

    class Page(BaseModel, frozen=True):
        users: list["Response.UserSummary"]
        cursor: str | None = None

        @classmethod
        def pack(cls, page: Page) -> Self:
            return cls(
                users=[Response.UserSummary.pack(user) for user in page.users],
                cursor=page.cursor,
            )

    class Credentials(BaseModel, frozen=True):
        id: str
        name: str
        password: str

        @classmethod
        def pack(cls, creds: Credentials) -> Self:
            return cls(
                id=creds.id,
                name=creds.name,
                password=creds.password,
            )

    class UploadForm(BaseModel, frozen=True):
        url: str
        fields: dict[str, str]

        @classmethod
        def pack(cls, upload: UploadForm) -> Self:
            return cls(
                url=upload.url,
                fields=upload.fields,
            )
