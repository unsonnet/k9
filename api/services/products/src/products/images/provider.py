from typing import Iterable

from shared.config import is_set, missing, settings
from shared.providers.base import BaseProvider, GrantSpec, apimethod
from shared.providers.database import DatabaseProvider
from shared.providers.storage import StorageProvider, UploadURL

from .models import Homomorphism, Image, ImageFormat

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
        format: ImageFormat,
        length: int,
        hom: Homomorphism,
    ) -> UploadURL:
        return self._mem.presign_put(
            f"uploads/products/{id}/images/{sid}/create.{format}",
            content_type=format.content_type,
            content_length=length,
            max_seconds=5 * 60,
            metadata={"hom": self._serialize(hom)},
        )

    @apimethod
    def transform_image(
        self,
        *,
        id: str,
        sid: str,
        format: ImageFormat | missing,
        length: int | missing,
        hom: Homomorphism | missing,
    ) -> UploadURL | Image:
        if is_set(format) and is_set(length):
            return self._mem.presign_put(
                f"uploads/products/{id}/images/{sid}/update.{format}",
                content_type=format.content_type,
                content_length=length,
                max_seconds=5 * 60,
                metadata={"hom": self._serialize(hom)} if is_set(hom) else {},
            )
        if is_set(hom):
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

    # ──── Private Methods ────

    @staticmethod
    def _serialize(hom: Homomorphism) -> str:
        return ",".join(str(x) for row in hom for x in row)
