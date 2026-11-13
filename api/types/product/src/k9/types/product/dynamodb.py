from decimal import Decimal
from typing import Annotated, Literal

from k9.types.common import DateID, ResourceID, SubresourceID
from pydantic import BaseModel, Field, HttpUrl

__all__ = [
    "Format",
    "Image",
    "Listing",
    "Material",
    "Price",
    "Product",
]


class Ceramic(BaseModel, frozen=True):
    type: Literal["ceramic"]
    subtype: Literal["ceramic", "porcelain"] | None
    look: None
    edge: Literal["straight", "beveled", "chiseled"] | None
    finish: Literal["matte", "semi-gloss", "glossy"] | None
    texture: None


class Stone(BaseModel, frozen=True):
    type: Literal["stone"]
    subtype: None
    look: None
    edge: Literal["straight", "beveled", "chiseled"] | None
    finish: Literal["honed", "polished", "crystalized"] | None
    texture: None


class Wood(BaseModel, frozen=True):
    type: Literal["wood"]
    subtype: Literal["solid", "engineered"] | None
    look: None
    edge: Literal["straight", "beveled"] | None
    finish: Literal["satin", "semi-gloss", "glossy"] | None
    texture: None


class Concrete(BaseModel, frozen=True):
    type: Literal["concrete"]
    subtype: None
    look: None
    edge: None
    finish: None
    texture: None


class Vinyl(BaseModel, frozen=True):
    type: Literal["vinyl"]
    subtype: Literal["plank", "tile"] | None
    look: None
    edge: None
    finish: Literal["matte", "semi-gloss", "glossy"] | None
    texture: None


class Laminate(BaseModel, frozen=True):
    type: Literal["laminate"]
    subtype: Literal["high-pressure", "low-pressure"] | None
    look: None
    edge: Literal["straight", "beveled"] | None
    finish: Literal["matte", "semi-gloss", "glossy"] | None
    texture: None


type Material = Annotated[
    Ceramic | Stone | Wood | Concrete | Vinyl | Laminate,
    Field(discriminator="type"),
]


class Format(BaseModel, frozen=True):
    length: Decimal | None
    width: Decimal | None
    thickness: Decimal | None
    wear: Decimal | None


class Image(BaseModel, frozen=True):
    type Vector = Annotated[list[Decimal], Field(min_length=3, max_length=3)]
    type Homomorphism = Annotated[list[Vector], Field(min_length=3, max_length=3)]

    id: SubresourceID
    scope: ResourceID | None
    url: HttpUrl
    hom: Homomorphism


class Price(BaseModel, frozen=True):
    id: DateID
    scope: ResourceID | None
    currency: str | None
    rate: Decimal | None
    unit: Decimal | None
    stock: Decimal | None


class Listing(BaseModel, frozen=True):
    id: SubresourceID
    scope: ResourceID | None
    vendor: ResourceID
    sku: str | None
    name: str
    website: HttpUrl | None


class Product(BaseModel, frozen=True):
    id: ResourceID
    scope: ResourceID | None
    brand: ResourceID | None
    material: Material
    format: Format
    subformats: list[Format]
    meta: bytes | None
