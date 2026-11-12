from typing import Iterable

from k9.providers.base import BaseProvider, GrantSpec, apimethod
from k9.providers.database import DatabaseProvider, DatabaseTypes
from k9.shared.config import is_set, missing, settings
from k9.shared.types import ResourceID, SubresourceID
from pydantic import BaseModel, Field, HttpUrl

from .prices.provider import Price

__all__ = [
    "ListingProvider",
]


class Listing(BaseModel, frozen=True):
    id: SubresourceID
    scope: ResourceID | None
    vendor: ResourceID
    sku: str | None
    name: str
    website: HttpUrl | None
    prices: list[Price] = Field(default_factory=list, alias="$prices")


class ListingProvider(BaseProvider):
    _db: DatabaseProvider

    def __init__(
        self,
        *,
        region: str | None = None,
        table: str | None = None,
    ) -> None:
        region = region or settings.aws_region
        # dynamodb
        self._db = DatabaseProvider(
            region=region,
            table=table or settings.dynamodb_table,
        )

    @property
    def permissions(self) -> Iterable[GrantSpec]:
        yield from self._db.permissions

    # ──── Public Methods ────

    @apimethod
    def create_listing(
        self,
        *,
        id: ResourceID,
        sid: SubresourceID,
        scope: ResourceID | None,
        vendor: ResourceID,
        sku: str | None,
        name: str,
        website: HttpUrl | None,
    ) -> Listing:
        with self._db.batch() as batch:
            batch.check_item(f"companies/{vendor}")
            batch.create_item(
                f"products/{id}/listings/{sid}",
                id=sid,
                scope=scope,
                vendor=vendor,
                sku=sku,
                name=name,
                website=str(website) if website is not None else None,
            )
        return self.read_listing(id=id, sid=sid)

    @apimethod
    def read_listing(
        self,
        *,
        id: ResourceID,
        sid: SubresourceID,
    ) -> Listing:
        return Listing.model_validate(
            self._db.read_item(f"products/{id}/listings/{sid}"),
        )

    @apimethod
    def update_listing(
        self,
        *,
        id: ResourceID,
        sid: SubresourceID,
        scope: ResourceID | None | missing,
        vendor: ResourceID | missing,
        sku: str | None | missing,
        name: str | missing,
        website: HttpUrl | None | missing,
    ) -> Listing:
        attrs: dict[str, DatabaseTypes] = {}
        with self._db.batch() as batch:
            if is_set(scope):
                attrs["scope"] = scope
            if is_set(vendor):
                attrs["vendor"] = vendor
                batch.check_item(f"companies/{vendor}")
            if is_set(sku):
                attrs["sku"] = sku
            if is_set(name):
                attrs["name"] = name
            if is_set(website):
                attrs["website"] = str(website) if website is not None else None
            batch.update_item(f"products/{id}/listings/{sid}", **attrs)
        return self.read_listing(id=id, sid=sid)

    @apimethod
    def delete_listing(
        self,
        *,
        id: ResourceID,
        sid: SubresourceID,
    ) -> None:
        self._db.delete_item(f"products/{id}/listings/{sid}")
        return None
