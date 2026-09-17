from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field, HttpUrl, field_validator
from shared.config import missing
from shared.helpers import sanitize_query, validate_resource_id
from shared.http.requests import Body, Path, Query

from .contacts.models import Response as contact
from .locations.models import Response as location
from .provider import Sector

__all__ = [
    "Request",
    "Response",
]


# ──── Request Payloads ────────────────────────────────────────────────────────────────


class Request:
    class Search(BaseModel, frozen=True):
        sector: Query[list[Sector] | missing] = missing
        name: Query[str | missing] = missing
        lat: Query[Decimal | missing] = Field(missing, ge=-90, le=90)
        lon: Query[Decimal | missing] = Field(missing, ge=-180, le=180)
        radius: Query[int | missing] = Field(missing, ge=1, le=500)
        limit: Query[int] = Field(25, ge=1, le=60)
        cursor: Query[str | missing] = missing

        @property
        def geo(self) -> tuple[Decimal, Decimal, int] | missing:
            match self.lat, self.lon, self.radius:
                case (Decimal(), Decimal(), int()):
                    return (self.lat, self.lon, self.radius)
            return missing

        @field_validator("name")
        @classmethod
        def sanitize_name(cls, value: str) -> str | missing:
            return q if (q := sanitize_query(value)) else missing

    class Create(BaseModel, frozen=True):
        sector: Body[Sector]
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
        sector: Body[Sector | missing] = missing
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

        @field_validator("id")
        @classmethod
        def validate_id(cls, value: str) -> str:
            return validate_resource_id(value)


# ──── Response Payloads ───────────────────────────────────────────────────────────────


class Response:
    class Company(BaseModel, frozen=True, from_attributes=True):
        id: str
        sector: Sector
        name: str
        logo: HttpUrl
        website: HttpUrl | None
        locations: list[location.Location]
        contacts: list[contact.Contact]

    class CompanyIndex(BaseModel, frozen=True, from_attributes=True):
        id: str
        sector: Sector
        name: str
        logo: HttpUrl
        website: HttpUrl | None
        locations: list[location.LocationIndex]

    class Page(BaseModel, frozen=True, from_attributes=True):
        companies: list[Response.CompanyIndex] = Field(validation_alias="items")
        cursor: str | None

    class UploadURL(BaseModel, frozen=True, from_attributes=True):
        url: HttpUrl
        fields: dict[str, str]
