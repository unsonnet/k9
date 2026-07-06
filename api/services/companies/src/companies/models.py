from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Self

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    HttpUrl,
    field_validator,
)
from shared.config import missing
from shared.http import Body, ImageMIMEType, Path, Query
from shared.providers.company import validate_id
from shared.providers.opensearch import sanitize_query

__all__ = [
    "Contact",
    "GeoPoint",
    "Location",
    "Sector",
    "Company",
    "CompanySummary",
    "Page",
    "UploadForm",
    "Request",
    "Response",
]


class GeoPoint(BaseModel, frozen=True):
    lat: Decimal
    lon: Decimal


class Location(BaseModel, frozen=True):
    id: str
    street: str
    city: str
    state: str
    zip: str
    geo: GeoPoint


class Contact(BaseModel, frozen=True):
    id: str
    name: str
    title: str | None
    email: EmailStr | None
    phone: str | None


class Sector(StrEnum):
    INSURANCE = "INSURANCE"
    MANUFACTURER = "MANUFACTURER"
    RETAILER = "RETAILER"


class Company(BaseModel, frozen=True):
    id: str
    sector: Sector
    name: str
    logo: HttpUrl | None
    website: HttpUrl | None
    locations: list[Location]
    contacts: list[Contact]
    created_at: datetime
    updated_at: datetime | None


class CompanySummary(BaseModel, frozen=True):
    id: str
    sector: Sector
    name: str
    logo: HttpUrl | None
    website: HttpUrl | None
    locations: list[Location]


class Page(BaseModel, frozen=True):
    companies: list[CompanySummary]
    cursor: str | None


class UploadForm(BaseModel, frozen=True):
    url: str
    fields: dict[str, str]


# ──── Request Payloads ────────────────────────────────────────────────────────────────


class Request:
    class List(BaseModel, frozen=True):
        sector: Query[list[Sector] | missing] = missing
        name: Query[str | missing] = missing
        lat: Query[float | missing] = Field(missing, ge=-90, le=90)
        lon: Query[float | missing] = Field(missing, ge=-180, le=180)
        radius: Query[int | missing] = Field(missing, ge=1, le=500)
        limit: Query[int] = Field(25, ge=1, le=60)
        cursor: Query[str | missing] = missing

        @property
        def geo(self) -> tuple[float, float, int] | missing:
            match self.lat, self.lon, self.radius:
                case (float(), float(), int()):
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
            return validate_id(value)

    class Update(BaseModel, frozen=True):
        id: Path[str]
        sector: Body[Sector | missing] = missing
        name: Body[str | missing] = Field(missing, min_length=1)
        website: Body[HttpUrl | None | missing] = missing

        @field_validator("id")
        @classmethod
        def validate_id(cls, value: str) -> str:
            return validate_id(value)

    class Delete(BaseModel, frozen=True):
        id: Path[str]

        @field_validator("id")
        @classmethod
        def validate_id(cls, value: str) -> str:
            return validate_id(value)

    class Logo(BaseModel, frozen=True):
        id: Path[str]
        contentType: Body[ImageMIMEType]

        @field_validator("id")
        @classmethod
        def validate_id(cls, value: str) -> str:
            return validate_id(value)


# ──── Response Payloads ───────────────────────────────────────────────────────────────


class Response:
    class Company(BaseModel, frozen=True):
        id: str
        sector: Sector
        name: str
        logo: HttpUrl | None
        website: HttpUrl | None
        locations: list[Location]
        contacts: list[Contact]
        createdAt: datetime
        updatedAt: datetime | None

        @classmethod
        def pack(cls, company: Company):
            return cls(
                id=company.id,
                sector=company.sector,
                name=company.name,
                logo=company.logo,
                website=company.website,
                locations=company.locations,
                contacts=company.contacts,
                createdAt=company.created_at,
                updatedAt=company.updated_at,
            )

    class CompanySummary(BaseModel, frozen=True):
        id: str
        sector: Sector
        name: str
        logo: HttpUrl | None
        website: HttpUrl | None
        locations: list[Location]

        @classmethod
        def pack(cls, company: CompanySummary):
            return cls(
                id=company.id,
                sector=company.sector,
                name=company.name,
                logo=company.logo,
                website=company.website,
                locations=company.locations,
            )

    class Page(BaseModel, frozen=True):
        companies: list["Response.CompanySummary"]
        cursor: str | None

        @classmethod
        def pack(cls, page: Page):
            return cls(
                companies=[
                    Response.CompanySummary.pack(company) for company in page.companies
                ],
                cursor=page.cursor,
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
