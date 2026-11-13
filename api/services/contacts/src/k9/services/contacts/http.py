from __future__ import annotations

from k9.resolvers.http.requests import Body, Path
from k9.shared.config import missing
from pydantic import BaseModel, Field

from .provider import EmailStr, HttpUrl, ImageFormat, Industry, PhoneNumber, ResourceID

__all__ = [
    "Request",
    "Response",
]


# ──── Request Payloads ────────────────────────────────────────────────────────────────


class Request:
    class Create(BaseModel, frozen=True):
        scope: Body[ResourceID | None]
        type: Body[Industry]
        name: Body[str] = Field(min_length=1)
        email: Body[EmailStr | None]
        phone: Body[PhoneNumber | None]

    class Read(BaseModel, frozen=True):
        id: Path[ResourceID]

    class Update(BaseModel, frozen=True):
        id: Path[ResourceID]
        scope: Body[ResourceID | None | missing] = missing
        type: Body[Industry | missing] = missing
        name: Body[str | missing] = Field(missing, min_length=1)
        picture: Body[None | missing] = missing
        email: Body[EmailStr | None | missing] = missing
        phone: Body[PhoneNumber | None | missing] = missing

    class Delete(BaseModel, frozen=True):
        id: Path[ResourceID]

    class Picture(BaseModel, frozen=True):
        id: Path[ResourceID]
        format: Body[ImageFormat]
        length: Body[int] = Field(ge=1, le=5 * 1024 * 1024)


# ──── Response Payloads ───────────────────────────────────────────────────────────────


class Response:
    class Contact(BaseModel, frozen=True, from_attributes=True):
        id: ResourceID
        scope: ResourceID | None
        type: Industry
        name: str
        picture: HttpUrl
        email: EmailStr | None
        phone: PhoneNumber | None

    class Upload(BaseModel, frozen=True, from_attributes=True):
        url: HttpUrl
        headers: dict[str, str]
