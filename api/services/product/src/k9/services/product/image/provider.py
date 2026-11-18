from typing import Iterable

from k9.providers.base import BaseProvider, GrantSpec, apimethod
from k9.providers.database import DatabaseProvider
from k9.providers.storage import StorageProvider, UploadForm
from k9.resolvers.http.requests import ImageFormat
from k9.shared.config import settings
from k9.types.common import ResourceID, SubresourceID, is_set, missing
from k9.types.product import Image

__all__ = [
    "ImageProvider",
]


class ImageProvider(BaseProvider):
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
    def create_image(
        self,
        *,
        id: ResourceID,
        sid: SubresourceID,
        scope: ResourceID | None,
        format: ImageFormat,
        length: int,
        hom: Image.Homomorphism,
    ) -> UploadForm:
        return self._mem.presign_put(
            f"uploads/products/{id}/images/{sid}/create.{format}",
            content_type=format.content_type,
            content_length=length,
            max_seconds=5 * 60,
            metadata={"scope": str(scope), "hom": self._serialize(hom)},
        )

    @apimethod
    def read_image(
        self,
        *,
        id: ResourceID,
        sid: SubresourceID,
    ) -> Image:
        return self._db.read_item(f"products/{id}/images/{sid}", Image)

    @apimethod
    def update_image(
        self,
        *,
        id: ResourceID,
        sid: SubresourceID,
        scope: ResourceID | None | missing,
        format: ImageFormat | missing,
        length: int | missing,
        hom: Image.Homomorphism | missing,
    ) -> UploadForm | Image:
        if is_set(format) and is_set(length):
            return self._mem.presign_put(
                f"uploads/products/{id}/images/{sid}/update.{format}",
                content_type=format.content_type,
                content_length=length,
                max_seconds=5 * 60,
                metadata={
                    "scope": str(scope) if is_set(scope) else "",
                    "hom": self._serialize(hom) if is_set(hom) else "",
                },
            )
        self._db.update_item(
            f"products/{id}/images/{sid}",
            Image.partial(
                scope=scope,
                hom=hom,
            ),
        )
        return self.read_image(id=id, sid=sid)

    @apimethod
    def delete_image(
        self,
        *,
        id: ResourceID,
        sid: SubresourceID,
    ) -> None:
        return self._db.delete_item(f"products/{id}/images/{sid}")

    # ──── Private Methods ────

    @staticmethod
    def _serialize(hom: Image.Homomorphism) -> str:
        return ",".join(str(x) for row in hom for x in row)
