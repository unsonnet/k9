from decimal import Decimal

from pydantic import AliasPath, BaseModel, Field, HttpUrl
from shared.providers.search import Page

from ..models import CompanyType

__all__ = [
    "LocationIndex",
    "CompanyIndex",
    "Page",
    "CompanyType",
]


class LocationIndex(BaseModel, frozen=True):
    id: str
    street: str
    city: str
    state: str
    zip: str
    lat: Decimal = Field(validation_alias=AliasPath("geo", "lat"))
    lon: Decimal = Field(validation_alias=AliasPath("geo", "lon"))


class CompanyIndex(BaseModel, frozen=True):
    id: str
    type: CompanyType
    name: str
    logo: HttpUrl
    website: HttpUrl | None
    locations: list[LocationIndex] = Field(default_factory=list, alias="$locations")
