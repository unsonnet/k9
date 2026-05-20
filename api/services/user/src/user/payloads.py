from datetime import datetime
from typing import Self

from pydantic import StrictBool, field_validator
from shared.abc import ApiModel, Role
from shared.http import Body, Path, Query
from shared.providers.cognito import normalize_name, validate_id, validate_name
from shared.providers.opensearch import sanitize_query

from .provider import Credentials as ProviderCredentials
from .provider import Page as ProviderPage
from .provider import Profile as ProviderProfile

__all__ = [
    "Request",
    "Response",
]


# ──── Request Payloads ────────────────────────────────────────────────────────────────


class Request:
    class List(ApiModel, frozen=True):
        q: Query[str | None] = None
        limit: Query[int | None] = None
        cursor: Query[str | None] = None

        @field_validator("q")
        @classmethod
        def sanitize_q(cls, value: str | None) -> str | None:
            return sanitize_query(normalize_name(value)) if value else None

    class Create(ApiModel, frozen=True):
        name: Body[str]
        role: Body[Role]
        enabled: Body[StrictBool] = True

        @field_validator("name")
        @classmethod
        def validate_name(cls, value: str) -> str:
            return validate_name(value)

    class Read(ApiModel, frozen=True):
        userId: Path[str]

        @field_validator("userId")
        @classmethod
        def validate_user_id(cls, value: str) -> str:
            return value if value == "me" else validate_id(value)

    class Update(ApiModel, frozen=True):
        userId: Path[str]
        name: Body[str | None] = None
        role: Body[Role | None] = None
        enabled: Body[StrictBool | None] = None

        @field_validator("userId")
        @classmethod
        def validate_user_id(cls, value: str) -> str:
            return value if value == "me" else validate_id(value)

        @field_validator("name")
        @classmethod
        def validate_name(cls, value: str | None) -> str | None:
            return validate_name(value) if value is not None else None

    class Delete(ApiModel, frozen=True):
        userId: Path[str]

        @field_validator("userId")
        @classmethod
        def validate_user_id(cls, value: str) -> str:
            return value if value == "me" else validate_id(value)

    class Reset(ApiModel, frozen=True):
        userId: Path[str]

        @field_validator("userId")
        @classmethod
        def validate_user_id(cls, value: str) -> str:
            return validate_id(value)


# ──── Response Payloads ───────────────────────────────────────────────────────────────


class Response:
    class Profile(ApiModel, frozen=True):
        id: str
        name: str
        role: Role
        enabled: StrictBool
        createdAt: datetime
        updatedAt: datetime | None = None
        lastLoginAt: datetime | None = None

        @classmethod
        def from_(cls, user: ProviderProfile) -> Self:
            return cls(
                id=user.id,
                name=user.name,
                role=user.role,
                enabled=user.enabled,
                createdAt=user.created_at,
                updatedAt=user.updated_at,
                lastLoginAt=user.last_login_at,
            )

    class Page(ApiModel, frozen=True):
        users: list["Response.Profile"]
        cursor: str | None = None

        @classmethod
        def from_(cls, page: ProviderPage) -> Self:
            return cls(
                users=[Response.Profile.from_(user) for user in page.users],
                cursor=page.cursor,
            )

    class Credentials(ApiModel, frozen=True):
        id: str
        name: str
        password: str

        @classmethod
        def from_(cls, creds: ProviderCredentials) -> Self:
            return cls(id=creds.id, name=creds.name, password=creds.password)
