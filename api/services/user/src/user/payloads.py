from datetime import datetime
from typing import Self

from pydantic import (
    Field,
    StrictBool,
    field_validator,
    model_validator,
)
from shared.abc import ApiModel, Role
from shared.http import Body, Path, Query
from shared.providers.cognito import normalize_name, validate_id, validate_name
from shared.providers.opensearch import sanitize_query

from .providers.report import Report as ProviderReport
from .providers.report import ReportPage as ProviderReportPage
from .providers.user import User as ProviderUser
from .providers.user import UserCreds as ProviderUserCreds
from .providers.user import UserPage as ProviderUserPage

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

    class ListReports(ApiModel, frozen=True):
        userId: Path[str]
        q: Query[str | None] = None
        final: Query[bool | None] = None
        dateFrom: Query[datetime | None] = None
        dateTo: Query[datetime | None] = None
        limit: Query[int | None] = Field(None, ge=1, le=100)
        cursor: Query[str | None] = None

        @field_validator("userId")
        @classmethod
        def validate_user_id(cls, value: str) -> str:
            return value if value == "me" else validate_id(value)

        @field_validator("q")
        @classmethod
        def sanitize_q(cls, value: str | None) -> str | None:
            return sanitize_query(value.strip()) if value else None

        @model_validator(mode="after")
        def verify_date_range(self) -> Self:
            match self.dateFrom, self.dateTo:
                case datetime() as start, datetime() as end if start > end:
                    raise ValueError("dateFrom must be before or equal to dateTo")
                case _:
                    return self


# ──── Response Payloads ───────────────────────────────────────────────────────────────


class Response:
    class User(ApiModel, frozen=True):
        id: str
        name: str
        role: Role
        enabled: StrictBool
        createdAt: datetime
        updatedAt: datetime | None = None
        lastLoginAt: datetime | None = None

        @classmethod
        def from_(cls, user: ProviderUser) -> Self:
            return cls(
                id=user.id,
                name=user.name,
                role=user.role,
                enabled=user.enabled,
                createdAt=user.created_at,
                updatedAt=user.updated_at,
                lastLoginAt=user.last_login_at,
            )

    class UserPage(ApiModel, frozen=True):
        users: list["Response.User"]
        cursor: str | None = None

        @classmethod
        def from_(cls, page: ProviderUserPage) -> Self:
            return cls(
                users=[Response.User.from_(user) for user in page.users],
                cursor=page.cursor,
            )

    class UserCreds(ApiModel, frozen=True):
        name: str
        password: str

        @classmethod
        def from_(cls, creds: ProviderUserCreds) -> Self:
            return cls(name=creds.name, password=creds.password)

    class Report(ApiModel, frozen=True):
        id: str
        user: str
        title: str
        final: StrictBool
        createdAt: datetime
        updatedAt: datetime | None = None

        @classmethod
        def from_(cls, report: ProviderReport) -> Self:
            return cls(
                id=report.id,
                user=report.user,
                title=report.title,
                final=report.final,
                createdAt=report.created_at,
                updatedAt=report.updated_at,
            )

    class ReportPage(ApiModel, frozen=True):
        reports: list["Response.Report"]
        cursor: str | None = None

        @classmethod
        def from_(cls, page: ProviderReportPage) -> "Response.ReportPage":
            return cls(
                reports=[Response.Report.from_(report) for report in page.reports],
                cursor=page.cursor,
            )
