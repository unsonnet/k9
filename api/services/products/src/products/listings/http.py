from pydantic import BaseModel, Field, HttpUrl, field_validator
from shared.config import missing
from shared.helpers import validate_resource_id, validate_subresource_id
from shared.http.requests import Body, Path

from .models import Price

__all__ = [
    "Request",
    "Response",
]


# ──── Request Payloads ────────────────────────────────────────────────────────────────


class Request:
    class Create(BaseModel, frozen=True):
        id: Path[str]
        vendor: Body[str]
        sku: Body[str | None]
        name: Body[str] = Field(min_length=1)
        prices: Body[list[Price]]
        url: Body[HttpUrl | None]

        @field_validator("id", "vendor")
        @classmethod
        def validate_ids(cls, value: str) -> str:
            return validate_resource_id(value)

    class Update(BaseModel, frozen=True):
        id: Path[str]
        sid: Path[str]
        vendor: Body[str | missing] = missing
        sku: Body[str | None | missing] = missing
        name: Body[str | missing] = Field(missing, min_length=1)
        prices: Body[list[Price] | missing] = missing
        url: Body[HttpUrl | None | missing] = missing

        @field_validator("id", "vendor")
        @classmethod
        def validate_ids(cls, value: str) -> str:
            return validate_resource_id(value)

        @field_validator("sid")
        @classmethod
        def validate_sub_id(cls, value: str) -> str:
            return validate_subresource_id(value)

    class Delete(BaseModel, frozen=True):
        id: Path[str]
        sid: Path[str]

        @field_validator("id")
        @classmethod
        def validate_id(cls, value: str) -> str:
            return validate_resource_id(value)

        @field_validator("sid")
        @classmethod
        def validate_sub_id(cls, value: str) -> str:
            return validate_subresource_id(value)


# ──── Response Payloads ───────────────────────────────────────────────────────────────


class Response:
    class Listing(BaseModel, frozen=True, from_attributes=True):
        id: str
        vendor: str
        sku: str | None
        name: str
        prices: list[Price]
        url: HttpUrl | None
