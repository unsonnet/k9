from typing import Iterable

from shared.config import settings
from shared.providers import BaseProvider, GrantSpec, apimethod
from shared.providers.database import DatabaseProvider
from shared.providers.identity import IdentityProvider
from shared.providers.storage import StorageProvider

__all__ = [
    "ProfileIndexProvider",
]


class ProfileIndexProvider(BaseProvider):
    _idp: IdentityProvider
    _mem: StorageProvider
    _db: DatabaseProvider

    def __init__(
        self,
        *,
        region: str | None = None,
        table: str | None = None,
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
        # dynamodb
        self._db = DatabaseProvider(
            region=region,
            table=table or settings.dynamodb_table,
        )

    @property
    def permissions(self) -> Iterable[GrantSpec]:
        yield from self._idp.permissions
        yield from self._db.permissions

    # ──── Public Methods ────

    @apimethod
    def sync_user(self, key: str, *, id: str) -> None:
        self._idp.update_user(
            username=f"id:{id}",
            picture=str(self._mem.get_url(key)),
        )

    @apimethod
    def sync_company(self, key: str, *, id: str) -> None:
        self._db.update_item(
            type="company",
            id=id,
            logo=str(self._mem.get_url(key)),
        )

    @apimethod
    def sync_contact(self, key: str, *, id: str, sid: str) -> None:
        self._db.update_item(
            type="company.contact",
            id=f"{id}.{sid}",
            picture=str(self._mem.get_url(key)),
        )
