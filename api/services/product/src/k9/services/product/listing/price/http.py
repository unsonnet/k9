from decimal import Decimal

from k9.resolvers.http.requests import Body, Path
from k9.types.common import DateID, ResourceID, SubresourceID, missing
from pydantic import BaseModel, Field

__all__ = [
    "Create",
    "Delete",
    "Update",
]


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
