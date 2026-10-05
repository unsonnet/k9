from typing import Iterable

from shared.config import is_set, missing, settings
from shared.providers import BaseProvider, GrantSpec, apimethod
from shared.providers.database import DatabaseProvider, DatabaseTypes
from shared.providers.storage import StorageProvider

from .models import Format, Material, Product

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
        id: str,
        brand: str | None,
        material: Material,
        format: Format,
        subformats: set[Format],
        meta: bytes | None,
    ) -> Product:
        self._db.create_item(
            type="product",
            id=id,
            brand=brand,
            material=material.model_dump(),
            format=format.model_dump(),
            subformats=[i.model_dump() for i in subformats],
            meta=meta,
        )
        return self.read_product(id=id)

    @apimethod
    def read_product(
        self,
        *,
        id: str,
    ) -> Product:
        return Product.model_validate(
            self._db.read_item(
                type="product",
                id=id,
            )
        )

    @apimethod
    def update_product(
        self,
        *,
        id: str,
        brand: str | None | missing,
        material: Material | missing,
        format: Format | missing,
        subformats: set[Format] | missing,
        meta: bytes | None | missing,
    ) -> Product:
        attrs: dict[str, DatabaseTypes] = {}
        if is_set(brand):
            attrs["brand"] = brand
        if is_set(material):
            attrs["material"] = material.model_dump()
        if is_set(format):
            attrs["format"] = format.model_dump()
        if is_set(subformats):
            attrs["subformats"] = [i.model_dump() for i in subformats]
        if is_set(meta):
            attrs["meta"] = meta
        self._db.update_item(
            type="product",
            id=id,
            **attrs,
        )
        return self.read_product(id=id)

    @apimethod
    def delete_product(
        self,
        *,
        id: str,
    ) -> None:
        self._db.delete_item(
            type="product",
            id=id,
        )
        return None
