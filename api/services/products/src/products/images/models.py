from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, HttpUrl

__all__ = [
    "Image",
]


class Image(BaseModel, frozen=True):
    id: str
    url: HttpUrl
    hom: list[Decimal]
    created_at: datetime
    updated_at: datetime | None
