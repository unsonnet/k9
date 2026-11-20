from typing import Iterable

from k9.providers.base import BaseProvider, GrantSpec, apimethod
from k9.providers.config import settings
from k9.providers.database import DatabaseProvider
from k9.types.common import DateID, ResourceID, missing
from k9.types.common.config import is_set
from k9.types.contact import EmailStr, Job, PhoneNumber

__all__ = [
    "JobProvider",
]


class JobProvider(BaseProvider):
    _db: DatabaseProvider

    def __init__(
        self,
        *,
        region: str | None = None,
        table: str | None = None,
    ) -> None:
        region = region or settings.aws_region
        # dynamodb
        self._db = DatabaseProvider(
            region=region,
            table=table or settings.dynamodb_table,
        )

    @property
    def permissions(self) -> Iterable[GrantSpec]:
        yield from self._db.permissions

    # ──── Public Methods ────

    @apimethod
    def create_job(
        self,
        *,
        id: ResourceID,
        date: DateID,
        scope: ResourceID | None,
        company: ResourceID | None,
        title: str,
        email: EmailStr | None,
        phone: PhoneNumber | None,
    ) -> Job:
        with self._db.batch() as tx:
            if company is not None:
                tx.check_item(f"companies/{company}")
            tx.create_item(
                f"contacts/{id}/jobs/{date}",
                Job(
                    id=date,
                    scope=scope,
                    company=company,
                    title=title,
                    email=email,
                    phone=phone,
                ),
            )
        return self.read_job(id=id, date=date)

    @apimethod
    def read_job(
        self,
        *,
        id: ResourceID,
        date: DateID,
    ) -> Job:
        return self._db.read_item(f"contacts/{id}/jobs/{date}", Job)

    @apimethod
    def update_job(
        self,
        *,
        id: ResourceID,
        date: DateID,
        scope: ResourceID | None | missing,
        company: ResourceID | None | missing,
        title: str | missing,
        email: EmailStr | None | missing,
        phone: PhoneNumber | None | missing,
    ) -> Job:
        with self._db.batch() as tx:
            if is_set(company) and company is not None:
                tx.check_item(f"companies/{company}")
            tx.update_item(
                f"contacts/{id}/jobs/{date}",
                Job.partial(
                    scope=scope,
                    company=company,
                    title=title,
                    email=email,
                    phone=phone,
                ),
            )
        return self.read_job(id=id, date=date)

    @apimethod
    def delete_job(
        self,
        *,
        id: ResourceID,
        date: DateID,
    ) -> None:
        return self._db.delete_item(f"contacts/{id}/jobs/{date}")
