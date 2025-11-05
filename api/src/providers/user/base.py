#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Final, Mapping, NoReturn
from uuid import UUID

from models.shared.types import (
    NonEmptyStr,
    PasswordStr,
    RoleStr,
    UsernameStr,
    PhoneStr,
)
from models.domain.auth import AuthContext
from models.domain.user import UserEntity, UserCreationResult, ListUsersResult
from utils.errors import DomainInvariantViolation


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
class NoopUserDBProvider(UserDBProvider):
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
