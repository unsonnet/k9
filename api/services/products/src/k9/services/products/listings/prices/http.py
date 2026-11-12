from decimal import Decimal

from k9.resolvers.http.requests import Body, Path
from k9.shared.config import missing
from pydantic import BaseModel, Field

from .provider import DateID, ResourceID, SubresourceID

__all__ = [
    "Request",
    "Response",
]


# ──── Request Payloads ────────────────────────────────────────────────────────────────


class Request:
    class Create(BaseModel, frozen=True):
        id: Path[ResourceID]
        sid: Path[SubresourceID]
        date: Path[DateID]
        scope: Body[ResourceID | None]
        currency: Body[str | None] = Field(min_length=1)
        rate: Body[Decimal | None]
        unit: Body[Decimal | None]
        stock: Body[Decimal | None]

    class Update(BaseModel, frozen=True):
        id: Path[ResourceID]
        sid: Path[SubresourceID]
        date: Path[DateID]
        scope: Body[ResourceID | None | missing] = missing
        currency: Body[str | None | missing] = Field(missing, min_length=1)
        rate: Body[Decimal | None | missing] = missing
        unit: Body[Decimal | None | missing] = missing
        stock: Body[Decimal | None | missing] = missing

    class Delete(BaseModel, frozen=True):
        id: Path[ResourceID]
        sid: Path[SubresourceID]
        date: Path[DateID]


# ──── Response Payloads ───────────────────────────────────────────────────────────────


class Response:
    class Price(BaseModel, frozen=True, from_attributes=True):
        id: DateID
        scope: ResourceID | None
        currency: str | None
        rate: Decimal | None
        unit: Decimal | None
        stock: Decimal | None
