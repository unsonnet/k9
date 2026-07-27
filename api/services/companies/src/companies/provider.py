from collections.abc import Iterable
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field, HttpUrl
from shared.config import GrantSpec, is_set, missing, settings
from shared.http import ImageMIMEType
from shared.providers import BaseProvider, apimethod
from shared.providers.database import DatabaseProvider, DatabaseTypes
from shared.providers.search import Near, Page, SearchProvider, Term, Text
from shared.providers.storage import StorageProvider, UploadURL

from .contacts.provider import Contact

__all__ = [
    "GeoPoint",
    "Location",
    "Contact",
    "Sector",
    "Company",
    "CompanySummary",
    "Page",
    "UploadURL",
    "CompanyProvider",
]


class GeoPoint(BaseModel, frozen=True):
    lat: Decimal
    lon: Decimal


class Location(BaseModel, frozen=True):
    id: str
    street: str
    city: str
    state: str
    zip: str
    geo: GeoPoint


class Sector(StrEnum):
    INSURANCE = "INSURANCE"
    MANUFACTURER = "MANUFACTURER"
    RETAILER = "RETAILER"


class Company(BaseModel):
    id: str
    sector: Sector
    name: str
    logo: HttpUrl | None
    website: HttpUrl | None
    locations: list[Location] = Field(default_factory=list, alias="$location")
    contacts: list[Contact] = Field(default_factory=list, alias="$contact")
    created_at: datetime
    updated_at: datetime | None


class CompanySummary(BaseModel):
    id: str
    sector: Sector
    name: str
    logo: HttpUrl | None
    website: HttpUrl | None
    locations: list[Location] = Field(default_factory=list, alias="$location")


class CompanyProvider(BaseProvider):
    _mem: StorageProvider
    _db: DatabaseProvider
    _os: SearchProvider

    def __init__(
        self,
        *,
        region: str | None = None,
        bucket: str | None = None,
        table: str | None = None,
        index: str | None = None,
        opensearch_endpoint: str | None = None,
    ) -> None:
        region = region or settings.aws_region
        # s3
        self._mem = StorageProvider(
            region=region,
            bucket=bucket or settings.s3_bucket,
        )
        # dynamodb
        self._db = DatabaseProvider(
            region=region,
            table=table or settings.dynamodb_table,
        )
        # opensearch
        self._os = SearchProvider(
            region=region,
            endpoint=opensearch_endpoint or settings.opensearch_endpoint,
            index=index or settings.opensearch_index_companies,
        )

    @property
    def permissions(self) -> Iterable[GrantSpec]:
        yield from self._mem.permissions
        yield from self._db.permissions
        yield from self._os.permissions

    # ──── Public Methods ────

    @apimethod
    def list_companies(
        self,
        *,
        sector: list[Sector] | missing,
        name: str | missing,
        geo: tuple[float, float, int] | missing,
        limit: int,
        cursor: str | missing,
    ) -> Page[CompanySummary]:
        return self._os.search(
            Term("sector", [i.value for i in sector] if is_set(sector) else None),
            Text("name", name if is_set(name) else None),
            Near("$location", geo if is_set(geo) else None),
            limit=limit,
            cursor=cursor if is_set(cursor) else None,
        ).hydrate(CompanySummary)

    @apimethod
    def create_company(
        self,
        *,
        id: str,
        sector: Sector,
        name: str,
        website: HttpUrl | None,
    ) -> Company:
        return Company.model_validate(
            self._db.create_item(
                type="company",
                id=id,
                sector=sector.value,
                name=name,
                logo=None,
                website=str(website) if website is not None else None,
            )
        )

    @apimethod
    def read_company(
        self,
        *,
        id: str,
    ) -> Company:
        return Company.model_validate(
            self._db.read_item(
                type="company",
                id=id,
            )
        )

    @apimethod
    def update_company(
        self,
        *,
        id: str,
        sector: Sector | missing,
        name: str | missing,
        logo: None | missing,
        website: HttpUrl | None | missing,
    ) -> Company:
        attrs: dict[str, DatabaseTypes] = {}
        if is_set(sector):
            attrs["sectory"] = sector.value
        if is_set(name):
            attrs["name"] = name
        if is_set(logo):
            attrs["logo"] = logo
        if is_set(website):
            attrs["website"] = str(website) if website is not None else None
        return Company.model_validate(
            self._db.update_item(
                type="company",
                id=id,
                **attrs,
            )
        )

    @apimethod
    def delete_company(
        self,
        *,
        id: str,
    ) -> None:
        self._db.delete_item(
            type="company",
            id=id,
        )
        return None

    @apimethod
    def upload_logo(
        self,
        *,
        id: str,
        content_type: ImageMIMEType,
        max_bytes: int,
        max_seconds: int,
    ) -> UploadURL:
        return self._mem.presign_post(
            f"companies/{id}/logo.jxl",
            content_type=content_type.value,
            max_bytes=max_bytes,
            max_seconds=max_seconds,
        )
