from k9.resolvers.http.requests import Body, Path
from k9.types.common import ResourceID, SubresourceID, missing
from pydantic import BaseModel, Field

from .provider import HttpUrl

__all__ = [
    "Create",
    "Delete",
    "Update",
]


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
