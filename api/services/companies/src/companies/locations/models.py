from datetime import datetime
from decimal import Decimal

from pydantic import AliasPath, BaseModel, Field

__all__ = [
    "Location",
    "LocationIndex",
]


class Location(BaseModel, frozen=True):
    id: str
    street: str
    city: str
    state: str
    zip: str
    lat: Decimal
    lon: Decimal
    created_at: datetime
    updated_at: datetime | None


class LocationIndex(BaseModel, frozen=True):
    id: str
    street: str
    city: str
    state: str
    zip: str
    lat: Decimal = Field(validation_alias=AliasPath("geo", "lat"))
    lon: Decimal = Field(validation_alias=AliasPath("geo", "lon"))
