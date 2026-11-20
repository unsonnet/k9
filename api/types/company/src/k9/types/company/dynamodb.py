from decimal import Decimal
from typing import TYPE_CHECKING, Literal, Self

from k9.types.base import Partial, ResourceModel
from k9.types.common import ResourceID, S3Url, SubresourceID, missing
from pydantic import BaseModel, HttpUrl

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
    logo: S3Url
    website: HttpUrl | None

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
            logo: S3Url | missing = ...,
            website: HttpUrl | None | missing = ...,
        ) -> Partial[Self]: ...
    # END GENERATED PARTIAL SIGNATURE
