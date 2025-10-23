#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from datetime import datetime
from typing import Mapping, Sequence
from uuid import UUID

from pydantic import BaseModel
from pydantic.types import NonNegativeInt, PositiveInt

from .common import PrefValueStr, RoleStr, UsernameStr, NonEmptyStr, PasswordStr


# ──────────────────────────────────────────────────────────────────────────────
# Core Models
# ──────────────────────────────────────────────────────────────────────────────
class Profile(BaseModel):
    id: UUID
    username: UsernameStr
    role: RoleStr
    preferences: Mapping[str, PrefValueStr]


class StoredProfile(Profile):
    createdAt: datetime
    updatedAt: datetime | None = None


# ──────────────────────────────────────────────────────────────────────────────
# Request & Response Models
# ──────────────────────────────────────────────────────────────────────────────
class ListUsersParams(BaseModel):
    limit: PositiveInt | None = None
    nextToken: NonEmptyStr | None = None


class ListUsersOKBody(BaseModel):
    total: NonNegativeInt
    users: Sequence[Profile]
    nextToken: NonEmptyStr | None = None


class CreateUserRequest(BaseModel):
    username: UsernameStr
    role: RoleStr
    preferences: Mapping[str, PrefValueStr] | None = None


class UpdateUserRequest(BaseModel):
    username: UsernameStr | None = None
    role: RoleStr | None = None
    preferences: Mapping[str, PrefValueStr | None] | None = None


class UpdatePasswordRequest(BaseModel):
    currentPassword: NonEmptyStr
    newPassword: PasswordStr
