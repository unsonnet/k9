from pydantic import BaseModel, EmailStr, Field, HttpUrl, field_validator
from pydantic_extra_types.phone_numbers import PhoneNumber
from shared.config import missing
from shared.helpers import validate_resource_id, validate_subresource_id
from shared.http.requests import Body, Path

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
        picture: Body[None | missing] = missing
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

    class Picture(BaseModel, frozen=True):
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
    class Contact(BaseModel, frozen=True, from_attributes=True):
        id: str
        name: str
        title: str | None
        picture: HttpUrl
        email: EmailStr | None
        phone: PhoneNumber | None

    class UploadURL(BaseModel, frozen=True, from_attributes=True):
        url: HttpUrl
        fields: dict[str, str]
