import base64
from datetime import datetime
from typing import Any, Iterable, Mapping, Protocol, Sequence

import boto3
from pydantic import HttpUrl
from shared.config import GrantSpec, is_set, missing, settings
from shared.errors import (
    DomainForbidden,
    DomainInvariantViolation,
    DomainNotFound,
    DomainRateLimited,
)
from shared.helpers import dt
from shared.http import Role
from shared.providers import BaseProvider, ExceptionMap, apimethod
from types_boto3_cognito_idp import CognitoIdentityProviderClient
from types_boto3_cognito_idp.type_defs import AttributeTypeTypeDef
from types_boto3_s3.service_resource import Bucket

from .models import Credentials, Page, UploadForm, User, UserSummary

__all__ = [
    "UserProvider",
    "CognitoUserProvider",
]


class UserProvider(Protocol):
    @property
    def permissions(self) -> Iterable[GrantSpec]: ...

    def list_users(
        self,
        *,
        q: str | missing,
        limit: int,
        cursor: str | missing,
    ) -> Page: ...

    def create_user(
        self,
        *,
        id: str,
        name: str,
        password: str,
        role: Role,
        enabled: bool,
    ) -> Credentials: ...

    def read_user(
        self,
        *,
        id: str,
    ) -> User: ...

    def update_user(
        self,
        *,
        id: str,
        name: str | missing,
        role: Role | missing,
        enabled: bool | missing,
    ) -> User: ...

    def delete_user(
        self,
        *,
        id: str,
    ) -> None: ...

    def generate_upload_form(
        self,
        *,
        id: str,
        content_type: str,
        max_bytes: int,
        max_seconds: int,
    ) -> UploadForm: ...

    def reset_user(
        self,
        *,
        id: str,
        password: str,
    ) -> Credentials: ...


# ──── AWS User Provider ───────────────────────────────────────────────────────────────


class CognitoUserProvider(BaseProvider):
    _idp: CognitoIdentityProviderClient
    _idp_pool: str
    _s3: Bucket
    _s3_url: str

    def __init__(
        self,
        *,
        region: str | None = None,
        bucket: str | None = None,
        user_pool_id: str | None = None,
    ) -> None:
        region = region or settings.aws_region
        # cognito idp
        self._idp = boto3.client("cognito-idp", region)
        self._idp_pool = user_pool_id or settings.cognito_user_pool_id
        # s3
        bucket = bucket or settings.s3_bucket
        self._s3 = boto3.resource("s3", region).Bucket(bucket)
        self._s3_url = f"https://{bucket}.s3.{region}.amazonaws.com"

    @property
    def permissions(self) -> Iterable[GrantSpec]:
        yield GrantSpec(
            actions=(
                "cognito-idp:AdminCreateUser",
                "cognito-idp:AdminDeleteUser",
                "cognito-idp:AdminDisableUser",
                "cognito-idp:AdminEnableUser",
                "cognito-idp:AdminGetUser",
                "cognito-idp:AdminSetUserMFAPreference",
                "cognito-idp:AdminSetUserPassword",
                "cognito-idp:AdminUpdateUserAttributes",
                "cognito-idp:AdminUserGlobalSignOut",
                "cognito-idp:ListUsers",
            ),
            resources=("cognito-user-pool",),
        )
        yield GrantSpec(
            actions=(
                "s3:GetObject",
                "s3:PutObject",
            ),
            resources=("s3-bucket",),
        )

    @property
    def _exception_map(self) -> ExceptionMap:
        cx = self._idp.exceptions
        return {
            DomainForbidden: [
                cx.ForbiddenException,
                cx.NotAuthorizedException,
            ],
            DomainRateLimited: [
                cx.TooManyRequestsException,
                cx.LimitExceededException,
            ],
            DomainNotFound: [
                cx.UserNotFoundException,
                cx.ResourceNotFoundException,
            ],
        }

    # ──── Private Methods ────

    @staticmethod
    def _encode_id(id: str) -> str:
        return f"id:{id}"

    @staticmethod
    def _decode_id(xid: str) -> str:
        return xid.removeprefix("id:")

    @staticmethod
    def _encode_name(name: str) -> str:
        return f"name:{base64.b64encode(name.encode()).decode('ascii')}"

    @classmethod
    def _unpack(cls, response: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
        attrs = {attr["Name"]: attr["Value"] for attr in response}
        attrs.setdefault("custom:last_login_at", None)
        return attrs

    @classmethod
    def _user(cls, response: Mapping[str, Any]) -> User:
        response = dict(response)
        response.setdefault("UserLastModifiedDate", None)
        match response:
            case {
                "Username": str(xid),
                "Enabled": bool(enabled),
                "UserCreateDate": datetime() as created_at,
                "UserLastModifiedDate": datetime() | None as updated_at,
                "UserAttributes": list(attrs),
            }:
                match cls._unpack(attrs):
                    case {
                        "name": str(name),
                        "picture": str(picture),
                        "custom:role": Role.USER | Role.ADMIN as role,
                        "custom:last_login_at": str() | None as last_login_at,
                    }:
                        return User(
                            id=cls._decode_id(xid),
                            name=name,
                            picture=HttpUrl(picture),
                            role=Role(role),
                            enabled=enabled,
                            created_at=dt(created_at),
                            updated_at=dt(updated_at),
                            last_login_at=dt(last_login_at, iso=False),
                        )
        raise DomainInvariantViolation(f"Unexpected cognito user: {response}")

    @classmethod
    def _user_summary(cls, response: Mapping[str, Any]) -> UserSummary:
        match dict(response):
            case {"Username": str(xid), "Attributes": list(attrs)}:
                match cls._unpack(attrs):
                    case {"name": str(name), "picture": str(picture)}:
                        return UserSummary(
                            id=cls._decode_id(xid),
                            name=name,
                            picture=HttpUrl(picture),
                        )
        raise DomainInvariantViolation(f"Unexpected cognito user summary: {response}")

    @classmethod
    def _page(cls, response: Mapping[str, Any]) -> Page:
        response = dict(response)
        response.setdefault("PaginationToken", None)
        match response:
            case {"Users": list(users), "PaginationToken": str() | None as cursor}:
                return Page(
                    users=[cls._user_summary(raw) for raw in users],
                    cursor=cursor,
                )
        raise DomainInvariantViolation(f"Unexpected cognito page: {response}")

    @classmethod
    def _upload_form(cls, response: Mapping[str, Any]) -> UploadForm:
        match response:
            case {"url": str(url), "fields": dict(fields)}:
                return UploadForm(
                    url=url,
                    fields=fields,
                )
        raise DomainInvariantViolation(f"Unexpected s3 upload form: {response}")

    # ──── Public Methods ────

    @apimethod
    def list_users(
        self,
        *,
        q: str | missing,
        limit: int,
        cursor: str | missing,
    ) -> Page:
        return self._page(
            self._idp.list_users(
                UserPoolId=self._idp_pool,
                Limit=limit,
                **({"Filter": f'name ^= "{q}"'} if is_set(q) else {}),
                **({"PaginationToken": cursor} if is_set(cursor) else {}),
            )
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
    ) -> Credentials:
        xid = self._encode_id(id)
        xname = self._encode_name(name)
        self._idp.admin_create_user(
            UserPoolId=self._idp_pool,
            Username=xid,
            UserAttributes=[
                {"Name": "preferred_username", "Value": xname},
                {"Name": "name", "Value": name},
                {"Name": "picture", "Value": f"{self._s3_url}/users/{id}/picture.jxl"},
                {"Name": "custom:role", "Value": role.value},
            ],
            MessageAction="SUPPRESS",
        )
        self._idp.admin_set_user_password(
            UserPoolId=self._idp_pool,
            Username=xid,
            Password=password,
            Permanent=False,
        )
        self._s3.copy(
            Key=f"users/{id}/picture.jxl",
            CopySource={
                "Bucket": self._s3.name,
                "Key": "users/default/picture.jxl",
            },
        )
        if not enabled:
            self._idp.admin_disable_user(
                UserPoolId=self._idp_pool,
                Username=xid,
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
        id: str,
    ) -> User:
        return self._user(
            self._idp.admin_get_user(
                UserPoolId=self._idp_pool,
                Username=self._encode_id(id),
            )
        )

    @apimethod
    def update_user(
        self,
        *,
        id: str,
        name: str | missing,
        role: Role | missing,
        enabled: bool | missing,
    ) -> User:
        xid = self._encode_id(id)
        if is_set(name) or is_set(role):
            attrs: list[AttributeTypeTypeDef] = []
            if is_set(name):
                xname = self._encode_name(name)
                attrs.append({"Name": "preferred_username", "Value": xname})
                attrs.append({"Name": "name", "Value": name})
            if is_set(role):
                attrs.append({"Name": "custom:role", "Value": role.value})
            self._idp.admin_update_user_attributes(
                UserPoolId=self._idp_pool,
                Username=xid,
                UserAttributes=attrs,
            )
        if is_set(enabled):
            if enabled:
                self._idp.admin_enable_user(
                    UserPoolId=self._idp_pool,
                    Username=xid,
                )
            else:
                self._idp.admin_disable_user(
                    UserPoolId=self._idp_pool,
                    Username=xid,
                )
        return self.read_user(id=id)

    @apimethod
    def delete_user(
        self,
        *,
        id: str,
    ) -> None:
        self._idp.admin_delete_user(
            UserPoolId=self._idp_pool,
            Username=self._encode_id(id),
        )
        return None

    @apimethod
    def generate_upload_form(
        self,
        *,
        id: str,
        content_type: str,
        max_bytes: int,
        max_seconds: int,
    ) -> UploadForm:
        return self._upload_form(
            self._s3.meta.client.generate_presigned_post(
                Bucket=self._s3.name,
                Key=f"users/{id}/picture.jxl",
                Fields={"Content-Type": content_type},
                Conditions=[
                    {"Content-Type": content_type},
                    ["content-length-range", 1, max_bytes],
                ],
                ExpiresIn=max_seconds,
            )
        )

    @apimethod
    def reset_user(
        self,
        *,
        id: str,
        password: str,
    ) -> Credentials:
        xid = self._encode_id(id)
        self._idp.admin_set_user_password(
            UserPoolId=self._idp_pool,
            Username=xid,
            Password=password,
            Permanent=False,
        )
        self._idp.admin_set_user_mfa_preference(
            UserPoolId=self._idp_pool,
            Username=xid,
            SoftwareTokenMfaSettings={
                "Enabled": False,
                "PreferredMfa": False,
            },
        )
        self._idp.admin_user_global_sign_out(
            UserPoolId=self._idp_pool,
            Username=xid,
        )
        return Credentials(
            id=id,
            name=self.read_user(id=id).name,
            password=password,
        )
