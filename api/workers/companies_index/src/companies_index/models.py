from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field
from shared.stream import NewImage, OldImage

__all__ = [
    "Request",
]


class Sector(StrEnum):
    INSURANCE = "INSURANCE"
    MANUFACTURER = "MANUFACTURER"
    RETAILER = "RETAILER"


class CompanyItem(BaseModel, frozen=True):
    type: Literal["COMPANY"]
    id: str
    sector: Sector
    name: str = Field(min_length=1)
    logo: str | None
    website: str | None


StreamItem = CompanyItem


class Request:
    class Upsert(BaseModel, frozen=True):
        item: NewImage[StreamItem]

    class Remove(BaseModel, frozen=True):
        item: OldImage[StreamItem]
