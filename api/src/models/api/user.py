#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""User API models - Request/Response DTOs for user management endpoints."""

from __future__ import annotations

from typing import Sequence
from pydantic.types import NonNegativeInt, PositiveInt
from uuid import UUID

from ..shared.base import ApiModel
from ..shared.types import (
    NonEmptyStr,
    PasswordStr,
    PhoneStr,
    PreferencesMap,
    RoleStr,
    UsernameStr,
)

# ──────────────────────────────────────────────────────────────────────────────
# Request Models
# ──────────────────────────────────────────────────────────────────────────────


class ListUsersRequest(ApiModel):
    """List users with pagination parameters."""

    limit: PositiveInt | None = None
    nextToken: NonEmptyStr | None = None


class CreateUserRequest(ApiModel):
    """Create new user request."""

    username: UsernameStr
    name: NonEmptyStr
    phone: PhoneStr
    role: RoleStr
    preferences: PreferencesMap | None = None


class UpdateUserRequest(ApiModel):
    """Update user request - all fields optional for PATCH."""

    username: UsernameStr | None = None
    name: NonEmptyStr | None = None
    phone: PhoneStr | None = None
    role: RoleStr | None = None
    preferences: PreferencesMap | None = None


class UpdatePasswordRequest(ApiModel):
    """Update user password request."""

    currentPassword: NonEmptyStr | None = None
    newPassword: PasswordStr


# ──────────────────────────────────────────────────────────────────────────────
# Response Models
# ──────────────────────────────────────────────────────────────────────────────


class UserProfileResponse(ApiModel):
    """User profile information for API responses."""

    id: UUID
    username: UsernameStr
    name: NonEmptyStr
    phone: PhoneStr
    role: RoleStr
    preferences: PreferencesMap


class ListUsersResponse(ApiModel):
    """Paginated list of users response."""

    total: NonNegativeInt
    users: Sequence[UserProfileResponse]
    nextToken: NonEmptyStr | None = None


class CreateUserResponse(ApiModel):
    """Response after creating a new user."""

    username: UsernameStr
    temporaryPassword: PasswordStr
