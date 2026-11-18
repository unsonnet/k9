from k9.resolvers.http.requests import Body, Path
from k9.types.common import ResourceID, SubresourceID, missing
from pydantic import BaseModel, Field

__all__ = [
    "Create",
    "Delete",
    "Update",
]


class Create(BaseModel, frozen=True):
    id: Path[ResourceID]
    scope: Body[ResourceID | None]
    street: Body[str] = Field(min_length=1)
    city: Body[str] = Field(min_length=1)
    state: Body[str] = Field(min_length=2, max_length=2)
    zip: Body[str] = Field(pattern=r"\A\d{5}(-\d{4})?\z")


class Update(BaseModel, frozen=True):
    id: Path[ResourceID]
    sid: Path[SubresourceID]
    scope: Body[ResourceID | None | missing] = missing


class Delete(BaseModel, frozen=True):
    id: Path[ResourceID]
    sid: Path[SubresourceID]
