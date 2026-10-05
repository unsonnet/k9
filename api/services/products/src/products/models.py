from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from .images.provider import Image
from .listings.provider import Listing

__all__ = [
    "Material",
    "Format",
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
    Ceramic | Stone | Wood | Concrete | Vinyl | Laminate, Field(discriminator="type")
]


class Format(BaseModel, frozen=True):
    length: Decimal | None
    width: Decimal | None
    thickness: Decimal | None
    wear: Decimal | None


class Product(BaseModel, frozen=True):
    id: str
    brand: str | None
    material: Material
    format: Format
    subformats: set[Format]
    images: list[Image] = Field(default_factory=list, alias="$image")
    listings: list[Listing] = Field(default_factory=list, alias="$listing")
    meta: bytes | None
    created_at: datetime
    updated_at: datetime | None
