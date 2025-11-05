#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import secrets
import string
from abc import ABC, abstractmethod
from typing import Any, Final, Mapping, NoReturn
from uuid import UUID

from config import boto3_client, settings
from models.shared.types import (
    NonEmptyStr,
    PasswordStr,
    PrefValueStr,
    RoleStr,
    UsernameStr,
    PhoneStr,
)
from models.shared.base import TimeStamped
from models.domain.auth import AuthContext
from models.domain.user import UserEntity, UserCreationResult, ListUsersResult
from utils.errors import (
    DomainError,
    DomainConflict,
    DomainInvariantViolation,
    DomainNotFound,
    DomainRateLimited,
    DomainUnauthorized,
    DomainUserDisabled,
)


# ──────────────────────────────────────────────────────────────────────────────
# User Provider
# ──────────────────────────────────────────────────────────────────────────────
class UserDBProvider(ABC):
    """Manage user data contracts for backends."""

    @abstractmethod
    def is_admin(self, ctx: AuthContext) -> bool:
        """Check if requester has admin privileges."""
        ...

    @abstractmethod
    def is_self(self, ctx: AuthContext, *, uid: UUID) -> bool:
        """Check if requester is the same user."""
        ...

    @abstractmethod
    def get_user(self, *, uid: UUID) -> UserEntity:
        """Get user by ID."""
        ...

    @abstractmethod
    def post_user(
        self,
        *,
        username: UsernameStr,
        name: NonEmptyStr,
        phone: PhoneStr,
        role: RoleStr,
        preferences: Mapping[str, str] | None = None,
    ) -> UserCreationResult:
        """Create new user."""
        ...

    @abstractmethod
    def put_user(self, *, user: UserEntity) -> UserEntity:
        """Replace user record."""
        ...

    @abstractmethod
    def delete_user(self, *, uid: UUID) -> None:
        """Delete user record."""
        ...

    @abstractmethod
    def list_users(
        self, *, limit: int | None, next_token: str | None
    ) -> ListUsersResult:
        """List user records."""
        ...

    @abstractmethod
    def update_password(self, *, uid: UUID, new_password: PasswordStr) -> None:
        """Update user password."""
        ...


# ──────────────────────────────────────────────────────────────────────────────
# Disabled Provider
# ──────────────────────────────────────────────────────────────────────────────
class _NoopUserDBProvider(UserDBProvider):
    """Manage user operations as a disabled provider."""

    _MSG: Final = "Failed to perform user operation."

    def _raise(self) -> NoReturn:
        raise DomainInvariantViolation(self._MSG)

    def is_admin(self, *_, **__) -> bool:
        self._raise()

    def is_self(self, *_, **__) -> bool:
        self._raise()

    def get_user(self, *_, **__) -> UserEntity:
        self._raise()

    def post_user(self, *_, **__) -> UserCreationResult:
        self._raise()

    def put_user(self, *_, **__) -> UserEntity:
        self._raise()

    def delete_user(self, *_, **__) -> None:
        self._raise()

    def list_users(self, *_, **__) -> ListUsersResult:
        self._raise()

    def update_password(self, *_, **__) -> None:
        self._raise()


# ──────────────────────────────────────────────────────────────────────────────
# Cognito Provider
# ──────────────────────────────────────────────────────────────────────────────
class CognitoUserDBProvider(UserDBProvider):
    """Manage user data using AWS Cognito."""

    NAME_ATTR: Final = "name"
    PHONE_ATTR: Final = "phone_number"
    ROLE_ATTR: Final = "custom:role"
    PREF_PREFIX: Final = "custom:pref_"

    def __init__(self) -> None:
        cfg = settings()
        if not (
            cfg.cognito_user_pool_id
            and cfg.cognito_client_id
            and cfg.cognito_client_secret
        ):
            raise DomainInvariantViolation("Failed to initialize user provider.")
        self.user_pool_id: str = cfg.cognito_user_pool_id
        self.client_id: str = cfg.cognito_client_id
        self._cognito = boto3_client("cognito-idp")

    # ─────────── Helpers ───────────
    @staticmethod
    def _decode_sub(attrs: Mapping[str, str]) -> UUID:
        return UUID(attrs["sub"])

    @staticmethod
    def _attrs_from_user(user: Mapping[str, Any]) -> dict[str, str]:
        ua = user.get("UserAttributes", user.get("Attributes", []))
        return {a["Name"]: str(a.get("Value", "")) for a in ua if "Name" in a}

    def _attrs_from_ctx(self, ctx: AuthContext) -> dict[str, str]:
        return self._attrs_from_user(
            self._cognito.get_user(AccessToken=str(ctx.bearer_token))
        )

    def _to_profile(self, u: Mapping[str, Any]) -> UserEntity:
        attrs = self._attrs_from_user(u)
        return UserEntity(
            id=self._decode_sub(attrs),
            username=str(u["Username"]),
            name=attrs[self.NAME_ATTR],
            phone=attrs[self.PHONE_ATTR],
            role=attrs[self.ROLE_ATTR],
            preferences={
                k[len(self.PREF_PREFIX) :]: v
                for k, v in attrs.items()
                if k.startswith(self.PREF_PREFIX)
            },
            created_at=u["UserCreateDate"],
            updated_at=u.get("UserLastModifiedDate"),
        )

    def _username_for(self, uid: UUID) -> str:
        try:
            r = self._cognito.list_users(
                UserPoolId=self.user_pool_id,
                Filter=f'sub = "{uid}"',
                Limit=1,
            )
            u = r.get("Users", [])
            if not u:
                raise self._cognito.exceptions.UserNotFoundException({}, "UserNotFound")
            return str(u[0]["Username"])
        except Exception as e:
            self._handle_error(e, "Failed to resolve username.")

    def _get_user(self, uid: UUID) -> dict[str, Any]:
        try:
            return self._cognito.admin_get_user(
                UserPoolId=self.user_pool_id,
                Username=self._username_for(uid),
            )
        except Exception as e:
            self._handle_error(e, "Failed to fetch user.")

    @staticmethod
    def _password() -> str:
        u, l, d, s = (
            string.ascii_uppercase,
            string.ascii_lowercase,
            string.digits,
            "!@#$%^&*",
        )
        base = [secrets.choice(x) for x in (u, l, d, s)]
        all_chars = u + l + d + s
        base += [secrets.choice(all_chars) for _ in range(12)]
        secrets.SystemRandom().shuffle(base)
        return "".join(base)

    def _handle_error(self, e: Exception, msg: str) -> NoReturn:
        c = self._cognito.exceptions
        m: dict[type[Exception], type[DomainError]] = {
            c.UserNotFoundException: DomainNotFound,
            c.UsernameExistsException: DomainConflict,
            c.AliasExistsException: DomainConflict,
            c.NotAuthorizedException: DomainUnauthorized,
            c.UserNotConfirmedException: DomainUserDisabled,
            c.TooManyRequestsException: DomainRateLimited,
            c.LimitExceededException: DomainRateLimited,
            c.InvalidParameterException: DomainUnauthorized,
            c.InternalErrorException: DomainInvariantViolation,
        }
        raise m.get(type(e), DomainInvariantViolation)(msg) from e

    # ─────────── Contract Methods ───────────
    def is_admin(self, ctx: AuthContext) -> bool:
        """Check if requester has admin privileges."""
        try:
            return self._attrs_from_ctx(ctx)[self.ROLE_ATTR] == settings().admin_role
        except Exception as e:
            self._handle_error(e, "Failed to check role.")

    def is_self(self, ctx: AuthContext, *, uid: UUID) -> bool:
        """Check if requester is the same user."""
        try:
            return self._decode_sub(self._attrs_from_ctx(ctx)) == uid
        except Exception as e:
            self._handle_error(e, "Failed to check role.")

    def get_user(self, *, uid: UUID) -> UserEntity:
        """Retrieve user by id."""
        return self._to_profile(self._get_user(uid))

    def post_user(
        self,
        *,
        username: UsernameStr,
        name: NonEmptyStr,
        phone: PhoneStr,
        role: RoleStr,
        preferences: Mapping[str, PrefValueStr] | None = None,
    ) -> UserCreationResult:
        """Create user record."""
        try:
            attrs = [
                {"Name": self.NAME_ATTR, "Value": name},
                {"Name": self.PHONE_ATTR, "Value": phone},
                {"Name": self.ROLE_ATTR, "Value": role},
                *(
                    {"Name": f"{self.PREF_PREFIX}{k}", "Value": v}
                    for k, v in (preferences or {}).items()
                ),
            ]
            p = self._password()
            self._cognito.admin_create_user(
                UserPoolId=self.user_pool_id,
                Username=str(username),
                UserAttributes=attrs,
                TemporaryPassword=p,
                MessageAction="SUPPRESS",
            )
            return UserCreationResult(username=username, temporary_password=p)
        except Exception as e:
            self._handle_error(e, "Failed to create user.")

    def put_user(self, *, user: UserEntity) -> UserEntity:
        """Replace user record."""
        try:
            u = self._get_user(user.id)
            self._cognito.admin_update_user_attributes(
                UserPoolId=self.user_pool_id,
                Username=str(u["Username"]),
                UserAttributes=[
                    {"Name": self.NAME_ATTR, "Value": user.name},
                    {"Name": self.PHONE_ATTR, "Value": user.phone},
                    {"Name": self.ROLE_ATTR, "Value": user.role},
                    *(
                        {"Name": f"{self.PREF_PREFIX}{k}", "Value": v}
                        for k, v in user.preferences.items()
                    ),
                ],
            )
            return self.get_user(uid=user.id)
        except Exception as e:
            self._handle_error(e, "Failed to update user.")

    def delete_user(self, *, uid: UUID) -> None:
        """Delete user record."""
        try:
            self._cognito.admin_delete_user(
                UserPoolId=self.user_pool_id,
                Username=self._username_for(uid),
            )
        except Exception as e:
            self._handle_error(e, "Failed to delete user.")

    def list_users(
        self, *, limit: int | None, next_token: str | None
    ) -> ListUsersResult:
        """List user records."""
        try:
            total = int(
                self._cognito.describe_user_pool(UserPoolId=self.user_pool_id)[
                    "UserPool"
                ]["EstimatedNumberOfUsers"]
            )
            params = {"UserPoolId": self.user_pool_id, "Limit": limit or 25}
            if next_token is not None:
                params["PaginationToken"] = next_token
            r = self._cognito.list_users(**params)
            return ListUsersResult(
                total=r.get("total", 0),
                users=[self._to_profile(u) for u in r.get("Users", [])],
                next_token=r.get("PaginationToken"),
            )
        except Exception as e:
            self._handle_error(e, "Failed to list users.")

    def update_password(self, *, uid: UUID, new_password: PasswordStr) -> None:
        """Update user password."""
        try:
            self._cognito.admin_set_user_password(
                UserPoolId=self.user_pool_id,
                Username=self._username_for(uid),
                Password=str(new_password),
                Permanent=True,
            )
        except Exception as e:
            self._handle_error(e, "Failed to update password.")
