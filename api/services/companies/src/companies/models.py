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
    model_validator,
)
from shared.http import Body, ImageMIMEType, Path, Query
from shared.providers.company import validate_id
from shared.providers.opensearch import sanitize_query

__all__ = [
    "GeoPoint",
    "Address",
    "Contact",
    "CompanySector",
    "Company",
    "CompanySummary",
    "Page",
    "UploadForm",
    "Request",
    "Response",
]


class GeoPoint(BaseModel, frozen=True):
    lat: Decimal = Field(ge=-90, le=90)
    lon: Decimal = Field(ge=-180, le=180)


class Address(BaseModel, frozen=True):
    street: str = Field(min_length=1)
    city: str = Field(min_length=1)
    state: str = Field(min_length=2, max_length=2)
    zip: str = Field(pattern=r"^\d{5}(-\d{4})?$")
    geo: GeoPoint | None = None


class Contact(BaseModel, frozen=True):
    name: str = Field(min_length=1)
    title: str | None
    email: EmailStr | None
    phone: str | None


class CompanySector(StrEnum):
    INSURANCE = "INSURANCE"
    MANUFACTURER = "MANUFACTURER"
    RETAILER = "RETAILER"


class Company(BaseModel, frozen=True):
    id: str
    sector: CompanySector
    name: str
    logo: HttpUrl
    website: HttpUrl
    locations: list[Address]
    contacts: list[Contact]
    created_at: datetime
    updated_at: datetime | None


class CompanySummary(BaseModel, frozen=True):
    id: str
    sector: CompanySector
    name: str
    logo: HttpUrl
    website: HttpUrl
    locations: list[Address]


class Page(BaseModel, frozen=True):
    companies: list[CompanySummary]
    cursor: str | None = None


class UploadForm(BaseModel, frozen=True):
    url: str
    fields: dict[str, str]


# ──── Request Payloads ────────────────────────────────────────────────────────────────


class Request:
    class List(BaseModel, frozen=True):
        q: Query[str | None] = None
        sector: Query[list[CompanySector] | None] = None
        lat: Query[float | None] = None
        lon: Query[float | None] = None
        radius: Query[int | None] = None
        limit: Query[int | None] = None
        cursor: Query[str | None] = None

        @field_validator("q")
        @classmethod
        def sanitize_q(cls, value: str | None) -> str | None:
            return sanitize_query(value) if value else None

        @field_validator("radius")
        @classmethod
        def clamp_radius(cls, value: int | None) -> int | None:
            return max(min(value, 500), 1) if value is not None else None

        @field_validator("limit")
        @classmethod
        def clamp_limit(cls, value: int | None) -> int | None:
            return max(min(value, 60), 1) if value is not None else None

        @model_validator(mode="after")
        def verify_has_geo(self) -> Self:
            match self.lat, self.lon, self.radius:
                case (None, None, None) | (float(), float(), int()):
                    return self
            raise ValueError(
                "Either all or none of latitude, longitude, and radius are required"
            )

    class Create(BaseModel, frozen=True):
        sector: Body[CompanySector]
        name: Body[str]
        website: Body[HttpUrl]
        locations: Body[list[Address]]
        contacts: Body[list[Contact]]

    class Read(BaseModel, frozen=True):
        id: Path[str]

        @field_validator("id")
        @classmethod
        def validate_id(cls, value: str) -> str:
            return validate_id(value)

    class Update(BaseModel, frozen=True):
        id: Path[str]
        sector: Body[CompanySector | None] = None
        name: Body[str | None] = None
        website: Body[HttpUrl | None] = None
        locations: Body[list[Address] | None] = None
        contacts: Body[list[Contact] | None] = None

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
        sector: CompanySector
        name: str
        logo: HttpUrl
        website: HttpUrl
        locations: list[Address]
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
        sector: CompanySector
        name: str
        logo: HttpUrl
        website: HttpUrl
        locations: list[Address]

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
