#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
from datetime import datetime, timezone
from typing import NoReturn
from uuid import UUID

from config import settings
from utils.http import (
    HttpError,
    Conflict,
    Created,
    Forbidden,
    InternalServerError,
    NoContent,
    NotFound,
    OK,
    TooManyRequests,
    Unauthorized,
    Gone,
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
from utils.errors import (
    DomainConflict,
    DomainExpiredToken,
    DomainInvariantViolation,
    DomainNotFound,
    DomainRateLimited,
    DomainUnauthorized,
    DomainUserDisabled,
    DomainForbidden,
)
from services.auth import AuthService
from providers.user import UserDBProvider


# ──────────────────────────────────────────────────────────────────────────────
# User Service
# ──────────────────────────────────────────────────────────────────────────────
class UserService:
    """Orchestrate user management using a configured provider."""

    provider: UserDBProvider
    auth: AuthService

    def __init__(self) -> None:
        from providers.user import CognitoUserDBProvider, _NoopUserDBProvider

        cfg = settings()

        # Full provider when deployed on AWS
        if cfg.platform == "aws":
            self.provider = CognitoUserDBProvider()

        # Local / dev fallback
        elif cfg.platform in {"dev", "local"}:
            self.provider = _NoopUserDBProvider()

        # Fail clearly if neither condition applies
        else:
            raise InternalServerError("Failed to initialize user service.")

        # Sub-services initialized last for consistency
        self.auth = AuthService()

    # ─────────── Helpers ───────────
    @staticmethod
    def _handle_error(e: Exception) -> NoReturn:
        """Map domain errors to HTTP responses."""
        m: dict[type[Exception], type[HttpError]] = {
            DomainNotFound: NotFound,
            DomainConflict: Conflict,
            DomainUnauthorized: Unauthorized,
            DomainForbidden: Forbidden,
            DomainUserDisabled: Forbidden,
            DomainExpiredToken: Gone,
            DomainRateLimited: TooManyRequests,
            DomainInvariantViolation: InternalServerError,
        }
        raise m.get(type(e), InternalServerError).from_exception(e)

    @staticmethod
    def _public(u: StoredProfile) -> Profile:
        """Sanitize private user attributes."""
        return Profile(
            id=u.id,
            username=u.username,
            name=u.name,
            phone=u.phone,
            role=u.role,
            preferences=u.preferences,
        )

    @staticmethod
    def _touch(u: StoredProfile, **x) -> StoredProfile:
        """Apply update timestamp."""
        return u.model_copy(update={**x, "updatedAt": datetime.now(timezone.utc)})

    # ─────────── Noncontract Methods ───────────

    def is_admin(self, ctx: AuthContext) -> bool:
        """Check if context user is an admin."""
        return self.provider.is_admin(ctx)

    def is_self(self, ctx: AuthContext, uid: UUID) -> bool:
        """Check if context user matches given user id."""
        return self.provider.is_self(ctx, uid=uid)

    # ─────────── Contract Methods ───────────

    # GET /user → 200 | 401 | 403 | 429 | 500
    def list_users(self, ctx: AuthContext, p: ListUsersParams) -> OK[ListUsersOKBody]:
        """List users."""
        try:
            if not self.provider.is_admin(ctx):
                raise DomainForbidden("Request denied.")
            r = self.provider.list_users(limit=p.limit, next_token=p.nextToken)
            return OK(
                ListUsersOKBody(
                    total=r.total,
                    users=[self._public(u) for u in r.users],
                    nextToken=r.nextToken,
                )
            )
        except Exception as e:
            self._handle_error(e)

    # POST /user → 201 | 401 | 403 | 409 | 429 | 500
    def create_user(
        self, ctx: AuthContext, p: CreateUserRequest
    ) -> Created[CreateUserResult]:
        """Create a new user."""
        try:
            if not self.provider.is_admin(ctx):
                raise DomainForbidden("Request denied.")
            return Created(
                self.provider.post_user(
                    username=p.username,
                    name=p.name,
                    phone=p.phone,
                    role=p.role,
                    preferences=p.preferences,
                )
            )
        except Exception as e:
            self._handle_error(e)

    # GET /user/{uid} → 200 | 401 | 403 | 404 | 429 | 500
    def get_user(self, ctx: AuthContext, uid: UUID) -> OK[Profile]:
        """Retrieve a user by id."""
        try:
            if not (self.provider.is_admin(ctx) or self.provider.is_self(ctx, uid=uid)):
                raise DomainForbidden("Request denied.")
            return OK(self._public(self.provider.get_user(uid=uid)))
        except Exception as e:
            self._handle_error(e)

    # PATCH /user/{uid} → 200 | 401 | 403 | 404 | 409 | 429 | 500
    def update_user(
        self, ctx: AuthContext, uid: UUID, p: UpdateUserRequest
    ) -> OK[Profile]:
        """Update a user by id."""
        try:
            a = self.provider.is_admin(ctx)
            s = self.provider.is_self(ctx, uid=uid)
            if not (a or s):
                raise DomainForbidden("Request denied.")
            if p.role is not None and not a:
                raise DomainForbidden("Request denied.")
            u = self.provider.get_user(uid=uid)
            if p.username is not None:
                u.username = p.username
            if p.name is not None:
                u.name = p.name
            if p.phone is not None:
                u.phone = p.phone
            if p.role is not None:
                u.role = p.role
            if p.preferences is not None:
                prefs = dict(u.preferences)
                for k, v in p.preferences.items():
                    prefs.pop(k, None) if v is None else prefs.__setitem__(k, v)
                u.preferences = prefs
            r = self.provider.put_user(user=self._touch(u))
            return OK(self._public(r))
        except Exception as e:
            self._handle_error(e)

    # DELETE /user/{uid} → 204 | 401 | 403 | 404 | 429 | 500
    def delete_user(self, ctx: AuthContext, uid: UUID) -> NoContent:
        """Delete a user by id."""
        try:
            if not self.provider.is_admin(ctx):
                raise DomainForbidden("Request denied.")
            self.provider.delete_user(uid=uid)
            return NoContent()
        except Exception as e:
            self._handle_error(e)

    # PATCH /user/{uid}/password → 204 | 401 | 403 | 404 | 429 | 500
    def update_password(
        self, ctx: AuthContext, uid: UUID, p: UpdatePasswordRequest
    ) -> NoContent:
        """Change a user's password."""
        try:
            a = self.provider.is_admin(ctx)
            s = self.provider.is_self(ctx, uid=uid)
            if not (a or s):
                raise DomainForbidden("Request denied.")
            if s:
                if not p.currentPassword:
                    raise DomainForbidden("Current password required.")
                pr = self.provider.get_user(uid=uid)
                self.auth.login(
                    LoginRequest(username=pr.username, password=p.currentPassword)
                )
            self.provider.update_password(uid=uid, new_password=p.newPassword)
            return NoContent()
        except Exception as e:
            self._handle_error(e)
