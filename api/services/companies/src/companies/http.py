from __future__ import annotations

from pydantic import BaseModel, Field, HttpUrl, field_validator
from shared.config import missing
from shared.helpers import validate_resource_id
from shared.resolvers.http.requests import Body, Path

from .contacts.http import Response as contact
from .locations.http import Response as location
from .models import CompanyType, ImageFormat

__all__ = [
    "Request",
    "Response",
]


# ──── Request Payloads ────────────────────────────────────────────────────────────────


class Request:
    class Create(BaseModel, frozen=True):
        type: Body[CompanyType]
        name: Body[str] = Field(min_length=1)
        website: Body[HttpUrl | None]

    class Read(BaseModel, frozen=True):
        id: Path[str]

        @field_validator("id")
        @classmethod
        def validate_id(cls, value: str) -> str:
            return validate_resource_id(value)

    class Update(BaseModel, frozen=True):
        id: Path[str]
        type: Body[CompanyType | missing] = missing
        name: Body[str | missing] = Field(missing, min_length=1)
        logo: Body[None | missing] = missing
        website: Body[HttpUrl | None | missing] = missing

        @field_validator("id")
        @classmethod
        def validate_id(cls, value: str) -> str:
            return validate_resource_id(value)

    class Delete(BaseModel, frozen=True):
        id: Path[str]

        @field_validator("id")
        @classmethod
        def validate_id(cls, value: str) -> str:
            return validate_resource_id(value)

    class Logo(BaseModel, frozen=True):
        id: Path[str]
        format: Body[ImageFormat]
        length: Body[int] = Field(ge=1, le=5 * 1024 * 1024)

        @field_validator("id")
        @classmethod
        def validate_id(cls, value: str) -> str:
            return validate_resource_id(value)


# ──── Response Payloads ───────────────────────────────────────────────────────────────


class Response:
    class Company(BaseModel, frozen=True, from_attributes=True):
        id: str
        type: CompanyType
        name: str
        logo: HttpUrl
        website: HttpUrl | None
        locations: list[location.Location]
        contacts: list[contact.Contact]

    class UploadURL(BaseModel, frozen=True, from_attributes=True):
        url: HttpUrl
        headers: dict[str, str]
