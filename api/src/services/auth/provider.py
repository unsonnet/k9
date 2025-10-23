#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
from abc import ABC, abstractmethod

from models.auth import AuthChallenge, AuthTokens
from models.common import PasswordStr, SessionStr, TokenStr, UsernameStr


# ──────────────────────────────────────────────────────────────────────────────
# Provider Interfaces
# ──────────────────────────────────────────────────────────────────────────────
class AuthProvider(ABC):
    """Backend contract for authentication."""

    @abstractmethod
    def start_password_reset(self, username: UsernameStr) -> None: ...

    @abstractmethod
    def authenticate(
        self, username: UsernameStr, password: PasswordStr
    ) -> AuthTokens | AuthChallenge: ...

    @abstractmethod
    def logout(self, bearer_token: TokenStr) -> None: ...

    @abstractmethod
    def refresh(self, username: UsernameStr, refresh_token: TokenStr) -> AuthTokens: ...

    @abstractmethod
    def reset_password(
        self, username: UsernameStr, session: SessionStr, new_password: PasswordStr
    ) -> None: ...


# Default no-op provider used by service constructors unless overridden
class _NoopAuthProvider(AuthProvider):  # pragma: no cover - placeholder
    def start_password_reset(self, username: UsernameStr) -> None:  # type: ignore[override]
        raise NotImplementedError("AuthProvider not configured")

    def authenticate(
        self, username: UsernameStr, password: PasswordStr
    ) -> AuthTokens | AuthChallenge:  # type: ignore[override]
        raise NotImplementedError("AuthProvider not configured")

    def logout(self, bearer_token: TokenStr) -> None:  # type: ignore[override]
        raise NotImplementedError("AuthProvider not configured")

    def refresh(self, username: UsernameStr, refresh_token: TokenStr) -> AuthTokens:  # type: ignore[override]
        raise NotImplementedError("AuthProvider not configured")

    def reset_password(
        self, username: UsernameStr, session: SessionStr, new_password: PasswordStr
    ) -> None:  # type: ignore[override]
        raise NotImplementedError("AuthProvider not configured")
