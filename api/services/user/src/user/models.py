from datetime import datetime, timezone
from typing import Any, Mapping, Self, Sequence, overload

from pydantic import StrictBool, field_validator
from shared.abc import ApiModel, DataModel, Role
from shared.errors import DomainInvariantViolation
from shared.http import Body, ImageMIMEType, Path, Query
from shared.providers.cognito import (
    decode_id,
    normalize_name,
    validate_id,
    validate_name,
)
from shared.providers.opensearch import sanitize_query

__all__ = [
    "Request",
    "Response",
]


@overload
def dt(value: datetime) -> datetime: ...
@overload
def dt(value: None) -> None: ...
def dt(value: datetime | None) -> datetime | None:
    match value:
        case datetime() as dt:
            return dt.astimezone(timezone.utc)
        case None:
            return None


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
            return min(value, 60) if value is not None else None

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
    class Profile(DataModel, frozen=True):
        id: str
        name: str
        picture: str
        role: Role
        enabled: bool
        created_at: datetime
        updated_at: datetime | None = None
        last_login_at: datetime | None = None

        @classmethod
        def _unpack(cls, response: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
            attrs = {attr["Name"]: attr["Value"] for attr in response}
            attrs.setdefault("custom:last_login_at", None)
            return attrs

        @classmethod
        def from_cognito(cls, response: Mapping[str, Any]) -> Self:
            response = dict(response)
            response.setdefault("UserLastModifiedDate", None)
            response.setdefault("UserAttributes", response.get("Attributes", []))
            match response:
                case {
                    "Username": str(xid),
                    "Enabled": bool(enabled),
                    "UserCreateDate": datetime() as created_at,
                    "UserLastModifiedDate": datetime() | None as updated_at,
                    "UserAttributes": list() as attrs,
                }:
                    match cls._unpack(attrs):
                        case {
                            "name": str(name),
                            "picture": str(picture),
                            "custom:role": Role.USER | Role.ADMIN as role,
                            "custom:last_login_at": datetime() | None as last_login_at,
                        }:
                            return cls(
                                id=decode_id(xid),
                                name=name,
                                picture=picture,
                                role=role,
                                enabled=enabled,
                                created_at=dt(created_at),
                                updated_at=dt(updated_at),
                                last_login_at=dt(last_login_at),
                            )
            raise DomainInvariantViolation(f"Unexpected cognito profile: {response}")

    class Page(DataModel, frozen=True):
        users: list["Provider.Profile"]
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
                        users=[Provider.Profile.from_cognito(raw) for raw in users],
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
    class Profile(ApiModel, frozen=True):
        id: str
        name: str
        picture: str
        role: Role
        enabled: StrictBool
        createdAt: datetime
        updatedAt: datetime | None = None
        lastLoginAt: datetime | None = None

        @classmethod
        def from_provider(cls, user: Provider.Profile) -> Self:
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

    class Page(ApiModel, frozen=True):
        users: list["Response.Profile"]
        cursor: str | None = None

        @classmethod
        def from_provider(cls, page: Provider.Page) -> Self:
            return cls(
                users=[Response.Profile.from_provider(user) for user in page.users],
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
                fields=dict(upload.fields),
            )
