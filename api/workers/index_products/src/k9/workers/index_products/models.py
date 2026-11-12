from decimal import Decimal
from typing import Annotated

from k9.shared.types import DateID, ResourceID, SubresourceID
from pydantic import BaseModel, Field, HttpUrl


class Material(BaseModel, frozen=True):
    type: str
    subtype: str | None
    look: str | None
    edge: str | None
    finish: str | None
    texture: str | None


class Format(BaseModel, frozen=True):
    length: Decimal | None
    width: Decimal | None
    thickness: Decimal | None
    wear: Decimal | None


class Product(BaseModel, frozen=True):
    id: ResourceID
    scope: ResourceID | None
    brand: ResourceID | None
    material: Material
    format: Format
    subformats: list[Format]
    meta: bytes | None


class Image(BaseModel, frozen=True):
    type Vector = Annotated[list[Decimal], Field(min_length=3, max_length=3)]
    type Homomorphism = Annotated[list[Vector], Field(min_length=3, max_length=3)]

    id: SubresourceID
    scope: ResourceID | None
    url: HttpUrl
    hom: Homomorphism


class Listing(BaseModel, frozen=True):
    id: SubresourceID
    scope: ResourceID | None
    vendor: ResourceID
    sku: str | None
    name: str
    website: HttpUrl | None


class Price(BaseModel, frozen=True):
    id: DateID
    scope: ResourceID | None
    currency: str | None
    rate: Decimal | None
    unit: Decimal | None
    stock: Decimal | None
