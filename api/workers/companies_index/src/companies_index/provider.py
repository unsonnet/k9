from collections.abc import Iterable
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel
from shared.config import GrantSpec, settings
from shared.providers import BaseProvider, apimethod
from shared.providers.search import SearchProvider

__all__ = [
    "Sector",
    "CompanyItem",
    "ContactItem",
    "CompanyIndexProvider",
]


class Sector(StrEnum):
    INSURANCE = "INSURANCE"
    MANUFACTURER = "MANUFACTURER"
    RETAILER = "RETAILER"


class CompanyItem(BaseModel, frozen=True):
    type: Literal["company"]
    id: str
    sector: Sector
    name: str
    logo: str | None
    website: str | None


class ContactItem(BaseModel, frozen=True):
    type: Literal["company.contact"]
    id: str
    name: str
    title: str | None
    profile: str | None
    email: str | None
    phone: str | None


class CompanyIndexProvider(BaseProvider):
    _os: SearchProvider

    def __init__(
        self,
        *,
        region: str | None = None,
        endpoint: str | None = None,
        index: str | None = None,
    ) -> None:
        self._os = SearchProvider(
            region=region or settings.aws_region,
            endpoint=endpoint or settings.opensearch_endpoint,
            index=index or settings.opensearch_index_companies,
        )

    @property
    def permissions(self) -> Iterable[GrantSpec]:
        yield from self._os.permissions

    # ──── Public Methods ────

    @apimethod
    def sync_company(self, *, item: CompanyItem) -> None:
        self._os.create_document(
            type=item.type,
            id=item.id,
            sector=item.sector.value,
            name=item.name,
            logo=item.logo,
            website=item.website,
        )

    @apimethod
    def delete_company(self, *, item: CompanyItem) -> None:
        self._os.delete_document(
            type=item.type,
            id=item.id,
        )

    @apimethod
    def sync_contact(self, *, item: ContactItem) -> None:
        self._os.create_document(
            type=item.type,
            id=item.id,
            name=item.name,
            title=item.title,
            profile=item.profile,
            email=item.email,
            phone=item.phone,
        )

    @apimethod
    def delete_contact(self, *, item: ContactItem) -> None:
        self._os.delete_document(
            type=item.type,
            id=item.id,
        )
