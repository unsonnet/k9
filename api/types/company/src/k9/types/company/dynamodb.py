from decimal import Decimal
from typing import TYPE_CHECKING, Literal, Self

from k9.types.base import Partial, ResourceModel
from k9.types.common import ResourceID, SubresourceID, missing
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


class Location(ResourceModel, frozen=True):
    id: SubresourceID
    scope: ResourceID | None
    address: Address
    geo: Coordinates

    # BEGIN GENERATED PARTIAL SIGNATURE
    if TYPE_CHECKING:

        @classmethod
        def partial(
            cls,
            *,
            id: SubresourceID | missing = ...,
            scope: ResourceID | None | missing = ...,
            address: Address | missing = ...,
            geo: Coordinates | missing = ...,
        ) -> Partial[Self]: ...
    # END GENERATED PARTIAL SIGNATURE


type Industry = Literal["insurance", "manufacturing", "retail"]


class Company(ResourceModel, frozen=True):
    id: ResourceID
    scope: ResourceID | None
    type: Industry
    name: str
    logo: HttpUrl
    website: HttpUrl | None
    locations: list[Location] = Field(default_factory=list, alias="$locations")

    # BEGIN GENERATED PARTIAL SIGNATURE
    if TYPE_CHECKING:

        @classmethod
        def partial(
            cls,
            *,
            id: ResourceID | missing = ...,
            scope: ResourceID | None | missing = ...,
            type: Industry | missing = ...,
            name: str | missing = ...,
            logo: HttpUrl | missing = ...,
            website: HttpUrl | None | missing = ...,
            locations: list[Location] | missing = ...,
        ) -> Partial[Self]: ...
    # END GENERATED PARTIAL SIGNATURE
