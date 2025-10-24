#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field
from pydantic.types import NonNegativeInt

from .common import PasswordStr, SessionStr, TokenStr, UsernameStr


# ──────────────────────────────────────────────────────────────────────────────
# Request & Response Models
# ──────────────────────────────────────────────────────────────────────────────
class ForgetRequest(BaseModel):
    username: UsernameStr


class LoginRequest(BaseModel):
    username: UsernameStr
    password: PasswordStr


class ChallengeType(str, Enum):
    NEW_PASSWORD_REQUIRED = "NEW_PASSWORD_REQUIRED"


class LoginAcceptedBody(BaseModel):
    username: UsernameStr
    challenge: ChallengeType = Field(default=ChallengeType.NEW_PASSWORD_REQUIRED)
    session: SessionStr


class LoginOKBody(BaseModel):
    user: UUID
    accessToken: TokenStr
    refreshToken: TokenStr
    expiresIn: NonNegativeInt


class RefreshRequest(BaseModel):
    username: UsernameStr
    refreshToken: TokenStr


class RefreshOKBody(BaseModel):
    user: UUID
    accessToken: TokenStr
    refreshToken: TokenStr
    expiresIn: NonNegativeInt


class ResetRequest(BaseModel):
    username: UsernameStr
    session: SessionStr
    newPassword: PasswordStr


class LogoutRequest(BaseModel):
    """Logout request body per OpenAPI: requires username and refreshToken.

    Note: Service will prefer this refresh token when provided, but for
    backward compatibility the access token from the Authorization header
    may still be used by the service/provider if no refreshToken is supplied
    by the caller.
    """

    username: UsernameStr
    refreshToken: TokenStr


# ──────────────────────────────────────────────────────────────────────────────
# Domain Models
# ──────────────────────────────────────────────────────────────────────────────
class AuthTokens(BaseModel):
    user: UUID
    access_token: TokenStr
    refresh_token: TokenStr
    expires_in: NonNegativeInt


class AuthChallenge(BaseModel):
    username: UsernameStr
    session: SessionStr


# ──────────────────────────────────────────────────────────────────────────────
# Contexts
# ──────────────────────────────────────────────────────────────────────────────
class AuthContext(BaseModel):
    """Bearer-auth context made available to providers/services."""

    bearerToken: TokenStr
