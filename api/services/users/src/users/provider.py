import base64
from dataclasses import dataclass
from typing import Any, Iterable

from shared.config import GrantSpec, is_set, missing, settings
from shared.http import Role
from shared.providers import BaseProvider, apimethod
from shared.providers.idp import IdentityProvider, User, UserPage
from shared.providers.mem import StorageProvider, UploadURL

__all__ = [
    "User",
    "UserPage",
    "UserCredentials",
    "UploadURL",
    "UserProvider",
]


@dataclass(frozen=True, slots=True)
class UserCredentials:
    id: str
    name: str
    password: str


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
    ) -> UserPage:
        return self._idp.list_users(
            limit=limit,
            cursor=cursor if is_set(cursor) else None,
        )

    @apimethod
    def create_user(
        self,
        *,
        id: str,
        name: str,
        password: str,
        role: Role,
        enabled: bool,
    ) -> UserCredentials:
        self._idp.create_user(
            username=f"id:{id}",
            preferred_username=f"name:{self._encode(name)}",
            password=password,
            id=id,
            name=name,
            picture=None,
            role=role.value,
            enabled=enabled,
        )
        return UserCredentials(
            id=id,
            name=name,
            password=password,
        )

    @apimethod
    def read_user(
        self,
        *,
        id: str,
    ) -> User:
        return self._idp.read_user(
            username=f"id:{id}",
        )

    @apimethod
    def update_user(
        self,
        *,
        id: str,
        name: str | missing,
        picture: None | missing,
        role: Role | missing,
        enabled: bool | missing,
    ) -> User:
        attrs: dict[str, Any] = {}
        if is_set(name):
            attrs["preferred_username"] = f"name:{self._encode(name)}"
            attrs["name"] = name
        if is_set(picture):
            attrs["picture"] = picture
        if is_set(role):
            attrs["role"] = role.value
        if is_set(enabled):
            attrs["enabled"] = enabled
        return self._idp.update_user(
            username=f"id:{id}",
            **attrs,
        )

    @apimethod
    def delete_user(
        self,
        *,
        id: str,
    ) -> None:
        return self._idp.delete_user(
            username=f"id:{id}",
        )

    @apimethod
    def upload_picture(
        self,
        *,
        id: str,
        content_type: str,
        max_bytes: int,
        max_seconds: int,
    ) -> UploadURL:
        return self._mem.presign_post(
            f"users/{id}/picture.jxl",
            content_type=content_type,
            max_bytes=max_bytes,
            max_seconds=max_seconds,
        )

    @apimethod
    def reset_user(
        self,
        *,
        id: str,
        password: str,
    ) -> UserCredentials:
        self._idp.reset_user(
            username=f"id:{id}",
            password=password,
        )
        return UserCredentials(
            id=id,
            name=self.read_user(id=id).attributes.get("name") or "",
            password=password,
        )

    # ──── Private Methods ────

    @staticmethod
    def _encode(name: str) -> str:
        return base64.b64encode(name.encode()).decode("ascii")
