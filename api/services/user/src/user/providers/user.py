from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Mapping, NotRequired, Protocol, Sequence, TypedDict, overload

import boto3
from shared.abc import BaseProvider, DataModel, ExceptionMap, private_api
from shared.config import settings
from shared.errors import (
    DomainForbidden,
    DomainInvariantViolation,
    DomainNotFound,
    DomainRateLimited,
    assert_unreachable,
)
from types_boto3_cognito_idp import CognitoIdentityProviderClient

__all__ = [
    "User",
    "UserPage",
    "UserProvider",
    "CognitoUserProvider",
]

# ──── User Models ─────────────────────────────────────────────────────────────────────


class User(DataModel, frozen=True):
    class Role(StrEnum):
        USER = "user"
        ADMIN = "admin"

    class Update(TypedDict):
        name: NotRequired[str]
        role: NotRequired["User.Role"]
        enabled: NotRequired[bool]

    id: str
    name: str
    role: Role
    enabled: bool
    created_at: datetime
    updated_at: datetime | None = None
    last_login_at: datetime | None = None


class UserPage(DataModel, frozen=True):
    users: Sequence[User]
    cursor: str | None = None


# ──── User Protocol ───────────────────────────────────────────────────────────────────


class UserProvider(Protocol):
    def list_users(
        self,
        *,
        q: str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> UserPage: ...

    def get_user(
        self,
        *,
        id: str,
    ) -> User: ...

    def update_user(
        self,
        *,
        id: str,
        update: User.Update,
    ) -> User: ...


# ──── AWS User Provider ───────────────────────────────────────────────────────────────


class CognitoUserProvider(BaseProvider):
    _client: CognitoIdentityProviderClient
    _user_pool_id: str

    def __init__(
        self,
        *,
        region: str | None = None,
        user_pool_id: str | None = None,
    ) -> None:
        region = region or settings.aws_region
        self._client = boto3.client("cognito-idp", region_name=region)
        self._user_pool_id = user_pool_id or settings.cognito_user_pool_id

    @property
    def _exception_map(self) -> ExceptionMap:
        cx = self._client.exceptions
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

    # ──── Helper Methods ────

    def _attrs(self, response: Mapping[str, Any]) -> dict[str, Any]:
        attrs = response.get("UserAttributes", response.get("Attributes", []))
        return {
            attr["Name"]: attr["Value"]
            for attr in attrs
            if "Name" in attr and "Value" in attr
        }

    def _role(self, id: str) -> User.Role:
        response = self._client.admin_list_groups_for_user(
            UserPoolId=self._user_pool_id,
            Username=id,
        )
        return (
            User.Role.ADMIN
            if any(grp.get("GroupName") == "admin" for grp in response["Groups"])
            else User.Role.USER
        )

    @overload
    def _dt(self, value: datetime) -> datetime: ...
    @overload
    def _dt(self, value: None) -> None: ...
    def _dt(self, value: datetime | None) -> datetime | None:
        match value:
            case datetime() as dt:
                return dt.astimezone(timezone.utc)
            case None:
                return None
            case _ as never:
                assert_unreachable(never)

    def _user(self, response: Mapping[str, Any]) -> User:
        match response:
            case {
                "Username": str(id),
                "Enabled": bool(enabled),
                "UserCreateDate": datetime() as created_at,
                "UserLastModifiedDate": datetime() as updated_at,
            }:
                attrs = self._attrs(response)
                return User(
                    id=id,
                    name=attrs["preferred_username"],
                    role=self._role(id),
                    enabled=enabled,
                    created_at=self._dt(created_at),
                    updated_at=self._dt(updated_at),
                    last_login_at=self._dt(attrs.get("custom:last_login_at")),
                )
        raise DomainInvariantViolation(f"Unexpected cognito response: {response}")

    def _page(self, response: Mapping[str, Any]) -> UserPage:
        return UserPage(
            users=[self._user(raw) for raw in response.get("Users", [])],
            cursor=response.get("PaginationToken"),
        )

    # ──── Private APIs ────

    @private_api
    def list_users(
        self,
        *,
        q: str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> UserPage:
        q = q.replace("\\", "\\\\").replace('"', '\\"') if q else None
        return self._page(
            self._client.list_users(
                UserPoolId=self._user_pool_id,
                Limit=min(limit or 25, 60),
                **({"Filter": f'preferred_username ^= "{q}"'} if q else {}),
                **({"PaginationToken": cursor} if cursor else {}),
            )
        )

    @private_api
    def get_user(
        self,
        *,
        id: str,
    ) -> User:
        return self._user(
            self._client.admin_get_user(
                UserPoolId=self._user_pool_id,
                Username=id,
            )
        )

    @private_api
    def update_user(
        self,
        *,
        id: str,
        update: User.Update,
    ) -> User:
        if "name" in update:
            self._client.admin_update_user_attributes(
                UserPoolId=self._user_pool_id,
                Username=id,
                UserAttributes=[
                    {
                        "Name": "preferred_username",
                        "Value": update["name"],
                    },
                ],
            )

        if "role" in update:
            match update["role"]:
                case User.Role.USER:
                    self._client.admin_remove_user_from_group(
                        UserPoolId=self._user_pool_id,
                        Username=id,
                        GroupName="admin",
                    )
                case User.Role.ADMIN:
                    self._client.admin_add_user_to_group(
                        UserPoolId=self._user_pool_id,
                        Username=id,
                        GroupName="admin",
                    )

        if "enabled" in update:
            match update["enabled"]:
                case True:
                    self._client.admin_enable_user(
                        UserPoolId=self._user_pool_id,
                        Username=id,
                    )
                case False:
                    self._client.admin_disable_user(
                        UserPoolId=self._user_pool_id,
                        Username=id,
                    )

        return self.get_user(id=id)
