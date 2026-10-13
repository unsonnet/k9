from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

__all__ = [
    "Location",
]


class Location(BaseModel, frozen=True):
    id: str
    street: str
    city: str
    state: str
    zip: str
    lat: Decimal
    lon: Decimal
    created_at: datetime
    updated_at: datetime | None
