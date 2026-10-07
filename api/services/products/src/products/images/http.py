from decimal import Decimal

from pydantic import BaseModel, Field, HttpUrl, field_validator
from shared.helpers import validate_resource_id, validate_subresource_id
from shared.http.requests import Body, Path

from .models import ImageFormat

__all__ = [
    "Request",
    "Response",
]


# ──── Request Payloads ────────────────────────────────────────────────────────────────


class Request:
    class Upload(BaseModel, frozen=True):
        id: Path[str]
        format: Body[ImageFormat]

        @field_validator("id")
        @classmethod
        def validate_id(cls, value: str) -> str:
            return validate_resource_id(value)

    class Update(BaseModel, frozen=True):
        id: Path[str]
        sid: Path[str]
        format: Body[ImageFormat]

        @field_validator("id")
        @classmethod
        def validate_id(cls, value: str) -> str:
            return validate_resource_id(value)

        @field_validator("sid")
        @classmethod
        def validate_sub_id(cls, value: str) -> str:
            return validate_subresource_id(value)

    class Transform(BaseModel, frozen=True):
        id: Path[str]
        sid: Path[str]
        hom: Body[list[Decimal]] = Field(min_length=1)

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
        fields: dict[str, str]
