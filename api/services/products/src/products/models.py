from decimal import Decimal

from pydantic import BaseModel, Field

from .images.provider import Image
from .listings.provider import Listing
from .materials import Material

__all__ = [
    "Material",
    "Format",
    "Product",
]


class Format(BaseModel, frozen=True):
    length: Decimal | None
    width: Decimal | None
    thickness: Decimal | None
    wear: Decimal | None


class Product(BaseModel, frozen=True):
    id: str
    brand: str
    material: Material
    format: Format
    subformats: list[Format]
    images: list[Image] = Field(default_factory=list, alias="$images")
    listings: list[Listing] = Field(default_factory=list, alias="$listings")
    meta: bytes | None
