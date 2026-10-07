from typing import Iterable

from pydantic import HttpUrl
from shared.config import is_set, missing, settings
from shared.providers import BaseProvider, GrantSpec, apimethod
from shared.providers.database import DatabaseProvider, DatabaseTypes

from .models import Listing, Price

__all__ = [
    "ProductListingProvider",
]


class ProductListingProvider(BaseProvider):
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
        id: str,
        sid: str,
        vendor: str,
        sku: str | None,
        name: str,
        prices: list[Price],
        url: HttpUrl | None,
    ) -> Listing:
        with self._db.batch() as batch:
            batch.check_item(
                type="company",
                id=vendor,
            )
            batch.create_item(
                type="product.listing",
                id=f"{id}.{sid}",
                vendor=vendor,
                sku=sku,
                name=name,
                prices=[i.model_dump() for i in prices],
                url=str(url) if url is not None else None,
            )
        return self.read_listing(id=id, sid=sid)

    @apimethod
    def read_listing(
        self,
        *,
        id: str,
        sid: str,
    ) -> Listing:
        return Listing.model_validate(
            self._db.read_item(
                type="product.listing",
                id=f"{id}.{sid}",
            )
        )

    @apimethod
    def update_listing(
        self,
        *,
        id: str,
        sid: str,
        vendor: str | missing,
        sku: str | None | missing,
        name: str | missing,
        prices: list[Price] | missing,
        url: HttpUrl | None | missing,
    ) -> Listing:
        attrs: dict[str, DatabaseTypes] = {}
        with self._db.batch() as batch:
            if is_set(vendor):
                attrs["vendor"] = vendor
                batch.check_item(
                    type="company",
                    id=vendor,
                )
            if is_set(sku):
                attrs["sku"] = sku
            if is_set(name):
                attrs["name"] = name
            if is_set(prices):
                attrs["prices"] = [i.model_dump() for i in prices]
            if is_set(url):
                attrs["url"] = str(url) if url is not None else None
            batch.update_item(
                type="product.listing",
                id=f"{id}.{sid}",
                **attrs,
            )
        return self.read_listing(id=id, sid=sid)

    @apimethod
    def delete_listing(
        self,
        *,
        id: str,
        sid: str,
    ) -> None:
        self._db.delete_item(
            type="product.listing",
            id=f"{id}.{sid}",
        )
        return None
