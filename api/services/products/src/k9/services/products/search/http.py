from __future__ import annotations

from decimal import Decimal

from k9.resolvers.http.requests import Body, Query
from k9.shared.config import missing
from k9.shared.helpers import sanitize_query
from pydantic import BaseModel, Field, field_validator

from .provider import (
    Format,
    FormatFilter,
    HttpUrl,
    Material,
    MaterialFilter,
    ResourceID,
    SubresourceID,
)

__all__ = [
    "Request",
    "Response",
]


# ──── Request Payloads ────────────────────────────────────────────────────────────────


class Request:
    class Search(BaseModel, frozen=True):
        q: Body[str | missing] = missing
        sku: Body[str | missing] = missing
        store: Body[list[ResourceID] | missing] = Field(missing, min_length=1)
        material: Body[list[MaterialFilter] | missing] = Field(missing, min_length=1)
        format: Body[list[FormatFilter] | missing] = Field(missing, min_length=1)
        reference: Body[ResourceID | missing] = missing
        limit: Query[int] = Field(24, ge=1, le=100)
        cursor: Query[str | missing] = missing

        @field_validator("q")
        @classmethod
        def sanitize_q(cls, value: str) -> str | missing:
            return q if (q := sanitize_query(value)) else missing

        @field_validator("sku")
        @classmethod
        def sanitize_sku(cls, value: str) -> str | missing:
            return s if (s := value.strip()) else missing


# ──── Response Payloads ───────────────────────────────────────────────────────────────


class Response:
    class ImageIndex(BaseModel, frozen=True, from_attributes=True):
        id: SubresourceID
        scope: ResourceID | None
        url: HttpUrl

    class ListingIndex(BaseModel, frozen=True, from_attributes=True):
        id: SubresourceID
        scope: ResourceID | None
        vendor: ResourceID
        sku: str | None
        name: str

    class ProductIndex(BaseModel, frozen=True, from_attributes=True):
        id: ResourceID
        scope: ResourceID | None
        brand: ResourceID | None
        material: Material
        format: Format
        subformats: list[Format]
        images: list[Response.ImageIndex]
        listings: list[Response.ListingIndex]
        score: Decimal | None

    class Page(BaseModel, frozen=True, from_attributes=True):
        products: list[Response.ProductIndex] = Field(validation_alias="items")
        cursor: str | None
