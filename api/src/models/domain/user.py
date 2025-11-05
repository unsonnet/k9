#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""User domain models - Business entities for user management."""

from __future__ import annotations

from uuid import UUID
from typing import Sequence
from pydantic.types import NonNegativeInt
from ..shared.base import DomainModel, StorageModel, TimeStamped
from ..shared.types import (
    NonEmptyStr,
    PasswordStr,
    PhoneStr,
    PreferencesMap,
    RoleStr,
    UsernameStr,
)

# ──────────────────────────────────────────────────────────────────────────────
# Domain Entities
# ──────────────────────────────────────────────────────────────────────────────


class UserProfile(DomainModel):
    """Core user profile entity."""

    id: UUID
    username: UsernameStr
    name: NonEmptyStr
    phone: PhoneStr
    role: RoleStr
    preferences: PreferencesMap


class UserEntity(StorageModel, TimeStamped):
    """Complete user entity with persistence metadata."""

    id: UUID
    username: UsernameStr
    name: NonEmptyStr
    phone: PhoneStr
    role: RoleStr
    preferences: PreferencesMap


# ──────────────────────────────────────────────────────────────────────────────
# Service Models
# ──────────────────────────────────────────────────────────────────────────────


class UserCreationResult(DomainModel):
    """Result of user creation operation."""

    username: UsernameStr
    temporary_password: PasswordStr


class ListUsersResult(DomainModel):
    """Result of listing users with pagination."""

    total: NonNegativeInt
    users: Sequence[UserEntity]
    next_token: NonEmptyStr | None = None
