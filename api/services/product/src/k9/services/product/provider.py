from typing import Iterable

from k9.providers.base import BaseProvider, GrantSpec, apimethod
from k9.providers.config import settings
from k9.providers.database import DatabaseProvider
from k9.providers.storage import StorageProvider
from k9.types.common import ResourceID, is_set, missing
from k9.types.product import Format, Material, Product

__all__ = [
    "ProductProvider",
]


class ProductProvider(BaseProvider):
    _mem: StorageProvider
    _db: DatabaseProvider

    def __init__(
        self,
        *,
        region: str | None = None,
        bucket: str | None = None,
        table: str | None = None,
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

    @property
    def permissions(self) -> Iterable[GrantSpec]:
        yield from self._mem.permissions
        yield from self._db.permissions

    # ──── Public Methods ────

    @apimethod
    def create_product(
        self,
        *,
        id: ResourceID,
        scope: ResourceID | None,
        brand: ResourceID | None,
        material: Material,
        format: Format,
        subformats: list[Format],
        meta: bytes | None,
    ) -> Product:
        with self._db.batch() as tx:
            if brand is not None:
                tx.check_item(f"companies/{brand}")
            tx.create_item(
                f"products/{id}",
                Product(
                    id=id,
                    scope=scope,
                    brand=brand,
                    material=material,
                    format=format,
                    subformats=subformats,
                    meta=meta,
                ),
            )
        return self.read_product(id=id)

    @apimethod
    def read_product(
        self,
        *,
        id: ResourceID,
    ) -> Product:
        return Product.model_validate(
            self._db.read_item(f"products/{id}"),
        )

    @apimethod
    def update_product(
        self,
        *,
        id: ResourceID,
        scope: ResourceID | None | missing,
        brand: ResourceID | None | missing,
        material: Material | missing,
        format: Format | missing,
        subformats: list[Format] | missing,
        meta: bytes | None | missing,
    ) -> Product:
        with self._db.batch() as tx:
            if is_set(brand) and brand is not None:
                tx.check_item(f"companies/{brand}")
            tx.update_item(
                f"products/{id}",
                Product.partial(
                    scope=scope,
                    brand=brand,
                    material=material,
                    format=format,
                    subformats=subformats,
                    meta=meta,
                ),
            )
        return self.read_product(id=id)

    @apimethod
    def delete_product(
        self,
        *,
        id: ResourceID,
    ) -> None:
        return self._db.delete_item(f"products/{id}")
