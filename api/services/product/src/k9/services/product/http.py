from k9.resolvers.http.requests import Body, Path
from k9.types.common import ResourceID, missing
from pydantic import BaseModel

from .provider import Format, Material

__all__ = [
    "Create",
    "Delete",
    "Read",
    "Update",
]


class Create(BaseModel, frozen=True):
    scope: Body[ResourceID | None]
    brand: Body[ResourceID | None]
    material: Body[Material]
    format: Body[Format]
    subformats: Body[list[Format]]
    meta: Body[bytes | None]


class Read(BaseModel, frozen=True):
    id: Path[ResourceID]


class Update(BaseModel, frozen=True):
    id: Path[ResourceID]
    scope: Body[ResourceID | None | missing] = missing
    brand: Body[ResourceID | None | missing] = missing
    material: Body[Material | missing] = missing
    format: Body[Format | missing] = missing
    subformats: Body[list[Format] | missing] = missing
    meta: Body[bytes | None | missing] = missing


class Delete(BaseModel, frozen=True):
    id: Path[ResourceID]
