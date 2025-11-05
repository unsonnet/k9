#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Auth API models - Request/Response DTOs for authentication endpoints."""

from __future__ import annotations

from enum import Enum
from uuid import UUID
from pydantic import Field
from pydantic.types import NonNegativeInt

from ..shared.base import ApiModel
from ..shared.types import PasswordStr, SessionStr, TokenStr, UsernameStr

# ──────────────────────────────────────────────────────────────────────────────
# Request Models
# ──────────────────────────────────────────────────────────────────────────────


class LoginRequest(ApiModel):
    """User login credentials."""

    username: UsernameStr
    password: PasswordStr


class ForgetPasswordRequest(ApiModel):
    """Request to initiate password reset flow."""

    username: UsernameStr


class RefreshTokenRequest(ApiModel):
    """Token refresh request."""

    username: UsernameStr
    refreshToken: TokenStr


class ResetPasswordRequest(ApiModel):
    """Complete password reset with new password."""

    username: UsernameStr
    session: SessionStr
    newPassword: PasswordStr


class LogoutRequest(ApiModel):
    """User logout request.

    Note: Service will prefer refresh token when provided, but for
    backward compatibility may use access token from Authorization header
    if no refresh token is supplied.
    """

    username: UsernameStr
    refreshToken: TokenStr


# ──────────────────────────────────────────────────────────────────────────────
# Response Models
# ──────────────────────────────────────────────────────────────────────────────


class ChallengeType(str, Enum):
    """Authentication challenge types."""

    NEW_PASSWORD_REQUIRED = "NEW_PASSWORD_REQUIRED"


class LoginChallengeResponse(ApiModel):
    """Login response when user must complete a challenge."""

    username: UsernameStr
    challenge: ChallengeType = Field(default=ChallengeType.NEW_PASSWORD_REQUIRED)
    session: SessionStr


class LoginSuccessResponse(ApiModel):
    """Successful login response with tokens."""

    user: UUID
    accessToken: TokenStr
    refreshToken: TokenStr
    expiresIn: NonNegativeInt


class RefreshTokenResponse(ApiModel):
    """Successful token refresh response."""

    user: UUID
    accessToken: TokenStr
    refreshToken: TokenStr
    expiresIn: NonNegativeInt
