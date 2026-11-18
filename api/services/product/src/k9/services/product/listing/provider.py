from typing import Iterable

from k9.providers.base import BaseProvider, GrantSpec, apimethod
from k9.providers.database import DatabaseProvider
from k9.shared.config import settings
from k9.types.common import ResourceID, SubresourceID, is_set, missing
from k9.types.product import Listing
from pydantic import HttpUrl

__all__ = [
    "ListingProvider",
]


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
                Listing(
                    id=sid,
                    scope=scope,
                    vendor=vendor,
                    sku=sku,
                    name=name,
                    website=website,
                ),
            )
        return self.read_listing(id=id, sid=sid)

    @apimethod
    def read_listing(
        self,
        *,
        id: ResourceID,
        sid: SubresourceID,
    ) -> Listing:
        return self._db.read_item(f"products/{id}/listings/{sid}", Listing)

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
        with self._db.batch() as batch:
            if is_set(vendor):
                batch.check_item(f"companies/{vendor}")
            batch.update_item(
                f"products/{id}/listings/{sid}",
                Listing.partial(
                    scope=scope,
                    vendor=vendor,
                    sku=sku,
                    name=name,
                    website=website,
                ),
            )
        return self.read_listing(id=id, sid=sid)

    @apimethod
    def delete_listing(
        self,
        *,
        id: ResourceID,
        sid: SubresourceID,
    ) -> None:
        return self._db.delete_item(f"products/{id}/listings/{sid}")
