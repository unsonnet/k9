from functools import cached_property
from typing import Iterable

from k9.providers.base import BaseProvider, GrantSpec, apimethod
from k9.providers.database import DatabaseProvider
from k9.providers.storage import HttpUrl, StorageProvider, UploadForm
from k9.resolvers.http.requests import ImageFormat
from k9.shared.config import settings
from k9.types.common import ResourceID, missing
from k9.types.company import Company, Industry

__all__ = [
    "CompanyProvider",
]


class CompanyProvider(BaseProvider):
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
    def create_company(
        self,
        *,
        id: ResourceID,
        scope: ResourceID | None,
        type: Industry,
        name: str,
        website: HttpUrl | None,
    ) -> Company:
        self._db.create_item(
            f"companies/{id}",
            Company(
                id=id,
                scope=scope,
                type=type,
                name=name,
                logo=self.default_logo,
                website=website,
            ),
        )
        return self.read_company(id=id)

    @apimethod
    def read_company(
        self,
        *,
        id: ResourceID,
    ) -> Company:
        return self._db.read_item(
            f"companies/{id}",
            Company,
        )

    @apimethod
    def update_company(
        self,
        *,
        id: ResourceID,
        scope: ResourceID | None | missing,
        type: Industry | missing,
        name: str | missing,
        logo: None | missing,
        website: HttpUrl | None | missing,
    ) -> Company:
        self._db.update_item(
            f"companies/{id}",
            Company.partial(
                scope=scope,
                type=type,
                name=name,
                logo=self.default_logo if logo is None else missing,
                website=website,
            ),
        )
        return self.read_company(id=id)

    @apimethod
    def delete_company(
        self,
        *,
        id: ResourceID,
    ) -> None:
        return self._db.delete_item(f"companies/{id}")

    @apimethod
    def upload_logo(
        self,
        *,
        id: ResourceID,
        format: ImageFormat,
        length: int,
    ) -> UploadForm:
        return self._mem.presign_put(
            f"uploads/companies/{id}/logo.{format}",
            content_type=format.content_type,
            content_length=length,
            max_seconds=5 * 60,
        )

    # ──── Private Methods ────

    @cached_property
    def default_logo(self) -> HttpUrl:
        return self._mem.get_url("companies/default/logo.jxl")
