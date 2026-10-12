from io import BytesIO
from typing import Iterable

import pillow_jxl  # noqa: F401
from PIL import Image, ImageOps
from pillow_heif import register_heif_opener
from shared.config import settings
from shared.providers.base import BaseProvider, GrantSpec, apimethod
from shared.providers.database import DatabaseProvider
from shared.providers.storage import StorageProvider

__all__ = [
    "SyncCompanyProvider",
]

register_heif_opener()


class SyncCompanyProvider(BaseProvider):
    _mem: StorageProvider
    _db: DatabaseProvider

    def __init__(
        self,
        *,
        region: str | None = None,
        table: str | None = None,
        bucket: str | None = None,
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
    def sync_company(self, key: str, *, id: str) -> None:
        target = f"companies/{id}/logo.jxl"
        self._mem.write(target, self._image(key), content_type="image/jxl")
        self._mem.delete(key)
        self._db.update_item(
            type="company",
            id=id,
            logo=str(self._mem.get_url(target)),
        )

    @apimethod
    def sync_contact(self, key: str, *, id: str, sid: str) -> None:
        target = f"companies/{id}/contacts/{sid}/picture.jxl"
        self._mem.write(target, self._image(key), content_type="image/jxl")
        self._mem.delete(key)
        self._db.update_item(
            type="company.contact",
            id=f"{id}.{sid}",
            picture=str(self._mem.get_url(target)),
        )

    # ──── Private Methods ────

    def _image(self, key: str) -> bytes:
        data = self._mem.read(key)["Body"].read()
        img = ImageOps.exif_transpose(Image.open(BytesIO(data))).convert("RGBA")
        img.save(out := BytesIO(), format="JXL", lossless=True)
        return out.getvalue()
