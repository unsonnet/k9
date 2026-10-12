from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, Field, HttpUrl
from shared.resolvers.http.requests import ImageFormat

__all__ = [
    "Image",
    "ImageFormat",
    "Homomorphism",
]


type Vector = Annotated[list[Decimal], Field(min_length=3, max_length=3)]
type Homomorphism = Annotated[list[Vector], Field(min_length=3, max_length=3)]


class Image(BaseModel, frozen=True):
    id: str
    url: HttpUrl
    hom: Homomorphism
    created_at: datetime
    updated_at: datetime | None
