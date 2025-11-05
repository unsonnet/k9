#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Auth domain models - Business entities and value objects for authentication."""

from __future__ import annotations

from uuid import UUID
from pydantic.types import NonNegativeInt

from ..shared.base import DomainModel
from ..shared.types import SessionStr, TokenStr, UsernameStr

# ──────────────────────────────────────────────────────────────────────────────
# Value Objects
# ──────────────────────────────────────────────────────────────────────────────


class AuthTokens(DomainModel):
    """Authenticated user token set."""

    user: UUID
    access_token: TokenStr
    refresh_token: TokenStr
    expires_in: NonNegativeInt


class AuthChallenge(DomainModel):
    """Authentication challenge state."""

    username: UsernameStr
    session: SessionStr


class AuthContext(DomainModel):
    """Bearer authentication context for services and providers."""

    bearer_token: TokenStr
