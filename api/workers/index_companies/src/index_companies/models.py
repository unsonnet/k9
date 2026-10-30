from decimal import Decimal
from enum import StrEnum
from typing import TypedDict

from shared.resolvers.dynamodb import EventModel, NewImage, OldImage

__all__ = [
    "Index",
    "Drop",
]


class CompanyType(StrEnum):
    INSURANCE = "insurance"
    MANUFACTURER = "manufacturer"
    RETAILER = "retailer"


class DynamoDBKey(TypedDict):
    key: str
    id: str
    type: str


class Index:
    class Company(EventModel, frozen=True):
        key: NewImage[DynamoDBKey]
        id: NewImage[str]
        type: NewImage[CompanyType]
        name: NewImage[str]
        logo: NewImage[str]
        website: NewImage[str | None]

    class Contact(EventModel, frozen=True):
        key: NewImage[DynamoDBKey]
        id: NewImage[str]
        name: NewImage[str]
        title: NewImage[str | None]
        picture: NewImage[str]
        email: NewImage[str | None]
        phone: NewImage[str | None]

    class Location(EventModel, frozen=True):
        key: NewImage[DynamoDBKey]
        id: NewImage[str]
        street: NewImage[str]
        city: NewImage[str]
        state: NewImage[str]
        zip: NewImage[str]
        lat: NewImage[Decimal]
        lon: NewImage[Decimal]


class Drop:
    class Item(EventModel, frozen=True):
        key: OldImage[DynamoDBKey]
