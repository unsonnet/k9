from pydantic import BaseModel, EmailStr, Field, field_validator
from shared.config import missing
from shared.http import Body, Path, Query
from shared.providers.company import validate_id, validate_sub_id

__all__ = [
    "Contact",
    "Page",
    "Request",
    "Response",
]


class Contact(BaseModel, frozen=True):
    id: str
    name: str
    title: str | None
    email: EmailStr | None
    phone: str | None


class Page(BaseModel, frozen=True):
    contacts: list[Contact]
    cursor: str | None


# ──── Request Payloads ────────────────────────────────────────────────────────────────


class Request:
    class List(BaseModel, frozen=True):
        id: Path[str]
        limit: Query[int] = Field(25, ge=1, le=60)
        cursor: Query[str | missing] = missing

        @field_validator("id")
        @classmethod
        def validate_id(cls, value: str) -> str:
            return validate_id(value)

    class Create(BaseModel, frozen=True):
        id: Path[str]
        name: Body[str] = Field(min_length=1)
        title: Body[str | None] = Field(None, min_length=1)
        email: Body[EmailStr | None] = None
        phone: Body[str | None] = Field(None, min_length=10)

        @field_validator("id")
        @classmethod
        def validate_id(cls, value: str) -> str:
            return validate_id(value)

    class Read(BaseModel, frozen=True):
        id: Path[str]
        sid: Path[str]

        @field_validator("id")
        @classmethod
        def validate_id(cls, value: str) -> str:
            return validate_id(value)

        @field_validator("sid")
        @classmethod
        def validate_sub_id(cls, value: str) -> str:
            return validate_sub_id(value)

    class Update(BaseModel, frozen=True):
        id: Path[str]
        sid: Path[str]
        name: Body[str | missing] = Field(missing, min_length=1)
        title: Body[str | None | missing] = Field(missing, min_length=1)
        email: Body[EmailStr | None | missing] = Field(missing)
        phone: Body[str | None | missing] = Field(missing, min_length=10)

        @field_validator("id")
        @classmethod
        def validate_id(cls, value: str) -> str:
            return validate_id(value)

        @field_validator("sid")
        @classmethod
        def validate_sub_id(cls, value: str) -> str:
            return validate_sub_id(value)

    class Delete(BaseModel, frozen=True):
        id: Path[str]
        sid: Path[str]

        @field_validator("id")
        @classmethod
        def validate_id(cls, value: str) -> str:
            return validate_id(value)

        @field_validator("sid")
        @classmethod
        def validate_sub_id(cls, value: str) -> str:
            return validate_sub_id(value)


# ──── Response Payloads ───────────────────────────────────────────────────────────────


class Response:
    class Contact(BaseModel, frozen=True):
        id: str
        name: str
        title: str | None
        email: EmailStr | None
        phone: str | None

        @classmethod
        def pack(cls, company: Contact):
            return cls(
                id=company.id,
                name=company.name,
                title=company.title,
                email=company.email,
                phone=company.phone,
            )

    class Page(BaseModel, frozen=True):
        contacts: list["Response.Contact"]
        cursor: str | None

        @classmethod
        def pack(cls, page: Page):
            return cls(
                contacts=[Response.Contact.pack(contact) for contact in page.contacts],
                cursor=page.cursor,
            )
