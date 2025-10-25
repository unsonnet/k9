#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Mapping, NoReturn
from uuid import UUID
import secrets
import string

from config import boto3_client, settings
from models.common import (
    NonEmptyStr,
    PasswordStr,
    PrefValueStr,
    RoleStr,
    UsernameStr,
    PhoneStr,
)
from models.auth import AuthContext
from models.user import StoredProfile, ListUsersResult, CreateUserResult
from ..errors import (
    DomainInvariantViolation,
    DomainNotFound,
    DomainUnauthorized,
    DomainRateLimited,
    DomainUserDisabled,
    DomainConflict,
)


# ──────────────────────────────────────────────────────────────────────────────
# Interface Definition
# ──────────────────────────────────────────────────────────────────────────────
class UserDBProvider(ABC):

    @abstractmethod
    def is_admin(self, ctx: AuthContext) -> bool: ...

    @abstractmethod
    def is_self(self, ctx: AuthContext, *, uid: UUID) -> bool: ...

    @abstractmethod
    def get_user(self, *, uid: UUID) -> StoredProfile: ...

    @abstractmethod
    def post_user(
        self,
        *,
        username: UsernameStr,
        name: NonEmptyStr,
        phone: PhoneStr,
        role: RoleStr,
        preferences: Mapping[str, PrefValueStr] | None,
    ) -> CreateUserResult: ...

    @abstractmethod
    def put_user(self, *, user: StoredProfile) -> StoredProfile: ...

    @abstractmethod
    def delete_user(self, *, uid: UUID) -> None: ...

    @abstractmethod
    def list_users(
        self, *, limit: int | None, next_token: str | None
    ) -> ListUsersResult: ...

    @abstractmethod
    def update_password(
        self,
        *,
        uid: UUID,
        new_password: PasswordStr,
    ) -> None: ...


# ──────────────────────────────────────────────────────────────────────────────
# Default Null Provider
# ──────────────────────────────────────────────────────────────────────────────
class _NoopUserDBProvider(UserDBProvider):
    def _raise(self) -> NoReturn:
        raise DomainInvariantViolation("User provider not configured.")

    def is_admin(self, *_, **__) -> bool:
        self._raise()  # type: ignore

    def is_self(self, *_, **__) -> bool:
        self._raise()  # type: ignore

    def get_user(self, *_, **__) -> StoredProfile:
        self._raise()  # type: ignore

    def post_user(self, *_, **__) -> CreateUserResult:
        self._raise()  # type: ignore

    def put_user(self, *_, **__) -> StoredProfile:
        self._raise()  # type: ignore

    def delete_user(self, *_, **__) -> None:
        self._raise()

    def list_users(self, *_, **__) -> ListUsersResult:
        self._raise()  # type: ignore

    def update_password(self, *_, **__) -> None:
        self._raise()


# ──────────────────────────────────────────────────────────────────────────────
# Cognito-backed Provider
# ──────────────────────────────────────────────────────────────────────────────
class CognitoUserDBProvider(UserDBProvider):
    NAME_ATTR = "name"
    PHONE_ATTR = "phone_number"
    ROLE_ATTR = "custom:role"
    PREF_PREFIX = "custom:pref_"

    def __init__(self) -> None:
        cfg = settings()
        if not cfg.cognito_user_pool_id or not cfg.cognito_client_id:
            raise DomainInvariantViolation("Cognito configuration incomplete.")

        self.user_pool_id = cfg.cognito_user_pool_id
        self.client_id = cfg.cognito_client_id
        self._cognito = boto3_client("cognito-idp")

    # ─────────── Helpers ───────────
    @staticmethod
    def _decode_sub(attrs: dict[str, str]) -> UUID:
        sub = attrs.get("sub")
        if not sub:
            raise DomainInvariantViolation("Missing `sub` attribute.")
        try:
            return UUID(sub)
        except ValueError:
            raise DomainInvariantViolation("Invalid `sub` UUID.")

    @staticmethod
    def _to_profile(user: dict) -> StoredProfile:
        attrs = {a["Name"]: a.get("Value", "") for a in user.get("UserAttributes", [])}
        uid = CognitoUserDBProvider._decode_sub(attrs)

        prefs = {
            k[len(CognitoUserDBProvider.PREF_PREFIX) :]: v
            for k, v in attrs.items()
            if k.startswith(CognitoUserDBProvider.PREF_PREFIX)
        }

        return StoredProfile(
            id=uid,
            username=user["Username"],
            name=attrs.get("name") or "",
            phone=attrs.get(CognitoUserDBProvider.PHONE_ATTR) or "",
            role=attrs.get(CognitoUserDBProvider.ROLE_ATTR, "user"),
            preferences=prefs,
            createdAt=user.get("UserCreateDate"),  # type: ignore
            updatedAt=user.get("UserLastModifiedDate"),
        )

    def _get_user_record(self, uid: UUID) -> dict:
        try:
            return self._cognito.admin_get_user(
                UserPoolId=self.user_pool_id,
                Username=str(uid),
            )
        except Exception as e:
            self._handle_error(e, "User lookup failed")

    def _generate_temp_password(self) -> str:
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*()"
        return "".join(secrets.choice(alphabet) for _ in range(16))

    def _handle_error(self, e: Exception, msg: str) -> NoReturn:
        cx = self._cognito.exceptions
        mapping = {
            cx.UserNotFoundException: DomainNotFound(msg),
            cx.UsernameExistsException: DomainConflict("Username already exists."),
            cx.AliasExistsException: DomainConflict("Username already exists."),
            cx.NotAuthorizedException: DomainUnauthorized("Unauthorized."),
            cx.UserNotConfirmedException: DomainUserDisabled("User disabled."),
            cx.TooManyRequestsException: DomainRateLimited("Rate limit exceeded."),
            cx.LimitExceededException: DomainRateLimited("Rate limit exceeded."),
            cx.InvalidParameterException: DomainUnauthorized("Invalid parameters."),
            cx.InternalErrorException: DomainInvariantViolation(
                "Identity provider error."
            ),
        }
        raise mapping.get(type(e), DomainUnauthorized(f"{msg}: {e}"))

    # ─────────── Contract Methods ───────────
    def is_admin(self, ctx: AuthContext) -> bool:
        try:
            resp = self._cognito.get_user(AccessToken=str(ctx.bearerToken))
            for attr in resp.get("UserAttributes", []):
                if attr["Name"] == self.ROLE_ATTR:
                    return attr.get("Value", "") == settings().admin_role
            raise DomainUnauthorized("Missing role attribute on user.")
        except Exception as e:
            self._handle_error(e, "Failed to extract role")

    def is_self(self, ctx: AuthContext, *, uid: UUID) -> bool:
        try:
            resp = self._cognito.get_user(AccessToken=str(ctx.bearerToken))
            attrs = {
                a["Name"]: a.get("Value", "") for a in resp.get("UserAttributes", [])
            }
            current_uid = self._decode_sub(attrs)
            return current_uid == uid
        except Exception as e:
            self._handle_error(e, "Failed to determine user identity")

    def get_user(self, *, uid: UUID) -> StoredProfile:
        record = self._get_user_record(uid)
        return self._to_profile(record)

    def post_user(
        self,
        *,
        username: UsernameStr,
        name: NonEmptyStr,
        phone: PhoneStr,
        role: RoleStr,
        preferences: Mapping[str, PrefValueStr] | None,
    ) -> CreateUserResult:
        attrs = [
            {"Name": self.NAME_ATTR, "Value": name},
            {"Name": self.PHONE_ATTR, "Value": phone},
            {"Name": self.ROLE_ATTR, "Value": role},
        ]
        if preferences:
            attrs.extend(
                {"Name": f"{self.PREF_PREFIX}{k}", "Value": v}
                for k, v in preferences.items()
            )

        try:
            temp_password = self._generate_temp_password()
            self._cognito.admin_create_user(
                UserPoolId=self.user_pool_id,
                Username=str(username),
                UserAttributes=attrs,
                TemporaryPassword=temp_password,
                MessageAction="SUPPRESS",
            )
            return CreateUserResult(
                username=username,
                tempPassword=temp_password,
            )
        except Exception as e:
            self._handle_error(e, "Failed to create user")

    def put_user(self, *, user: StoredProfile) -> StoredProfile:
        try:
            record = self._get_user_record(user.id)
            username = record["Username"]

            attrs = [
                {"Name": "name", "Value": user.name},
                {"Name": self.PHONE_ATTR, "Value": user.phone},
                {"Name": self.ROLE_ATTR, "Value": str(user.role)},
            ]
            attrs.extend(
                {"Name": f"{self.PREF_PREFIX}{k}", "Value": str(v)}
                for k, v in user.preferences.items()
            )

            self._cognito.admin_update_user_attributes(
                UserPoolId=self.user_pool_id,
                Username=username,
                UserAttributes=attrs,
            )
            updated = self._get_user_record(user.id)
            return self._to_profile(updated)
        except Exception as e:
            self._handle_error(e, "Failed to update user")

    def delete_user(self, *, uid: UUID) -> None:
        try:
            record = self._get_user_record(uid)
            self._cognito.admin_delete_user(
                UserPoolId=self.user_pool_id,
                Username=record["Username"],
            )
        except Exception as e:
            self._handle_error(e, "Failed to delete user")

    def list_users(
        self, *, limit: int | None, next_token: str | None
    ) -> ListUsersResult:
        try:
            pool = self._cognito.describe_user_pool(UserPoolId=self.user_pool_id)
            total = int(pool.get("UserPool", {}).get("EstimatedNumberOfUsers", 0))

            resp = self._cognito.list_users(
                UserPoolId=self.user_pool_id,
                Limit=limit or 25,
                PaginationToken=next_token,
            )
            users = [self._to_profile(u) for u in resp.get("Users", [])]

            return ListUsersResult(
                total=total,
                users=users,
                nextToken=resp.get("PaginationToken"),
            )
        except Exception as e:
            self._handle_error(e, "Failed to list users")

    def update_password(
        self,
        *,
        uid: UUID,
        new_password: PasswordStr,
    ) -> None:
        try:
            record = self._get_user_record(uid)
            self._cognito.admin_set_user_password(
                UserPoolId=self.user_pool_id,
                Username=record["Username"],
                Password=str(new_password),
                Permanent=True,
            )
        except Exception as e:
            self._handle_error(e, "Failed to update password")
