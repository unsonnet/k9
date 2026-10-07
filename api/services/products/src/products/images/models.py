from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, HttpUrl
from shared.http.requests import ImageFormat

__all__ = [
    "Image",
    "ImageFormat",
]


class Image(BaseModel, frozen=True):
    id: str
    url: HttpUrl
    hom: list[Decimal]
    created_at: datetime
    updated_at: datetime | None
