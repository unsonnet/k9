from collections.abc import Iterable

from pydantic import BaseModel, HttpUrl
from pydantic.networks import EmailStr
from pydantic_extra_types.phone_numbers import PhoneNumber
from shared.config import GrantSpec, is_set, missing, settings
from shared.http import ImageMIMEType
from shared.providers import BaseProvider, apimethod
from shared.providers.database import DatabaseProvider, DatabaseTypes
from shared.providers.storage import StorageProvider, UploadURL

__all__ = [
    "Contact",
    "UploadURL",
    "CompanyContactProvider",
]


class Contact(BaseModel, frozen=True):
    id: str
    name: str
    title: str | None
    picture: HttpUrl | None
    email: EmailStr | None
    phone: PhoneNumber | None


class CompanyContactProvider(BaseProvider):
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
        id: str,
        sid: str,
        name: str,
        title: str | None,
        email: EmailStr | None,
        phone: PhoneNumber | None,
    ) -> Contact:
        return Contact.model_validate(
            self._db.create_item(
                type="company.contact",
                id=f"{id}.{sid}",
                name=name,
                title=title,
                picture=None,
                email=email,
                phone=phone,
            )
        )

    @apimethod
    def read_contact(
        self,
        *,
        id: str,
        sid: str,
    ) -> Contact:
        return Contact.model_validate(
            self._db.read_item(
                type="company.contact",
                id=f"{id}.{sid}",
            )
        )

    @apimethod
    def update_contact(
        self,
        *,
        id: str,
        sid: str,
        name: str | missing,
        title: str | None | missing,
        picture: None | missing,
        email: EmailStr | None | missing,
        phone: PhoneNumber | None | missing,
    ) -> Contact:
        attrs: dict[str, DatabaseTypes] = {}
        if is_set(name):
            attrs["name"] = name
        if is_set(title):
            attrs["title"] = title
        if is_set(picture):
            attrs["picture"] = picture
        if is_set(email):
            attrs["email"] = email
        if is_set(phone):
            attrs["phone"] = phone
        return Contact.model_validate(
            self._db.update_item(
                type="company.contact",
                id=f"{id}.{sid}",
                **attrs,
            )
        )

    @apimethod
    def delete_contact(
        self,
        *,
        id: str,
        sid: str,
    ) -> None:
        self._db.delete_item(
            type="company.contact",
            id=f"{id}.{sid}",
        )
        return None

    @apimethod
    def upload_picture(
        self,
        *,
        id: str,
        sid: str,
        content_type: ImageMIMEType,
        max_bytes: int,
        max_seconds: int,
    ) -> UploadURL:
        return self._mem.presign_post(
            f"companies/{id}/contacts/{sid}/picture.jxl",
            content_type=content_type.value,
            max_bytes=max_bytes,
            max_seconds=max_seconds,
        )
