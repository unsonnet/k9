from enum import StrEnum

from pydantic import BaseModel, Field, HttpUrl
from shared.providers.storage import UploadURL
from shared.resolvers.http.requests import ImageFormat

from .contacts.models import Contact
from .locations.models import Location

__all__ = [
    "Company",
    "Contact",
    "Location",
    "CompanyType",
    "UploadURL",
    "ImageFormat",
]


class CompanyType(StrEnum):
    INSURANCE = "insurance"
    MANUFACTURER = "manufacturer"
    RETAILER = "retailer"


class Company(BaseModel, frozen=True):
    id: str
    type: CompanyType
    name: str
    logo: HttpUrl
    website: HttpUrl | None
    locations: list[Location] = Field(default_factory=list, alias="$locations")
    contacts: list[Contact] = Field(default_factory=list, alias="$contacts")
