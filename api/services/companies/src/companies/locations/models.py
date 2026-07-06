from decimal import Decimal

from pydantic import BaseModel, Field, field_validator
from shared.config import missing
from shared.http import Body, Path, Query
from shared.providers.company import validate_id, validate_sub_id

__all__ = [
    "GeoPoint",
    "Location",
    "Page",
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


class Page(BaseModel, frozen=True):
    locations: list[Location]
    cursor: str | None


# ──── Request Payloads ────────────────────────────────────────────────────────────────


class Request:
    class List(BaseModel, frozen=True):
        id: Path[str]
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

        @field_validator("id")
        @classmethod
        def validate_id(cls, value: str) -> str:
            return validate_id(value)

    class Create(BaseModel, frozen=True):
        id: Path[str]
        street: Body[str] = Field(min_length=1)
        city: Body[str] = Field(min_length=1)
        state: Body[str] = Field(min_length=2, max_length=2)
        zip: Body[str] = Field(pattern=r"^\d{5}(-\d{4})?$")

        @field_validator("id")
        @classmethod
        def validate_id(cls, value: str) -> str:
            return validate_id(value)

    class Read(BaseModel, frozen=True):
        id: Path[str]
        sid: Path[str]

        @field_validator("id")
        @classmethod
        def validate_id(cls, value: str) -> str:
            return validate_id(value)

        @field_validator("sid")
        @classmethod
        def validate_sub_id(cls, value: str) -> str:
            return validate_sub_id(value)

    class Update(BaseModel, frozen=True):
        id: Path[str]
        sid: Path[str]
        street: Body[str | missing] = Field(missing, min_length=1)
        city: Body[str | missing] = Field(missing, min_length=1)
        state: Body[str | missing] = Field(missing, min_length=2, max_length=2)
        zip: Body[str | missing] = Field(missing, pattern=r"^\d{5}(-\d{4})?$")

        @field_validator("id")
        @classmethod
        def validate_id(cls, value: str) -> str:
            return validate_id(value)

        @field_validator("sid")
        @classmethod
        def validate_sub_id(cls, value: str) -> str:
            return validate_sub_id(value)

    class Delete(BaseModel, frozen=True):
        id: Path[str]
        sid: Path[str]

        @field_validator("id")
        @classmethod
        def validate_id(cls, value: str) -> str:
            return validate_id(value)

        @field_validator("sid")
        @classmethod
        def validate_sub_id(cls, value: str) -> str:
            return validate_sub_id(value)


# ──── Response Payloads ───────────────────────────────────────────────────────────────


class Response:
    class Location(BaseModel, frozen=True):
        id: str
        street: str
        city: str
        state: str
        zip: str
        geo: GeoPoint

        @classmethod
        def pack(cls, company: Location):
            return cls(
                id=company.id,
                street=company.street,
                city=company.city,
                state=company.state,
                zip=company.zip,
                geo=company.geo,
            )

    class Page(BaseModel, frozen=True):
        locations: list["Response.Location"]
        cursor: str | None

        @classmethod
        def pack(cls, page: Page):
            return cls(
                locations=[
                    Response.Location.pack(location) for location in page.locations
                ],
                cursor=page.cursor,
            )
