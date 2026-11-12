from k9.resolvers.http.requests import Body, Path
from k9.shared.config import missing
from pydantic import BaseModel, Field

from .provider import Homomorphism, HttpUrl, ImageFormat, ResourceID, SubresourceID

__all__ = [
    "Request",
    "Response",
]


# ──── Request Payloads ────────────────────────────────────────────────────────────────


class Request:
    class Upload(BaseModel, frozen=True):
        id: Path[ResourceID]
        scope: Body[ResourceID | None]
        format: Body[ImageFormat]
        length: Body[int] = Field(ge=1, le=5 * 1024 * 1024)
        hom: Body[Homomorphism]

    class Transform(BaseModel, frozen=True):
        id: Path[ResourceID]
        sid: Path[SubresourceID]
        scope: Body[ResourceID | None | missing] = missing
        format: Body[ImageFormat | missing] = missing
        length: Body[int | missing] = Field(missing, ge=1, le=5 * 1024 * 1024)
        hom: Body[Homomorphism | missing] = missing

    class Delete(BaseModel, frozen=True):
        id: Path[ResourceID]
        sid: Path[SubresourceID]


# ──── Response Payloads ───────────────────────────────────────────────────────────────


class Response:
    class Image(BaseModel, frozen=True, from_attributes=True):
        id: SubresourceID
        scope: ResourceID | None
        url: HttpUrl
        hom: Homomorphism

    class Upload(BaseModel, frozen=True, from_attributes=True):
        url: HttpUrl
        headers: dict[str, str]
