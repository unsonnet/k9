#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
from abc import ABC, abstractmethod

from models.common import PasswordStr, SessionStr, TokenStr, UsernameStr
from models.auth import (
    AuthTokens,
    AuthChallenge,
)


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
