from typing import Self

from pydantic import BaseModel, EmailStr, Field, HttpUrl, field_validator
from pydantic_extra_types.phone_numbers import PhoneNumber
from shared.config import missing
from shared.helpers import validate_resource_id, validate_subresource_id
from shared.http import Body, ImageMIMEType, Path

from .provider import Contact, UploadURL

__all__ = [
    "Request",
    "Response",
]


# ──── Request Payloads ────────────────────────────────────────────────────────────────


class Request:
    class Create(BaseModel, frozen=True):
        id: Path[str]
        name: Body[str] = Field(min_length=1)
        title: Body[str | None] = Field(None, min_length=1)
        email: Body[EmailStr | None] = None
        phone: Body[PhoneNumber | None] = None

        @field_validator("id")
        @classmethod
        def validate_id(cls, value: str) -> str:
            return validate_resource_id(value)

    class Read(BaseModel, frozen=True):
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

    class Update(BaseModel, frozen=True):
        id: Path[str]
        sid: Path[str]
        name: Body[str | missing] = Field(missing, min_length=1)
        title: Body[str | None | missing] = Field(missing, min_length=1)
        profile: Body[None | missing] = missing
        email: Body[EmailStr | None | missing] = missing
        phone: Body[PhoneNumber | None | missing] = missing

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

    class Profile(BaseModel, frozen=True):
        id: Path[str]
        sid: Path[str]
        contentType: Body[ImageMIMEType]

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
    class Contact(BaseModel, frozen=True):
        id: str
        name: str
        title: str | None
        profile: HttpUrl | None
        email: EmailStr | None
        phone: PhoneNumber | None

        @classmethod
        def pack(cls, contact: Contact):
            return cls(
                id=contact.id,
                name=contact.name,
                title=contact.title,
                profile=contact.profile,
                email=contact.email,
                phone=contact.phone,
            )

    class UploadURL(BaseModel, frozen=True):
        url: HttpUrl
        fields: dict[str, str]

        @classmethod
        def pack(cls, upload: UploadURL) -> Self:
            return cls(
                url=upload.url,
                fields=upload.fields,
            )
