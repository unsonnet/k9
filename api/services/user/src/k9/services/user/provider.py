import base64
from functools import cached_property
from typing import Iterable

from k9.providers.base import BaseProvider, GrantSpec, apimethod
from k9.providers.config import settings
from k9.providers.identity import IdentityProvider
from k9.providers.storage import HttpUrl, StorageProvider, UploadForm
from k9.resolvers.http.requests import ImageFormat
from k9.types.base import Page
from k9.types.common import Name, Password, Role, UserID, is_set, missing
from k9.types.user import Credentials, User

__all__ = [
    "UserProvider",
]


class UserProvider(BaseProvider):
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
    def list_users(
        self,
        *,
        limit: int,
        cursor: str | missing,
    ) -> Page[User]:
        return self._idp.list_users(
            limit=limit,
            cursor=cursor if is_set(cursor) else None,
        ).hydrate(User)

    @apimethod
    def create_user(
        self,
        *,
        id: UserID,
        role: Role,
        name: Name,
        password: Password,
        enabled: bool,
    ) -> Credentials:
        self._idp.create_user(
            username=f"id:{id}",
            password=password,
            enabled=enabled,
            id=id,
            preferred_username=f"name:{self._encode(name)}",
            name=name,
            picture=str(self.default_picture),
            role=role,
        )
        return Credentials(
            id=id,
            name=name,
            password=password,
        )

    @apimethod
    def read_user(
        self,
        *,
        id: UserID,
    ) -> User:
        return User.model_validate(
            self._idp.read_user(
                username=f"id:{id}",
            )
        )

    @apimethod
    def update_user(
        self,
        *,
        id: UserID,
        role: Role | missing,
        name: Name | missing,
        picture: None | missing,
        enabled: bool | missing,
    ) -> User:
        attrs: dict[str, str | None] = {}
        if is_set(name):
            attrs["preferred_username"] = f"name:{self._encode(name)}"
            attrs["name"] = name
        if is_set(picture):
            attrs["picture"] = str(self.default_picture)
        if is_set(role):
            attrs["role"] = role
        return User.model_validate(
            self._idp.update_user(
                username=f"id:{id}",
                enabled=enabled,
                **attrs,
            )
        )

    @apimethod
    def delete_user(
        self,
        *,
        id: UserID,
    ) -> None:
        return self._idp.delete_user(
            username=f"id:{id}",
        )

    @apimethod
    def upload_picture(
        self,
        *,
        id: UserID,
        format: ImageFormat,
        length: int,
    ) -> UploadForm:
        return self._mem.presign_put(
            f"uploads/users/{id}/picture.{format}",
            content_type=format.content_type,
            content_length=length,
            max_seconds=5 * 60,
        )

    @apimethod
    def reset_user(
        self,
        *,
        id: UserID,
        password: Password,
    ) -> Credentials:
        self._idp.reset_user(
            username=f"id:{id}",
            password=password,
        )
        return Credentials(
            id=id,
            name=self.read_user(id=id).name,
            password=password,
        )

    # ──── Private Methods ────

    @staticmethod
    def _encode(name: str) -> str:
        return base64.b64encode(name.encode()).decode("ascii")

    @cached_property
    def default_picture(self) -> HttpUrl:
        return self._mem.get_url("users/default/picture.jxl")
