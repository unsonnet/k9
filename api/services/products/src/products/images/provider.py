from decimal import Decimal
from typing import Iterable

from shared.config import settings
from shared.providers import BaseProvider, GrantSpec, apimethod
from shared.providers.database import DatabaseProvider
from shared.providers.storage import StorageProvider, UploadURL

from .models import Image

__all__ = [
    "ProductImageProvider",
]


class ProductImageProvider(BaseProvider):
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
    def upload_image(
        self,
        *,
        id: str,
        sid: str,
    ) -> UploadURL:
        return self._mem.presign_post(
            f"products/{id}/{sid}.jxl",
            content_type="image/jxl",
            max_bytes=5 * 1024 * 1024,
            max_seconds=5 * 60,
        )

    @apimethod
    def transform_image(
        self,
        *,
        id: str,
        sid: str,
        hom: list[Decimal],
    ) -> Image:
        self._db.update_item(
            type="product.image",
            id=f"{id}.{sid}",
            hom=hom,
        )
        return Image.model_validate(
            self._db.read_item(
                type="product.image",
                id=f"{id}.{sid}",
            ),
        )

    @apimethod
    def delete_image(
        self,
        *,
        id: str,
        sid: str,
    ) -> None:
        self._db.delete_item(
            type="product.image",
            id=f"{id}.{sid}",
        )
        return None
