from k9.resolvers.http.requests import Body, Path
from k9.shared.config import missing
from pydantic import BaseModel, Field

from .provider import HttpUrl, Price, ResourceID, SubresourceID

__all__ = [
    "Request",
    "Response",
]


# ──── Request Payloads ────────────────────────────────────────────────────────────────


class Request:
    class Create(BaseModel, frozen=True):
        id: Path[ResourceID]
        scope: Body[ResourceID | None]
        vendor: Body[ResourceID]
        sku: Body[str | None]
        name: Body[str] = Field(min_length=1)
        website: Body[HttpUrl | None]

    class Update(BaseModel, frozen=True):
        id: Path[ResourceID]
        sid: Path[SubresourceID]
        scope: Body[ResourceID | None | missing] = missing
        vendor: Body[ResourceID | missing] = missing
        sku: Body[str | None | missing] = missing
        name: Body[str | missing] = Field(missing, min_length=1)
        website: Body[HttpUrl | None | missing] = missing

    class Delete(BaseModel, frozen=True):
        id: Path[ResourceID]
        sid: Path[SubresourceID]


# ──── Response Payloads ───────────────────────────────────────────────────────────────


class Response:
    class Listing(BaseModel, frozen=True, from_attributes=True):
        id: SubresourceID
        scope: ResourceID | None
        vendor: ResourceID
        sku: str | None
        name: str
        website: HttpUrl | None
        prices: list[Price]
