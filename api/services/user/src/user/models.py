from datetime import datetime
from typing import Any, Mapping, Self, Sequence

from pydantic import HttpUrl, StrictBool, field_validator
from shared.abc import ApiModel, DataModel, Role
from shared.errors import DomainInvariantViolation
from shared.helpers import dt
from shared.http import Body, ImageMIMEType, Path, Query
from shared.providers.opensearch import sanitize_query
from shared.providers.user import (
    decode_id,
    normalize_name,
    validate_id,
    validate_name,
)

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

        @field_validator("limit")
        @classmethod
        def clamp_limit(cls, value: int | None) -> int | None:
            return max(min(value, 60), 0) if value is not None else None

    class Create(ApiModel, frozen=True):
        name: Body[str]
        role: Body[Role]
        enabled: Body[StrictBool] = True

        @field_validator("name")
        @classmethod
        def validate_name(cls, value: str) -> str:
            return validate_name(normalize_name(value))

    class Read(ApiModel, frozen=True):
        id: Path[str]

        @field_validator("id")
        @classmethod
        def validate_id(cls, value: str) -> str:
            return value if value == "me" else validate_id(value)

    class Update(ApiModel, frozen=True):
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

    class Delete(ApiModel, frozen=True):
        id: Path[str]

        @field_validator("id")
        @classmethod
        def validate_id(cls, value: str) -> str:
            return validate_id(value)

    class Picture(ApiModel, frozen=True):
        id: Path[str]
        contentType: Body[ImageMIMEType]

        @field_validator("id")
        @classmethod
        def validate_id(cls, value: str) -> str:
            return value if value == "me" else validate_id(value)

    class Reset(ApiModel, frozen=True):
        id: Path[str]

        @field_validator("id")
        @classmethod
        def validate_id(cls, value: str) -> str:
            return value if value == "me" else validate_id(value)


# ──── Provider Models ─────────────────────────────────────────────────────────────────


class Provider:
    @staticmethod
    def _unpack(response: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
        attrs = {attr["Name"]: attr["Value"] for attr in response}
        attrs.setdefault("custom:last_login_at", None)
        return attrs

    class User(DataModel, frozen=True):
        id: str
        name: str
        picture: HttpUrl
        role: Role
        enabled: bool
        created_at: datetime
        updated_at: datetime | None = None
        last_login_at: datetime | None = None

        @classmethod
        def from_cognito(cls, response: Mapping[str, Any]) -> Self:
            response = dict(response)
            response.setdefault("UserLastModifiedDate", None)
            match response:
                case {
                    "Username": str(xid),
                    "Enabled": bool(enabled),
                    "UserCreateDate": datetime() as created_at,
                    "UserLastModifiedDate": datetime() | None as updated_at,
                    "UserAttributes": Sequence() as attrs,
                }:
                    match Provider._unpack(attrs):
                        case {
                            "name": str(name),
                            "picture": str(picture),
                            "custom:role": Role.USER | Role.ADMIN as role,
                            "custom:last_login_at": datetime() | None as last_login_at,
                        }:
                            return cls(
                                id=decode_id(xid),
                                name=name,
                                picture=HttpUrl(picture),
                                role=Role(role),
                                enabled=enabled,
                                created_at=dt(created_at),
                                updated_at=dt(updated_at),
                                last_login_at=dt(last_login_at),
                            )
            raise DomainInvariantViolation(f"Unexpected cognito profile: {response}")

    class UserSummary(DataModel, frozen=True):
        id: str
        name: str
        picture: HttpUrl

        @classmethod
        def from_cognito(cls, response: Mapping[str, Any]) -> Self:
            match dict(response):
                case {
                    "Username": str(xid),
                    "Attributes": Sequence() as attrs,
                }:
                    match Provider._unpack(attrs):
                        case {
                            "name": str(name),
                            "picture": str(picture),
                        }:
                            return cls(
                                id=decode_id(xid),
                                name=name,
                                picture=HttpUrl(picture),
                            )
            raise DomainInvariantViolation(f"Unexpected cognito profile: {response}")

    class Page(DataModel, frozen=True):
        users: list["Provider.UserSummary"]
        cursor: str | None = None

        @classmethod
        def from_cognito(cls, response: Mapping[str, Any]) -> Self:
            response = dict(response)
            response.setdefault("PaginationToken", None)
            match response:
                case {
                    "Users": list(users),
                    "PaginationToken": str() | None as cursor,
                }:
                    return cls(
                        users=[Provider.UserSummary.from_cognito(raw) for raw in users],
                        cursor=cursor,
                    )
            raise DomainInvariantViolation(f"Unexpected cognito page: {response}")

    class Credentials(DataModel, frozen=True):
        id: str
        name: str
        password: str

    class UploadForm(DataModel, frozen=True):
        url: str
        fields: dict[str, str]

        @classmethod
        def from_cognito(cls, response: Mapping[str, Any]) -> Self:
            match response:
                case {
                    "url": str(url),
                    "fields": dict(fields),
                }:
                    return cls(
                        url=url,
                        fields=fields,
                    )
            raise DomainInvariantViolation(f"Unexpected s3 upload form: {response}")


# ──── Response Payloads ───────────────────────────────────────────────────────────────


class Response:
    class User(ApiModel, frozen=True):
        id: str
        name: str
        picture: HttpUrl
        role: Role
        enabled: StrictBool
        createdAt: datetime
        updatedAt: datetime | None = None
        lastLoginAt: datetime | None = None

        @classmethod
        def from_provider(cls, user: Provider.User) -> Self:
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

    class UserSummary(ApiModel, frozen=True):
        id: str
        name: str
        picture: HttpUrl

        @classmethod
        def from_provider(cls, user: Provider.UserSummary) -> Self:
            return cls(
                id=user.id,
                name=user.name,
                picture=user.picture,
            )

    class Page(ApiModel, frozen=True):
        users: list["Response.UserSummary"]
        cursor: str | None = None

        @classmethod
        def from_provider(cls, page: Provider.Page) -> Self:
            return cls(
                users=[Response.UserSummary.from_provider(user) for user in page.users],
                cursor=page.cursor,
            )

    class Credentials(ApiModel, frozen=True):
        id: str
        name: str
        password: str

        @classmethod
        def from_provider(cls, creds: Provider.Credentials) -> Self:
            return cls(
                id=creds.id,
                name=creds.name,
                password=creds.password,
            )

    class UploadForm(ApiModel, frozen=True):
        url: str
        fields: dict[str, str]

        @classmethod
        def from_provider(cls, upload: Provider.UploadForm) -> Self:
            return cls(
                url=upload.url,
                fields=upload.fields,
            )
