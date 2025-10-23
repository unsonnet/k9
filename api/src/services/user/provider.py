#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Mapping, Sequence
from uuid import UUID
from pydantic import BaseModel
from pydantic.types import NonNegativeInt

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
    StoredProfile,
)


# ──────────────────────────────────────────────────────────────────────────────
# Provider Interfaces
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


# Default no-op used by service constructors unless overridden
class _NoopUserDBProvider(UserDBProvider):  # pragma: no cover - placeholder
    def get_user(self, *_, **__) -> StoredProfile:  # type: ignore[override]
        raise NotImplementedError("UserDBProvider not configured")

    def post_user(self, *_, **__) -> StoredProfile:  # type: ignore[override]
        raise NotImplementedError("UserDBProvider not configured")

    def put_user(self, *_, **__) -> StoredProfile:  # type: ignore[override]
        raise NotImplementedError("UserDBProvider not configured")

    def delete_user(self, *_, **__) -> None:  # type: ignore[override]
        raise NotImplementedError("UserDBProvider not configured")

    def list_users(self, *_, **__) -> ListUsersResult:  # type: ignore[override]
        raise NotImplementedError("UserDBProvider not configured")

    def update_password(self, *_, **__) -> None:  # type: ignore[override]
        raise NotImplementedError("UserDBProvider not configured")
