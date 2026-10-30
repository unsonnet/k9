from functools import cached_property
from typing import Iterable

from pydantic import HttpUrl
from shared.config import is_set, missing, settings
from shared.providers.base import BaseProvider, GrantSpec, apimethod
from shared.providers.database import DatabaseProvider, DatabaseTypes
from shared.providers.storage import StorageProvider, UploadURL

from .models import Company, CompanyType, ImageFormat

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
        id: str,
        type: CompanyType,
        name: str,
        website: HttpUrl | None,
    ) -> Company:
        self._db.create_item(
            f"companies/{id}",
            id=id,
            type=type.value,
            name=name,
            logo=str(self.default_logo),
            website=str(website) if website is not None else None,
        )
        return self.read_company(id=id)

    @apimethod
    def read_company(
        self,
        *,
        id: str,
    ) -> Company:
        return Company.model_validate(
            self._db.read_item(f"companies/{id}"),
        )

    @apimethod
    def update_company(
        self,
        *,
        id: str,
        type: CompanyType | missing,
        name: str | missing,
        logo: None | missing,
        website: HttpUrl | None | missing,
    ) -> Company:
        attrs: dict[str, DatabaseTypes] = {}
        if is_set(type):
            attrs["type"] = type.value
        if is_set(name):
            attrs["name"] = name
        if is_set(logo):
            attrs["logo"] = str(self.default_logo)
        if is_set(website):
            attrs["website"] = str(website) if website is not None else None
        self._db.update_item(f"companies/{id}", **attrs)
        return self.read_company(id=id)

    @apimethod
    def delete_company(
        self,
        *,
        id: str,
    ) -> None:
        self._db.delete_item(f"companies/{id}")
        return None

    @apimethod
    def upload_logo(
        self,
        *,
        id: str,
        format: ImageFormat,
        length: int,
    ) -> UploadURL:
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
