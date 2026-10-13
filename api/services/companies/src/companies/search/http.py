from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field, HttpUrl, field_validator
from shared.config import missing
from shared.helpers import sanitize_query
from shared.resolvers.http.requests import Query

from .models import Sector

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


# ──── Response Payloads ───────────────────────────────────────────────────────────────


class Response:
    class LocationIndex(BaseModel, frozen=True, from_attributes=True):
        id: str
        street: str
        city: str
        state: str
        zip: str
        lat: Decimal
        lon: Decimal

    class CompanyIndex(BaseModel, frozen=True, from_attributes=True):
        id: str
        sector: Sector
        name: str
        logo: HttpUrl
        website: HttpUrl | None
        locations: list[Response.LocationIndex]

    class Page(BaseModel, frozen=True, from_attributes=True):
        companies: list[Response.CompanyIndex] = Field(validation_alias="items")
        cursor: str | None
