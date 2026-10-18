from pydantic import BaseModel
from shared.resolvers.dynamodb import EventModel, NewImage, OldImage

__all__ = [
    "Index",
    "Drop",
]


class Format(BaseModel, frozen=True):
    length: float | None
    width: float | None
    thickness: float | None
    wear: float | None


class Index:
    class Product(EventModel, frozen=True):
        type: NewImage[str]
        id: NewImage[str]
        brand: NewImage[str]
        material: NewImage[dict[str, str | None]]
        format: NewImage[Format]
        subformats: NewImage[list[Format]]

    class Image(EventModel, frozen=True):
        type: NewImage[str]
        id: NewImage[str]
        url: NewImage[str]

    class Listing(EventModel, frozen=True):
        type: NewImage[str]
        id: NewImage[str]
        vendor: NewImage[str]
        sku: NewImage[str | None]
        name: NewImage[str]


class Drop:
    class Item(EventModel, frozen=True):
        type: OldImage[str]
        id: OldImage[str]
