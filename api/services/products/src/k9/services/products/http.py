from k9.resolvers.http.requests import Body, Path
from k9.shared.config import missing
from pydantic import BaseModel

from .images.http import Response as image
from .listings.http import Response as listing
from .provider import Format, Material, ResourceID

__all__ = [
    "Request",
    "Response",
]


# ──── Request Payloads ────────────────────────────────────────────────────────────────


class Request:
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


# ──── Response Payloads ───────────────────────────────────────────────────────────────


class Response:
    class Product(BaseModel, frozen=True, from_attributes=True):
        id: ResourceID
        scope: ResourceID | None
        brand: ResourceID | None
        material: Material
        format: Format
        subformats: list[Format]
        images: list[image.Image]
        listings: list[listing.Listing]
        meta: bytes | None
