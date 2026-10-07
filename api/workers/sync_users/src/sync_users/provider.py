from io import BytesIO
from typing import Iterable

import pillow_jxl  # noqa: F401
from PIL import Image, ImageOps
from pillow_heif import register_heif_opener
from shared.config import settings
from shared.providers import BaseProvider, GrantSpec, apimethod
from shared.providers.identity import IdentityProvider
from shared.providers.storage import StorageProvider

__all__ = [
    "SyncUserProvider",
]

register_heif_opener()


class SyncUserProvider(BaseProvider):
    _idp: IdentityProvider
    _mem: StorageProvider

    def __init__(
        self,
        *,
        region: str | None = None,
        bucket: str | None = None,
        user_pool_id: str | None = None,
    ) -> None:
        region = region or settings.aws_region
        # cognito idp
        self._idp = IdentityProvider(
            region=region,
            pool=user_pool_id or settings.cognito_user_pool_id,
        )
        # s3
        self._mem = StorageProvider(
            region=region,
            bucket=bucket or settings.s3_bucket,
        )

    @property
    def permissions(self) -> Iterable[GrantSpec]:
        yield from self._idp.permissions
        yield from self._mem.permissions

    # ──── Public Methods ────

    @apimethod
    def sync_user(self, key: str, *, id: str) -> None:
        self._idp.update_user(
            username=f"id:{id}",
            picture=str(self._mem.get_url(self._convert(key))),
        )

    # ──── Private Methods ────

    def _convert(self, key: str) -> str:
        target = key.removeprefix("uploads/").rpartition(".")[0] + ".jxl"
        data = self._to_jxl(self._mem.read(key))
        self._mem.write(target, data, content_type="image/jxl")
        self._mem.delete(key)
        return target

    @staticmethod
    def _to_jxl(data: bytes) -> bytes:
        img = ImageOps.exif_transpose(Image.open(BytesIO(data)))
        img = img.convert("RGBA")
        img.save(out := BytesIO(), format="JXL", lossless=True)
        return out.getvalue()
