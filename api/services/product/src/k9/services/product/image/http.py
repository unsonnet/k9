from k9.resolvers.http.requests import Body, Path
from k9.types.common import ResourceID, SubresourceID, missing
from pydantic import BaseModel, Field

from .provider import Image, ImageFormat

__all__ = [
    "Delete",
    "Transform",
    "Upload",
]


class Upload(BaseModel, frozen=True):
    id: Path[ResourceID]
    scope: Body[ResourceID | None]
    format: Body[ImageFormat]
    length: Body[int] = Field(ge=1, le=5 * 1024 * 1024)
    hom: Body[Image.Homomorphism]


class Transform(BaseModel, frozen=True):
    id: Path[ResourceID]
    sid: Path[SubresourceID]
    scope: Body[ResourceID | None | missing] = missing
    format: Body[ImageFormat | missing] = missing
    length: Body[int | missing] = Field(missing, ge=1, le=5 * 1024 * 1024)
    hom: Body[Image.Homomorphism | missing] = missing


class Delete(BaseModel, frozen=True):
    id: Path[ResourceID]
    sid: Path[SubresourceID]
