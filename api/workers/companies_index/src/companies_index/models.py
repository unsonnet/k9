from decimal import Decimal
from enum import StrEnum

from shared.dynamodb import EventModel, NewImage, OldImage

__all__ = [
    "Sync",
    "Remove",
]


class Sector(StrEnum):
    INSURANCE = "INSURANCE"
    MANUFACTURER = "MANUFACTURER"
    RETAILER = "RETAILER"


class Sync:
    class Company(EventModel, frozen=True):
        type: NewImage[str]
        id: NewImage[str]
        sector: NewImage[Sector]
        name: NewImage[str]
        logo: NewImage[str | None]
        website: NewImage[str | None]

    class Contact(EventModel, frozen=True):
        type: NewImage[str]
        id: NewImage[str]
        name: NewImage[str]
        title: NewImage[str | None]
        picture: NewImage[str | None]
        email: NewImage[str | None]
        phone: NewImage[str | None]

    class Location(EventModel, frozen=True):
        type: NewImage[str]
        id: NewImage[str]
        street: NewImage[str]
        city: NewImage[str]
        state: NewImage[str]
        zip: NewImage[str]
        lat: NewImage[Decimal]
        lon: NewImage[Decimal]


class Remove:
    class Item(EventModel, frozen=True):
        type: OldImage[str]
        id: OldImage[str]
