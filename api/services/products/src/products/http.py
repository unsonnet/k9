from pydantic import BaseModel, field_validator
from shared.config import missing
from shared.helpers import validate_resource_id
from shared.http.requests import Body, Path

from .images.http import Response as image
from .listings.http import Response as listing
from .models import Format, Material

__all__ = [
    "Request",
    "Response",
]


# ──── Request Payloads ────────────────────────────────────────────────────────────────


class Request:
    class Create(BaseModel, frozen=True):
        brand: Body[str | None]
        material: Body[Material]
        format: Body[Format]
        subformats: Body[set[Format]]
        meta: Body[bytes | None]

        @field_validator("brand")
        @classmethod
        def validate_id(cls, value: str | None) -> str | None:
            return validate_resource_id(value) if value else None

    class Read(BaseModel, frozen=True):
        id: Path[str]

        @field_validator("id")
        @classmethod
        def validate_id(cls, value: str) -> str:
            return validate_resource_id(value)

    class Update(BaseModel, frozen=True):
        id: Path[str]
        brand: Body[str | None | missing] = missing
        material: Body[Material | missing] = missing
        format: Body[Format | missing] = missing
        subformats: Body[set[Format] | missing] = missing
        meta: Body[bytes | None | missing] = missing

        @field_validator("id", "brand")
        @classmethod
        def validate_ids(cls, value: str | None) -> str | None:
            return validate_resource_id(value) if value else None

    class Delete(BaseModel, frozen=True):
        id: Path[str]

        @field_validator("id")
        @classmethod
        def validate_id(cls, value: str) -> str:
            return validate_resource_id(value)


# ──── Response Payloads ───────────────────────────────────────────────────────────────


class Response:
    class Product(BaseModel, frozen=True, from_attributes=True):
        id: str
        brand: str | None
        material: Material
        format: Format
        subformats: set[Format]
        images: list[image.Image]
        listings: list[listing.Listing]
        meta: bytes | None
