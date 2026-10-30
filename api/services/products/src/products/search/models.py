from decimal import Decimal
from typing import Iterator, Self

from pydantic import BaseModel, Field, HttpUrl, model_validator
from shared.providers.search import Page

from ..models import Format, Material, Product

__all__ = [
    "FormatFilter",
    "Format",
    "ImageIndex",
    "ListingIndex",
    "MaterialFilter",
    "Material",
    "Page",
    "ProductIndex",
    "Product",
    "Range",
]


# ──── Search Filters ──────────────────────────────────────────────────────────────────


class MaterialFilter(BaseModel, frozen=True):
    type: str | None = None
    subtype: str | None = None
    look: str | None = None
    edge: str | None = None
    finish: str | None = None
    texture: str | None = None

    def terms(self) -> Iterator[tuple[str, str]]:
        return ((k, v) for k, v in self if v is not None)


class Range(BaseModel, frozen=True):
    gte: Decimal | None = None
    lte: Decimal | None = None
    include_missing: bool = False

    @model_validator(mode="after")
    def validate_bounds(self) -> Self:
        if self.gte is not None and self.lte is not None and self.gte > self.lte:
            raise ValueError("gte must not exceed lte")
        return self


class FormatFilter(BaseModel, frozen=True):
    length: Range | None = None
    width: Range | None = None
    thickness: Range | None = None
    wear: Range | None = None

    def ranges(self) -> Iterator[tuple[str, Range]]:
        return ((k, v) for k, v in self if v is not None)


# ──── Search Results ──────────────────────────────────────────────────────────────────


class ImageIndex(BaseModel, frozen=True):
    id: str
    url: HttpUrl


class ListingIndex(BaseModel, frozen=True):
    id: str
    vendor: str
    sku: str | None
    name: str


class ProductIndex(BaseModel, frozen=True):
    id: str
    brand: str
    material: Material
    format: Format
    subformats: list[Format] = Field(alias="$subformat")
    images: list[ImageIndex] = Field(default_factory=list, alias="$images")
    listings: list[ListingIndex] = Field(default_factory=list, alias="$listings")
    score: float | None = Field(None, alias="$score")
