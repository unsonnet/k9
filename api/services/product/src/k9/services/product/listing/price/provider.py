from decimal import Decimal
from typing import Iterable

from k9.providers.base import BaseProvider, GrantSpec, apimethod
from k9.providers.database import DatabaseProvider
from k9.shared.config import settings
from k9.types.common import DateID, ResourceID, SubresourceID, missing
from k9.types.product import Price

__all__ = [
    "PriceProvider",
]


class PriceProvider(BaseProvider):
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
    def create_price(
        self,
        *,
        id: ResourceID,
        sid: SubresourceID,
        date: DateID,
        scope: ResourceID | None,
        currency: str | None,
        rate: Decimal | None,
        unit: Decimal | None,
        stock: Decimal | None,
    ) -> Price:
        with self._db.batch() as batch:
            batch.create_item(
                f"products/{id}/listings/{sid}/prices/{date}",
                Price(
                    id=date,
                    scope=scope,
                    currency=currency,
                    rate=rate,
                    unit=unit,
                    stock=stock,
                ),
            )
        return self.read_price(id=id, sid=sid, date=date)

    @apimethod
    def read_price(
        self,
        *,
        id: ResourceID,
        sid: SubresourceID,
        date: DateID,
    ) -> Price:
        return self._db.read_item(f"products/{id}/listings/{sid}/prices/{date}", Price)

    @apimethod
    def update_price(
        self,
        *,
        id: ResourceID,
        sid: SubresourceID,
        date: DateID,
        scope: ResourceID | None | missing,
        currency: str | None | missing,
        rate: Decimal | None | missing,
        unit: Decimal | None | missing,
        stock: Decimal | None | missing,
    ) -> Price:
        self._db.update_item(
            f"products/{id}/listings/{sid}/prices/{date}",
            Price.partial(
                scope=scope,
                currency=currency,
                rate=rate,
                unit=unit,
                stock=stock,
            ),
        )
        return self.read_price(id=id, sid=sid, date=date)

    @apimethod
    def delete_price(
        self,
        *,
        id: ResourceID,
        sid: SubresourceID,
        date: DateID,
    ) -> None:
        return self._db.delete_item(f"products/{id}/listings/{sid}/prices/{date}")
