#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Mapping, Sequence, NoReturn
from uuid import UUID
from pydantic import BaseModel
from pydantic.types import NonNegativeInt

# Typed HTTP responses/errors
from utils.http import (
    OK,
    Created,
    NoContent,
    Unauthorized,
    Forbidden,
    NotFound,
    Conflict,
    InternalServerError,
)

# ──────────────────────────────────────────────────────────────────────────────
from models.common import (
    AuthContext,
    NonEmptyStr,
    PasswordStr,
    PrefValueStr,
    RoleStr,
    UsernameStr,
)
from models.user import (
    Profile,
    StoredProfile,
    ListUsersParams,
    ListUsersOKBody,
    CreateUserRequest,
    UpdateUserRequest,
    UpdatePasswordRequest,
)


# ──────────────────────────────────────────────────────────────────────────────
# Domain Errors
from .errors import (
    DomainUnauthorized,
    DomainForbidden,
    DomainNotFound,
    DomainConflict,
    DomainInvariantViolation,
)


# ──────────────────────────────────────────────────────────────────────────────
# Provider Interface
# ──────────────────────────────────────────────────────────────────────────────
class ListUsersResult(BaseModel):
    total: NonNegativeInt
    users: Sequence[StoredProfile]
    nextToken: NonEmptyStr | None = None


class UserDBProvider(ABC):
    """
    Backend contract for user persistence.

    Responsibilities:
      • post_user → Create a new user and assign its ID (provider decides ID source).
      • put_user  → Persist updates to an existing user; ID must already exist.
      • get_user  → Retrieve stored user profile by UUID.
      • delete_user → Remove a user by ID.
      • list_users → Paginated listing.
      • update_password → Provider-defined password change.
    """

    @abstractmethod
    def get_user(self, ctx: AuthContext, *, uid: UUID) -> StoredProfile: ...

    @abstractmethod
    def post_user(
        self,
        ctx: AuthContext,
        *,
        username: UsernameStr,
        role: RoleStr,
        preferences: Mapping[str, PrefValueStr] | None,
    ) -> StoredProfile: ...

    @abstractmethod
    def put_user(self, ctx: AuthContext, *, user: StoredProfile) -> StoredProfile: ...

    @abstractmethod
    def delete_user(self, ctx: AuthContext, *, uid: UUID) -> None: ...

    @abstractmethod
    def list_users(
        self, ctx: AuthContext, *, limit: int | None, next_token: str | None
    ) -> ListUsersResult: ...

    @abstractmethod
    def update_password(
        self,
        ctx: AuthContext,
        *,
        uid: UUID,
        current_password: NonEmptyStr,
        new_password: PasswordStr,
    ) -> None: ...


# ──────────────────────────────────────────────────────────────────────────────
# User Service
# ──────────────────────────────────────────────────────────────────────────────
class UserService:
    """
    API-facing service for user management.
    Mirrors provider contract and matches product/report/auth service patterns.
    """

    def __init__(self, provider: UserDBProvider):
        self.provider = provider

    # ─────────── Helpers ───────────
    @staticmethod
    def _handle_error(e: Exception, msg: str = "Internal error") -> NoReturn:
        mapping = {
            DomainUnauthorized: lambda: Unauthorized("Not authorized."),
            DomainForbidden: lambda: Forbidden("Forbidden."),
            DomainNotFound: lambda: NotFound(msg),
            DomainConflict: lambda: Conflict("Conflict."),
            DomainInvariantViolation: lambda: InternalServerError(str(e)),
        }
        raise mapping.get(type(e), lambda: InternalServerError(str(e)))()

    @staticmethod
    def _public_profile(u: StoredProfile) -> Profile:
        return Profile(
            id=u.id, username=u.username, role=u.role, preferences=u.preferences
        )

    @staticmethod
    def _touch(u: StoredProfile, **updates) -> StoredProfile:
        return u.model_copy(update={**updates, "updatedAt": datetime.now(timezone.utc)})

    # ─────────── Endpoints ───────────
    # GET /user → 200 | 401 | 403 | 500
    def list_users(
        self, ctx: AuthContext, params: ListUsersParams
    ) -> OK[ListUsersOKBody]:
        try:
            res = self.provider.list_users(
                ctx, limit=params.limit, next_token=params.nextToken
            )
            body = ListUsersOKBody(
                total=res.total,
                users=[self._public_profile(u) for u in res.users],
                nextToken=res.nextToken,
            )
            return OK(body)
        except Exception as e:
            self._handle_error(e, "Failed to list users.")

    # POST /user → 201 | 400 | 401 | 403 | 409 | 500
    def create_user(
        self, ctx: AuthContext, payload: CreateUserRequest
    ) -> Created[Profile]:
        try:
            stored = self.provider.post_user(
                ctx,
                username=payload.username,
                role=payload.role,
                preferences=payload.preferences,
            )
            return Created(self._public_profile(stored))
        except Exception as e:
            self._handle_error(e, "Failed to create user.")

    # GET /user/{uid} → 200 | 401 | 403 | 404 | 500
    def get_user(self, ctx: AuthContext, uid: UUID) -> OK[Profile]:
        try:
            stored = self.provider.get_user(ctx, uid=uid)
            return OK(self._public_profile(stored))
        except Exception as e:
            self._handle_error(e, "User not found.")

    # PATCH /user/{uid} → 200 | 401 | 403 | 404 | 409 | 500
    def update_user(
        self, ctx: AuthContext, uid: UUID, payload: UpdateUserRequest
    ) -> OK[Profile]:
        try:
            user = self.provider.get_user(ctx, uid=uid)

            if payload.username is not None:
                user.username = payload.username
            if payload.role is not None:
                user.role = payload.role
            if payload.preferences is not None:
                new_prefs = dict(user.preferences)
                for k, v in payload.preferences.items():
                    if v is None:
                        new_prefs.pop(k, None)
                    else:
                        new_prefs[k] = v
                user.preferences = new_prefs

            updated = self._touch(user)
            stored = self.provider.put_user(ctx, user=updated)
            return OK(self._public_profile(stored))
        except Exception as e:
            self._handle_error(e, "Failed to update user.")

    # DELETE /user/{uid} → 204 | 401 | 403 | 404 | 500
    def delete_user(self, ctx: AuthContext, uid: UUID) -> NoContent:
        try:
            self.provider.delete_user(ctx, uid=uid)
            return NoContent()
        except Exception as e:
            self._handle_error(e, "User not found.")

    # PATCH /user/{uid}/password → 204 | 401 | 403 | 404 | 500
    def update_password(
        self, ctx: AuthContext, uid: UUID, payload: UpdatePasswordRequest
    ) -> NoContent:
        try:
            self.provider.update_password(
                ctx,
                uid=uid,
                current_password=payload.currentPassword,
                new_password=payload.newPassword,
            )
            return NoContent()
        except Exception as e:
            self._handle_error(e, "Failed to update password.")
