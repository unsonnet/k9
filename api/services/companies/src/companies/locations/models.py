from decimal import Decimal

from pydantic import BaseModel, Field, field_validator
from shared.helpers import validate_resource_id, validate_subresource_id
from shared.http import Body, Path

from .provider import Location

__all__ = [
    "Request",
    "Response",
]


# ──── Request Payloads ────────────────────────────────────────────────────────────────


class Request:
    class Create(BaseModel, frozen=True):
        id: Path[str]
        street: Body[str] = Field(min_length=1)
        city: Body[str] = Field(min_length=1)
        state: Body[str] = Field(min_length=2, max_length=2)
        zip: Body[str] = Field(pattern=r"^\d{5}(-\d{4})?$")

        @field_validator("id")
        @classmethod
        def validate_id(cls, value: str) -> str:
            return validate_resource_id(value)

    class Read(BaseModel, frozen=True):
        id: Path[str]
        sid: Path[str]

        @field_validator("id")
        @classmethod
        def validate_id(cls, value: str) -> str:
            return validate_resource_id(value)

        @field_validator("sid")
        @classmethod
        def validate_sub_id(cls, value: str) -> str:
            return validate_subresource_id(value)

    class Delete(BaseModel, frozen=True):
        id: Path[str]
        sid: Path[str]

        @field_validator("id")
        @classmethod
        def validate_id(cls, value: str) -> str:
            return validate_resource_id(value)

        @field_validator("sid")
        @classmethod
        def validate_sub_id(cls, value: str) -> str:
            return validate_subresource_id(value)


# ──── Response Payloads ───────────────────────────────────────────────────────────────


class Response:
    class Location(BaseModel, frozen=True):
        id: str
        street: str
        city: str
        state: str
        zip: str
        lat: Decimal
        lon: Decimal

        @classmethod
        def pack(cls, location: Location):
            return cls(
                id=location.id,
                street=location.street,
                city=location.city,
                state=location.state,
                zip=location.zip,
                lat=location.lat,
                lon=location.lon,
            )
