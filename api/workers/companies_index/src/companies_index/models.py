from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field, HttpUrl
from shared.stream import Keys, NewImage

__all__ = [
    "GeoPoint",
    "Address",
    "CompanySector",
    "CompanySummary",
    "Request",
]


class GeoPoint(BaseModel, frozen=True):
    lat: Decimal = Field(ge=-90, le=90)
    lon: Decimal = Field(ge=-180, le=180)


class Address(BaseModel, frozen=True):
    street: str = Field(min_length=1)
    city: str = Field(min_length=1)
    state: str = Field(min_length=2, max_length=2)
    zip: str = Field(pattern=r"^\d{5}(-\d{4})?$")
    geo: GeoPoint


class CompanySector(StrEnum):
    INSURANCE = "INSURANCE"
    MANUFACTURER = "MANUFACTURER"
    RETAILER = "RETAILER"


class CompanySummary(BaseModel, frozen=True):
    id: str
    sector: CompanySector
    name: str = Field(min_length=1)
    logo: HttpUrl
    website: HttpUrl
    locations: list[Address]


# ──── Request Payloads ────────────────────────────────────────────────────────────────


class Request:
    class Upsert(BaseModel, frozen=True):
        company: NewImage[CompanySummary]

    class Remove(BaseModel, frozen=True):
        id: Keys[str]
