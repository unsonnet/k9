from decimal import Decimal
from typing import Iterable

from k9.providers.base import BaseProvider, GrantSpec, apimethod
from k9.providers.database import DatabaseProvider, DatabaseTypes
from k9.providers.storage import StorageProvider
from k9.shared.config import is_set, missing, settings
from k9.types.common import ResourceID
from pydantic import BaseModel, Field

from .images.provider import Image
from .listings.provider import Listing
from .materials import Material

__all__ = [
    "ProductProvider",
]


class Format(BaseModel, frozen=True):
    length: Decimal | None
    width: Decimal | None
    thickness: Decimal | None
    wear: Decimal | None


class Product(BaseModel, frozen=True):
    id: ResourceID
    scope: ResourceID | None
    brand: ResourceID | None
    material: Material
    format: Format
    subformats: list[Format]
    images: list[Image] = Field(default_factory=list, alias="$images")
    listings: list[Listing] = Field(default_factory=list, alias="$listings")
    meta: bytes | None


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
        with self._db.batch() as batch:
            if brand is not None:
                batch.check_item(f"companies/{brand}")
            batch.create_item(
                f"products/{id}",
                id=id,
                scope=scope,
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
        attrs: dict[str, DatabaseTypes] = {}
        with self._db.batch() as batch:
            if is_set(scope):
                attrs["scope"] = scope
            if is_set(brand):
                attrs["brand"] = brand
                if brand is not None:
                    batch.check_item(f"companies/{brand}")
            if is_set(material):
                attrs["material"] = material.model_dump()
            if is_set(format):
                attrs["format"] = format.model_dump()
            if is_set(subformats):
                attrs["subformats"] = [i.model_dump() for i in subformats]
            if is_set(meta):
                attrs["meta"] = meta
            batch.update_item(f"products/{id}", **attrs)
        return self.read_product(id=id)

    @apimethod
    def delete_product(
        self,
        *,
        id: ResourceID,
    ) -> None:
        self._db.delete_item(f"products/{id}")
        return None
