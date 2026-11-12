from decimal import Decimal
from typing import Literal

from k9.shared.types import ResourceID, SubresourceID
from pydantic import BaseModel, HttpUrl

type Industry = Literal["insurance", "manufacturer", "retailer"]


class Company(BaseModel, frozen=True):
    id: ResourceID
    scope: ResourceID | None
    type: Industry
    name: str
    logo: HttpUrl
    website: HttpUrl | None


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
