from decimal import Decimal

from pydantic import BaseModel, Field, HttpUrl, field_validator
from shared.config import missing
from shared.helpers import validate_resource_id, validate_subresource_id
from shared.resolvers.http.requests import Body, Path

from .models import Homomorphism, ImageFormat

__all__ = [
    "Request",
    "Response",
]


# ──── Request Payloads ────────────────────────────────────────────────────────────────


class Request:
    class Upload(BaseModel, frozen=True):
        id: Path[str]
        format: Body[ImageFormat]
        length: Body[int] = Field(ge=1, le=5 * 1024 * 1024)
        hom: Body[Homomorphism]

        @field_validator("id")
        @classmethod
        def validate_id(cls, value: str) -> str:
            return validate_resource_id(value)

    class Transform(BaseModel, frozen=True):
        id: Path[str]
        sid: Path[str]
        format: Body[ImageFormat | missing]
        length: Body[int | missing] = Field(ge=1, le=5 * 1024 * 1024)
        hom: Body[Homomorphism | missing]

        @field_validator("id")
        @classmethod
        def validate_id(cls, value: str) -> str:
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
    class Image(BaseModel, frozen=True, from_attributes=True):
        id: str
        url: HttpUrl
        hom: list[Decimal]

    class UploadURL(BaseModel, frozen=True, from_attributes=True):
        url: HttpUrl
        headers: dict[str, str]
