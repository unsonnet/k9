from typing import Iterable

from k9.providers.base import BaseProvider, GrantSpec, apimethod
from k9.providers.database import DatabaseProvider, DatabaseTypes
from k9.shared.config import is_set, missing, settings
from k9.types.common import DateID, ResourceID
from pydantic import BaseModel, EmailStr
from pydantic_extra_types.phone_numbers import PhoneNumber

__all__ = [
    "JobProvider",
]


class Job(BaseModel, frozen=True):
    id: DateID
    scope: ResourceID | None
    company: ResourceID
    title: str
    email: EmailStr | None
    phone: PhoneNumber | None


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
        company: ResourceID,
        title: str,
        email: EmailStr | None,
        phone: PhoneNumber | None,
    ) -> Job:
        self._db.create_item(
            f"contacts/{id}/jobs/{date}",
            id=id,
            scope=scope,
            company=company,
            title=title,
            email=email,
            phone=phone,
        )
        return self.read_job(id=id, date=date)

    @apimethod
    def read_job(
        self,
        *,
        id: ResourceID,
        date: DateID,
    ) -> Job:
        return Job.model_validate(
            self._db.read_item(f"contacts/{id}/jobs/{date}"),
        )

    @apimethod
    def update_job(
        self,
        *,
        id: ResourceID,
        date: DateID,
        scope: ResourceID | None | missing,
        company: ResourceID | missing,
        title: str | missing,
        email: EmailStr | None | missing,
        phone: PhoneNumber | None | missing,
    ) -> Job:
        attrs: dict[str, DatabaseTypes] = {}
        if is_set(scope):
            attrs["scope"] = scope
        if is_set(company):
            attrs["company"] = company
        if is_set(title):
            attrs["title"] = title
        if is_set(email):
            attrs["email"] = email
        if is_set(phone):
            attrs["phone"] = phone
        self._db.update_item(f"contacts/{id}/jobs/{date}", **attrs)
        return self.read_job(id=id, date=date)

    @apimethod
    def delete_job(
        self,
        *,
        id: ResourceID,
        date: DateID,
    ) -> None:
        self._db.delete_item(f"contacts/{id}/jobs/{date}")
        return None
