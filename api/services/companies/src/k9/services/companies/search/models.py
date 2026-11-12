from decimal import Decimal

from k9.providers.search import Page
from pydantic import AliasPath, BaseModel, Field, HttpUrl

from ..provider import Industry

__all__ = [
    "LocationIndex",
    "CompanyIndex",
    "Page",
    "Industry",
]


class LocationIndex(BaseModel, frozen=True):
    id: str
    lat: Decimal = Field(validation_alias=AliasPath("geo", "lat"))
    lng: Decimal = Field(validation_alias=AliasPath("geo", "lon"))


class CompanyIndex(BaseModel, frozen=True):
    id: str
    type: Industry
    name: str
    logo: HttpUrl
    website: HttpUrl | None
    locations: list[LocationIndex] = Field(default_factory=list, alias="$locations")
