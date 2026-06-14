from typing import Protocol

import boto3
from shared.abc import BaseProvider, ExceptionMap, Role, private_api
from shared.config import settings
from shared.errors import DomainForbidden, DomainNotFound, DomainRateLimited
from shared.providers.cognito import encode_id, encode_name
from types_boto3_cognito_idp import CognitoIdentityProviderClient
from types_boto3_cognito_idp.type_defs import AttributeTypeTypeDef
from types_boto3_s3 import S3Client

from .models import Provider

__all__ = [
    "UserProvider",
    "CognitoUserProvider",
]


# ──── User Protocol ───────────────────────────────────────────────────────────────────


class UserProvider(Protocol):
    def list_users(
        self,
        *,
        q: str | None,
        limit: int,
        cursor: str | None,
    ) -> Provider.Page: ...

    def create_user(
        self,
        *,
        id: str,
        name: str,
        password: str,
        role: Role,
        enabled: bool,
    ) -> Provider.Credentials: ...

    def read_user(
        self,
        *,
        id: str,
    ) -> Provider.User: ...

    def update_user(
        self,
        *,
        id: str,
        name: str | None,
        role: Role | None,
        enabled: bool | None,
    ) -> Provider.User: ...

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
    ) -> Provider.UploadForm: ...

    def reset_user(
        self,
        *,
        id: str,
        password: str,
    ) -> Provider.Credentials: ...


# ──── AWS User Provider ───────────────────────────────────────────────────────────────


class CognitoUserProvider(BaseProvider):
    _cognito: CognitoIdentityProviderClient
    _pool_id: str
    _s3: S3Client
    _bucket: str
    _bucket_url: str

    def __init__(
        self,
        *,
        region: str | None = None,
        user_pool_id: str | None = None,
        user_bucket: str | None = None,
    ) -> None:
        region = region or settings.aws_region
        self._cognito = boto3.client("cognito-idp", region_name=region)
        self._pool_id = user_pool_id or settings.cognito_user_pool_id
        self._s3 = boto3.client("s3", region_name=region)
        self._bucket = user_bucket or settings.s3_user_bucket
        self._bucket_url = f"https://{self._bucket}.s3.{region}.amazonaws.com"

    @property
    def _exception_map(self) -> ExceptionMap:
        cx = self._cognito.exceptions
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

    # ──── Private APIs ────

    @private_api
    def list_users(
        self,
        *,
        q: str | None,
        limit: int,
        cursor: str | None,
    ) -> Provider.Page:
        return Provider.Page.from_cognito(
            self._cognito.list_users(
                UserPoolId=self._pool_id,
                Limit=limit,
                **({"Filter": f'name ^= "{q}"'} if q else {}),
                **({"PaginationToken": cursor} if cursor else {}),
            )
        )

    @private_api
    def create_user(
        self,
        *,
        id: str,
        name: str,
        password: str,
        role: Role,
        enabled: bool,
    ) -> Provider.Credentials:
        xid = encode_id(id)
        self._cognito.admin_create_user(
            UserPoolId=self._pool_id,
            Username=xid,
            UserAttributes=[
                {"Name": "preferred_username", "Value": encode_name(name)},
                {"Name": "name", "Value": name},
                {
                    "Name": "picture",
                    "Value": f"{self._bucket_url}/users/{id}/picture.jxl",
                },
                {"Name": "custom:role", "Value": role.value},
            ],
            MessageAction="SUPPRESS",
        )
        self._cognito.admin_set_user_password(
            UserPoolId=self._pool_id,
            Username=xid,
            Password=password,
            Permanent=False,
        )
        self._s3.copy_object(
            Bucket=self._bucket,
            Key=f"users/{id}/picture.jxl",
            CopySource={
                "Bucket": self._bucket,
                "Key": "users/default/picture.jxl",
            },
        )
        if not enabled:
            self._cognito.admin_disable_user(
                UserPoolId=self._pool_id,
                Username=xid,
            )
        return Provider.Credentials(
            id=id,
            name=name,
            password=password,
        )

    @private_api
    def read_user(
        self,
        *,
        id: str,
    ) -> Provider.User:
        return Provider.User.from_cognito(
            self._cognito.admin_get_user(
                UserPoolId=self._pool_id,
                Username=encode_id(id),
            )
        )

    @private_api
    def update_user(
        self,
        *,
        id: str,
        name: str | None,
        role: Role | None,
        enabled: bool | None,
    ) -> Provider.User:
        xid = encode_id(id)
        if name is not None or role is not None:
            attrs: list[AttributeTypeTypeDef] = []
            if name is not None:
                attrs.append({"Name": "preferred_username", "Value": encode_name(name)})
                attrs.append({"Name": "name", "Value": name})
            if role is not None:
                attrs.append({"Name": "custom:role", "Value": role.value})
            self._cognito.admin_update_user_attributes(
                UserPoolId=self._pool_id,
                Username=xid,
                UserAttributes=attrs,
            )
        if enabled is not None:
            if enabled:
                self._cognito.admin_enable_user(
                    UserPoolId=self._pool_id,
                    Username=xid,
                )
            else:
                self._cognito.admin_disable_user(
                    UserPoolId=self._pool_id,
                    Username=xid,
                )
        return self.read_user(id=id)

    @private_api
    def delete_user(
        self,
        *,
        id: str,
    ) -> None:
        self._cognito.admin_delete_user(
            UserPoolId=self._pool_id,
            Username=encode_id(id),
        )
        return None

    @private_api
    def generate_upload_form(
        self,
        *,
        id: str,
        content_type: str,
        max_bytes: int,
        max_seconds: int,
    ) -> Provider.UploadForm:
        return Provider.UploadForm.from_cognito(
            self._s3.generate_presigned_post(
                Bucket=self._bucket,
                Key=f"users/{id}/picture.jxl",
                Fields={"Content-Type": content_type},
                Conditions=[
                    {"Content-Type": content_type},
                    ["content-length-range", 1, max_bytes],
                ],
                ExpiresIn=max_seconds,
            )
        )

    @private_api
    def reset_user(
        self,
        *,
        id: str,
        password: str,
    ) -> Provider.Credentials:
        xid = encode_id(id)
        self._cognito.admin_set_user_password(
            UserPoolId=self._pool_id,
            Username=xid,
            Password=password,
            Permanent=False,
        )
        self._cognito.admin_set_user_mfa_preference(
            UserPoolId=self._pool_id,
            Username=xid,
            SoftwareTokenMfaSettings={
                "Enabled": False,
                "PreferredMfa": False,
            },
        )
        self._cognito.admin_user_global_sign_out(
            UserPoolId=self._pool_id,
            Username=xid,
        )
        return Provider.Credentials(
            id=id,
            name=self.read_user(id=id).name,
            password=password,
        )
