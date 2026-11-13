from __future__ import annotations

from k9.resolvers.http.requests import Body, Path
from k9.shared.config import missing
from pydantic import BaseModel, Field

from .provider import DateID, EmailStr, PhoneNumber, ResourceID

__all__ = [
    "Request",
    "Response",
]


# ──── Request Payloads ────────────────────────────────────────────────────────────────


class Request:
    class Create(BaseModel, frozen=True):
        id: Path[ResourceID]
        date: Path[DateID]
        scope: Body[ResourceID | None]
        company: Body[ResourceID]
        title: Body[str]
        email: Body[EmailStr | None]
        phone: Body[PhoneNumber | None]

    class Update(BaseModel, frozen=True):
        id: Path[ResourceID]
        date: Path[DateID]
        scope: Body[ResourceID | None | missing] = missing
        company: Body[ResourceID | missing] = missing
        title: Body[str | missing] = Field(missing, min_length=1)
        email: Body[EmailStr | None | missing] = missing
        phone: Body[PhoneNumber | None | missing] = missing

    class Delete(BaseModel, frozen=True):
        id: Path[ResourceID]
        date: Path[DateID]


# ──── Response Payloads ───────────────────────────────────────────────────────────────


class Response:
    class Job(BaseModel, frozen=True, from_attributes=True):
        id: DateID
        scope: ResourceID | None
        company: ResourceID
        title: str
        email: EmailStr | None
        phone: PhoneNumber | None
