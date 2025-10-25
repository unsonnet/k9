#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
from datetime import datetime, timezone
from typing import NoReturn
from uuid import UUID

from config import settings
from utils.http import (
    Conflict,
    Created,
    Forbidden,
    InternalServerError,
    NoContent,
    NotFound,
    OK,
    TooManyRequests,
    Unauthorized,
)

from models.auth import AuthContext, LoginRequest
from models.user import (
    CreateUserRequest,
    CreateUserResult,
    ListUsersOKBody,
    ListUsersParams,
    Profile,
    StoredProfile,
    UpdatePasswordRequest,
    UpdateUserRequest,
)

from ..errors import (
    DomainConflict,
    DomainForbidden,
    DomainInvariantViolation,
    DomainNotFound,
    DomainRateLimited,
    DomainUnauthorized,
)

from .provider import UserDBProvider


# ──────────────────────────────────────────────────────────────────────────────
# User Service
# ──────────────────────────────────────────────────────────────────────────────
class UserService:
    """
    API-facing orchestrator for user management.
    Provider enforces identity truth: admin vs self.
    """

    provider: UserDBProvider

    def __init__(self):
        from .provider import CognitoUserDBProvider, _NoopUserDBProvider

        cfg = settings()
        if cfg.cognito_user_pool_id and cfg.cognito_client_id:
            self.provider = CognitoUserDBProvider()
            return
        if cfg.platform in ("dev", "local"):
            self.provider = _NoopUserDBProvider()
            return
        raise InternalServerError("User provider not configured properly.")

    # ─────────── Helpers ───────────
    @staticmethod
    def _handle_error(e: Exception, msg: str = "Internal error") -> NoReturn:
        mapping = {
            DomainUnauthorized: lambda: Unauthorized("Not authorized."),
            DomainForbidden: lambda: Forbidden("Forbidden."),
            DomainNotFound: lambda: NotFound(msg),
            DomainConflict: lambda: Conflict("Conflict."),
            DomainRateLimited: lambda: TooManyRequests("Rate limit exceeded."),
            DomainInvariantViolation: lambda: InternalServerError(str(e)),
        }
        raise mapping.get(type(e), lambda: InternalServerError(str(e)))()

    @staticmethod
    def _public_profile(u: StoredProfile) -> Profile:
        return Profile(
            id=u.id,
            username=u.username,
            name=u.name,
            phone=u.phone,
            role=u.role,
            preferences=u.preferences,
        )

    @staticmethod
    def _touch(u: StoredProfile, **updates) -> StoredProfile:
        return u.model_copy(update={**updates, "updatedAt": datetime.now(timezone.utc)})

    # ─────────── Endpoints ───────────

    # GET /user → 200 | 401 | 403 | 429 | 500
    def list_users(
        self, ctx: AuthContext, params: ListUsersParams
    ) -> OK[ListUsersOKBody]:
        try:
            if not self.provider.is_admin(ctx):
                raise DomainForbidden("Admin privileges required.")

            res = self.provider.list_users(
                limit=params.limit, next_token=params.nextToken
            )
            body = ListUsersOKBody(
                total=res.total,
                users=[self._public_profile(u) for u in res.users],
                nextToken=res.nextToken,
            )
            return OK(body)
        except Exception as e:
            self._handle_error(e, "Failed to list users.")

    # POST /user → 201 | 400 | 401 | 403 | 409 | 429 | 500
    def create_user(
        self, ctx: AuthContext, payload: CreateUserRequest
    ) -> Created[CreateUserResult]:
        try:
            if not self.provider.is_admin(ctx):
                raise DomainForbidden("Admin privileges required.")

            created = self.provider.post_user(
                username=payload.username,
                name=payload.name,
                phone=payload.phone,
                role=payload.role,
                preferences=payload.preferences,
            )
            return Created(created)
        except Exception as e:
            self._handle_error(e, "Failed to create user.")

    # GET /user/{uid} → 200 | 401 | 403 | 404 | 429 | 500
    def get_user(self, ctx: AuthContext, uid: UUID) -> OK[Profile]:
        try:
            if not (self.provider.is_admin(ctx) or self.provider.is_self(ctx, uid=uid)):
                raise DomainForbidden("Not allowed to view other users unless admin.")

            stored = self.provider.get_user(uid=uid)
            return OK(self._public_profile(stored))
        except Exception as e:
            self._handle_error(e, "User not found.")

    # PATCH /user/{uid} → 200 | 401 | 403 | 404 | 409 | 429 | 500
    def update_user(
        self, ctx: AuthContext, uid: UUID, payload: UpdateUserRequest
    ) -> OK[Profile]:
        try:
            is_admin = self.provider.is_admin(ctx)
            is_self = self.provider.is_self(ctx, uid=uid)

            if not (is_admin or is_self):
                raise DomainForbidden(
                    "Not allowed to update users unless admin or self."
                )

            if payload.role is not None and not is_admin:
                raise DomainForbidden("Only administrators can change role.")

            user = self.provider.get_user(uid=uid)

            if payload.username is not None:
                user.username = payload.username
            if payload.name is not None:
                user.name = payload.name
            if payload.phone is not None:
                user.phone = payload.phone
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

            stored = self.provider.put_user(user=self._touch(user))
            return OK(self._public_profile(stored))
        except Exception as e:
            self._handle_error(e, "Failed to update user.")

    # DELETE /user/{uid} → 204 | 401 | 403 | 404 | 429 | 500
    def delete_user(self, ctx: AuthContext, uid: UUID) -> NoContent:
        try:
            if not self.provider.is_admin(ctx):
                raise DomainForbidden("Admin privileges required.")

            self.provider.delete_user(uid=uid)
            return NoContent()
        except Exception as e:
            self._handle_error(e, "Failed to delete user.")

    # PATCH /user/{uid}/password → 204 | 401 | 403 | 404 | 429 | 500
    def update_password(
        self, ctx: AuthContext, uid: UUID, payload: UpdatePasswordRequest
    ) -> NoContent:
        try:
            is_admin = self.provider.is_admin(ctx)
            is_self = self.provider.is_self(ctx, uid=uid)

            if not (is_admin or is_self):
                raise DomainForbidden(
                    "Only administrators can reset another user's password."
                )

            if not is_admin:
                if not payload.currentPassword:
                    raise DomainForbidden("Current password required.")

                profile = self.provider.get_user(uid=uid)
                from services.auth.service import AuthService

                auth = AuthService()
                auth.login(
                    LoginRequest(
                        username=profile.username,
                        password=payload.currentPassword,
                    )
                )

            self.provider.update_password(uid=uid, new_password=payload.newPassword)
            return NoContent()
        except Exception as e:
            self._handle_error(e, "Failed to update password.")
