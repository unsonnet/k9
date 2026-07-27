from typing import Annotated

from pydantic import BaseModel, Field
from shared.stream import NewImage, OldImage

from .provider import CompanyItem, ContactItem, LocationItem

__all__ = [
    "Request",
]


StreamItem = Annotated[
    CompanyItem | ContactItem | LocationItem, Field(discriminator="type")
]


class Request:
    class Upsert(BaseModel, frozen=True):
        item: NewImage[StreamItem]

    class Remove(BaseModel, frozen=True):
        item: OldImage[StreamItem]
