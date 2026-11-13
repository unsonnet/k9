from decimal import Decimal
from typing import Literal

from k9.types.common import ResourceID, SubresourceID
from pydantic import BaseModel, Field, HttpUrl

__all__ = [
    "Address",
    "Company",
    "Coordinates",
    "Industry",
    "Location",
]


class Address(BaseModel, frozen=True):
    street: str
    city: str
    state: str
    zip: str


class Coordinates(BaseModel, frozen=True):
    lat: Decimal
    lng: Decimal


class Location(BaseModel, frozen=True):
    id: SubresourceID
    scope: ResourceID | None
    address: Address
    geo: Coordinates


type Industry = Literal["insurance", "manufacturing", "retail"]


class Company(BaseModel, frozen=True):
    id: ResourceID
    scope: ResourceID | None
    type: Industry
    name: str
    logo: HttpUrl
    website: HttpUrl | None
    locations: list[Location] = Field(default_factory=list, alias="$locations")
