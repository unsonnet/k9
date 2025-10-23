#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
from abc import ABC, abstractmethod
from uuid import UUID

from models.auth import AuthChallenge, AuthTokens
from models.common import PasswordStr, SessionStr, TokenStr, UsernameStr
from ..errors import DomainExpiredToken, DomainNotFound, DomainUnauthorized


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


# Local/dev provider used when running in stage="dev"
class LocalAuthProvider(AuthProvider):
    """A simple in-process auth provider for local development.

    Behavior mirrors tests' FakeAuthProvider to keep handler/service flows
    working without external dependencies.
    """

    def __init__(self) -> None:
        # Deterministic user id for tests/dev
        self.valid_user = UUID("00000000-0000-0000-0000-000000000001")

    def start_password_reset(self, username: UsernameStr) -> None:  # type: ignore[override]
        if username == "missing":
            raise DomainNotFound()

    def authenticate(
        self, username: UsernameStr, password: PasswordStr
    ) -> AuthTokens | AuthChallenge:  # type: ignore[override]
        if password == "bad":
            # treat as unauthorized credentials
            raise DomainUnauthorized()
        if username == "challenge":
            # session must satisfy SessionStr min_length=10
            return AuthChallenge(username=username, session="session-abc123")
        return AuthTokens(
            user=self.valid_user,
            # tokens must satisfy TokenStr min_length=16
            access_token="access-token-123456",
            refresh_token="refresh-token-123456",
            expires_in=3600,
        )

    def logout(self, bearer_token: TokenStr) -> None:  # type: ignore[override]
        if bearer_token == "bad":
            raise DomainUnauthorized()

    def refresh(self, username: UsernameStr, refresh_token: TokenStr) -> AuthTokens:  # type: ignore[override]
        if username == "missing":
            raise DomainNotFound()
        token_str = str(refresh_token)
        if token_str.endswith("expired") or token_str.endswith("bad"):
            raise DomainExpiredToken("expired")
        return AuthTokens(
            user=self.valid_user,
            access_token="access-token-456789",
            refresh_token="refresh-token-456789",
            expires_in=3600,
        )

    def reset_password(
        self, username: UsernameStr, session: SessionStr, new_password: PasswordStr
    ) -> None:  # type: ignore[override]
        if username == "missing":
            raise DomainNotFound()
        if str(session).endswith("expired"):
            raise DomainExpiredToken("expired")
