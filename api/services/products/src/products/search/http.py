from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field, HttpUrl, field_validator
from shared.config import missing
from shared.helpers import sanitize_query, validate_resource_id
from shared.resolvers.http.requests import Body, Query

from .models import Format, FormatFilter, Material, MaterialFilter

__all__ = [
    "Request",
    "Response",
]


# ──── Request Payloads ────────────────────────────────────────────────────────────────


class Request:
    class Search(BaseModel, frozen=True):
        q: Body[str | missing] = missing
        sku: Body[str | missing] = missing
        store: Body[list[str] | missing] = Field(missing, min_length=1)
        material: Body[list[MaterialFilter] | missing] = Field(missing, min_length=1)
        format: Body[list[FormatFilter] | missing] = Field(missing, min_length=1)
        reference: Body[str | missing] = missing
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

        @field_validator("store")
        @classmethod
        def validate_company_ids(cls, value: list[str]) -> list[str]:
            return [validate_resource_id(i) for i in value]

        @field_validator("reference")
        @classmethod
        def validate_reference(cls, value: str) -> str:
            return validate_resource_id(value)


# ──── Response Payloads ───────────────────────────────────────────────────────────────


class Response:
    class ImageIndex(BaseModel, frozen=True, from_attributes=True):
        id: str
        url: HttpUrl

    class ListingIndex(BaseModel, frozen=True, from_attributes=True):
        id: str
        vendor: str
        sku: str | None
        name: str

    class ProductIndex(BaseModel, frozen=True, from_attributes=True):
        id: str
        brand: str
        material: Material
        format: Format
        subformats: list[Format]
        images: list[Response.ImageIndex]
        listings: list[Response.ListingIndex]
        score: Decimal | None

    class Page(BaseModel, frozen=True, from_attributes=True):
        products: list[Response.ProductIndex] = Field(validation_alias="items")
        cursor: str | None
