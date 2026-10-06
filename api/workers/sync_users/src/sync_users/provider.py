from typing import Iterable

from shared.config import settings
from shared.providers import BaseProvider, GrantSpec, apimethod
from shared.providers.identity import IdentityProvider
from shared.providers.storage import StorageProvider

__all__ = [
    "SyncUserProvider",
]


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
            picture=str(self._mem.get_url(key)),
        )
