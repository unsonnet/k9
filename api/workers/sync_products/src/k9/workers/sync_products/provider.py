from decimal import Decimal
from io import BytesIO
from typing import Iterable

import pillow_jxl  # noqa: F401
from k9.providers.base import BaseProvider, GrantSpec, apimethod
from k9.providers.database import DatabaseProvider
from k9.providers.storage import StorageObject, StorageProvider
from k9.shared.config import settings
from PIL import Image, ImageOps
from pillow_heif import register_heif_opener

__all__ = [
    "SyncProductProvider",
]

register_heif_opener()


class SyncProductProvider(BaseProvider):
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
    def create_image(self, key: str, *, id: str, sid: str) -> None:
        new = self._mem.read(key)
        target = f"products/{id}/images/{sid}.jxl"
        self._mem.write(target, self._image(new), content_type="image/jxl")
        self._mem.delete(key)
        self._db.create_item(
            f"products/{id}/images/{sid}",
            id=sid,
            url=str(self._mem.get_url(target)),
            **self._scope(new),
            **self._hom(new),
        )

    @apimethod
    def update_image(self, key: str, *, id: str, sid: str) -> None:
        new = self._mem.read(key)
        target = f"products/{id}/images/{sid}.jxl"
        old = self._mem.read(target)
        self._mem.write(target, self._image(old, mask=new), content_type="image/jxl")
        self._mem.delete(key)
        self._db.update_item(
            f"products/{id}/images/{sid}",
            **self._scope(new),
            **self._hom(new),
        )

    # ──── Private Methods ────

    @staticmethod
    def _image(obj: StorageObject, *, mask: StorageObject | None = None) -> bytes:
        data = obj["Body"].read()
        img = ImageOps.exif_transpose(Image.open(BytesIO(data))).convert("RGBA")
        if mask:
            data = mask["Body"].read()
            alpha = ImageOps.exif_transpose(Image.open(BytesIO(data))).convert("RGBA")
            img.putalpha(alpha.getchannel("A").resize(img.size))
        img.save(out := BytesIO(), format="JXL", lossless=True)
        return out.getvalue()

    @staticmethod
    def _scope(obj: StorageObject) -> dict[str, str | None]:
        match obj["Metadata"].get("scope", ""):
            case "":
                return {}
            case "None":
                return {"scope": None}
            case str(scope):
                return {"scope": scope}

    @staticmethod
    def _hom(obj: StorageObject) -> dict[str, list[list[Decimal]]]:
        match obj["Metadata"].get("hom", ""):
            case "":
                return {}
            case str(raw):
                hom = [Decimal(x) for x in raw.split(",")]
                return {"hom": [hom[i : i + 3] for i in [0, 3, 6]]}
