from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, HttpUrl

__all__ = [
    "Price",
    "Listing",
]


class Price(BaseModel, frozen=True):
    amount: Decimal | None
    posted_at: datetime


class Listing(BaseModel, frozen=True):
    id: str
    vendor: str
    sku: str | None
    name: str
    prices: list[Price]
    url: HttpUrl | None
    created_at: datetime
    updated_at: datetime | None
