from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, HttpUrl
from shared.http.requests import ImageFormat
from shared.providers.search import Page
from shared.providers.storage import UploadURL

from .contacts.provider import Contact
from .locations.models import Location, LocationIndex

__all__ = [
    "Company",
    "CompanyIndex",
    "Contact",
    "Location",
    "LocationIndex",
    "Page",
    "Sector",
    "UploadURL",
    "ImageFormat",
]


class Sector(StrEnum):
    INSURANCE = "INSURANCE"
    MANUFACTURER = "MANUFACTURER"
    RETAILER = "RETAILER"


class Company(BaseModel, frozen=True):
    id: str
    sector: Sector
    name: str
    logo: HttpUrl
    website: HttpUrl | None
    locations: list[Location] = Field(default_factory=list, alias="$location")
    contacts: list[Contact] = Field(default_factory=list, alias="$contact")
    created_at: datetime
    updated_at: datetime | None


class CompanyIndex(BaseModel, frozen=True):
    id: str
    sector: Sector
    name: str
    logo: HttpUrl
    website: HttpUrl | None
    locations: list[LocationIndex] = Field(default_factory=list, alias="$location")
