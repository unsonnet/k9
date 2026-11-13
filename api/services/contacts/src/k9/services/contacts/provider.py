from functools import cached_property
from typing import Iterable, Literal

from k9.providers.base import BaseProvider, GrantSpec, apimethod
from k9.providers.database import DatabaseProvider, DatabaseTypes
from k9.providers.storage import HttpUrl, StorageProvider, Upload
from k9.resolvers.http.requests import ImageFormat
from k9.shared.config import is_set, missing, settings
from k9.types.common import ResourceID
from pydantic import BaseModel, EmailStr, Field
from pydantic_extra_types.phone_numbers import PhoneNumber

from .jobs.provider import Job

__all__ = [
    "ContactProvider",
]


type Industry = Literal["insurance", "manufacturing", "retail"]


class Contact(BaseModel, frozen=True):
    id: ResourceID
    scope: ResourceID | None
    type: Industry
    name: str
    picture: HttpUrl
    email: EmailStr | None
    phone: PhoneNumber | None
    jobs: list[Job] = Field(default_factory=list, alias="$jobs")


class ContactProvider(BaseProvider):
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
    def create_contact(
        self,
        *,
        id: ResourceID,
        scope: ResourceID | None,
        type: Industry,
        name: str,
        email: EmailStr | None,
        phone: PhoneNumber | None,
    ) -> Contact:
        self._db.create_item(
            f"contacts/{id}",
            id=id,
            scope=scope,
            type=type,
            name=name,
            picture=str(self.default_picture),
            email=email,
            phone=phone,
        )
        return self.read_contact(id=id)

    @apimethod
    def read_contact(
        self,
        *,
        id: ResourceID,
    ) -> Contact:
        return Contact.model_validate(
            self._db.read_item(f"contacts/{id}"),
        )

    @apimethod
    def update_contact(
        self,
        *,
        id: ResourceID,
        scope: ResourceID | None | missing,
        type: Industry | missing,
        name: str | missing,
        picture: HttpUrl | None | missing,
        email: EmailStr | None | missing,
        phone: PhoneNumber | None | missing,
    ) -> Contact:
        attrs: dict[str, DatabaseTypes] = {}
        if is_set(scope):
            attrs["scope"] = scope
        if is_set(type):
            attrs["type"] = type
        if is_set(name):
            attrs["name"] = name
        if is_set(picture):
            attrs["picture"] = str(picture) if picture is not None else None
        if is_set(email):
            attrs["email"] = email
        if is_set(phone):
            attrs["phone"] = phone
        self._db.update_item(f"contacts/{id}", **attrs)
        return self.read_contact(id=id)

    @apimethod
    def delete_contact(
        self,
        *,
        id: ResourceID,
    ) -> None:
        self._db.delete_item(f"contacts/{id}")
        return None

    @apimethod
    def upload_picture(
        self,
        *,
        id: ResourceID,
        format: ImageFormat,
        length: int,
    ) -> Upload:
        return self._mem.presign_put(
            f"uploads/contacts/{id}/picture.{format}",
            content_type=format.content_type,
            content_length=length,
            max_seconds=5 * 60,
        )

    # ──── Private Methods ────

    @cached_property
    def default_picture(self) -> HttpUrl:
        return self._mem.get_url("contacts/default/picture.jxl")
