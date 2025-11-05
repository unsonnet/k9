#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Final, NoReturn

from models.domain.auth import AuthChallenge, AuthTokens
from models.shared.types import PasswordStr, SessionStr, TokenStr, UsernameStr
from utils.errors import DomainInvariantViolation


# ──────────────────────────────────────────────────────────────────────────────
# Auth Provider
# ──────────────────────────────────────────────────────────────────────────────
class AuthProvider(ABC):
    """Manage authentication contracts for backends."""

    @abstractmethod
    def start_password_reset(self, username: UsernameStr) -> None:
        """Initiate forgot-password flow."""
        ...

    @abstractmethod
    def authenticate(
        self, username: UsernameStr, password: PasswordStr
    ) -> AuthTokens | AuthChallenge:
        """Authenticate user with username/password."""
        ...

    @abstractmethod
    def logout(self, refresh_token: TokenStr) -> None:
        """Revoke refresh token and invalidate session."""
        ...

    @abstractmethod
    def refresh(self, username: UsernameStr, refresh_token: TokenStr) -> AuthTokens:
        """Refresh access token using a valid refresh token."""
        ...

    @abstractmethod
    def reset_password(
        self, username: UsernameStr, session: SessionStr, new_password: PasswordStr
    ) -> None:
        """Complete password reset (e.g., NEW_PASSWORD_REQUIRED)."""
        ...


# ──────────────────────────────────────────────────────────────────────────────
# Disabled Provider
# ──────────────────────────────────────────────────────────────────────────────
class NoopAuthProvider(AuthProvider):
    """Manage authentication operations as a disabled provider."""

    _MSG: Final = "Failed to perform authentication operation."

    def _raise(self) -> NoReturn:
        raise DomainInvariantViolation(self._MSG)

    def start_password_reset(self, username: UsernameStr) -> None:
        self._raise()

    def authenticate(
        self, username: UsernameStr, password: PasswordStr
    ) -> AuthTokens | AuthChallenge:
        self._raise()

    def logout(self, refresh_token: TokenStr) -> None:
        self._raise()

    def refresh(self, username: UsernameStr, refresh_token: TokenStr) -> AuthTokens:
        self._raise()

    def reset_password(
        self, username: UsernameStr, session: SessionStr, new_password: PasswordStr
    ) -> None:
        self._raise()
