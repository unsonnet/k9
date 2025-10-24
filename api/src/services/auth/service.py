#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
from typing import NoReturn

from config import settings
from utils.http import (
    Accepted,
    Forbidden,
    Gone,
    InternalServerError,
    NoContent,
    NotFound,
    OK,
    TooManyRequests,
    Unauthorized,
)
from models.auth import (
    AuthChallenge,
    AuthTokens,
    LogoutRequest,
    ForgetRequest,
    LoginAcceptedBody,
    LoginOKBody,
    LoginRequest,
    RefreshOKBody,
    RefreshRequest,
    ResetRequest,
    ChallengeType,
)
from ..errors import (
    DomainExpiredToken,
    DomainInvalidCredentials,
    DomainInvariantViolation,
    DomainNotFound,
    DomainRateLimited,
    DomainUnauthorized,
    DomainUserDisabled,
)
from .provider import AuthProvider


# ──────────────────────────────────────────────────────────────────────────────
# Auth Service
# ──────────────────────────────────────────────────────────────────────────────
class AuthService:
    """
    High-level orchestrator for authentication and password flows.
    Vendor-neutral design — integrates with any AuthProvider backend (e.g., Cognito, Keycloak, Local).
    """

    provider: AuthProvider

    def __init__(self):
        from .provider import CognitoAuthProvider, _NoopAuthProvider

        cfg = settings()

        # Prefer Cognito if configured, otherwise local dev fallback.
        if cfg.cognito_user_pool_id and cfg.cognito_client_id:
            self.provider = CognitoAuthProvider()
            return

        if cfg.platform in ("dev", "local"):
            self.provider = _NoopAuthProvider()
            return

        raise InternalServerError("Authentication provider not configured properly.")

    # ─────────── Helpers ───────────
    @staticmethod
    def _handle_error(e: Exception, msg: str = "Internal error") -> NoReturn:
        """
        Maps domain-level errors to standardized HTTP responses.
        Ensures consistency with OpenAPI 1.0.1 spec.
        """
        mapping = {
            DomainNotFound: lambda: NotFound(msg),
            DomainInvalidCredentials: lambda: Unauthorized("Invalid credentials."),
            DomainUnauthorized: lambda: Unauthorized("Unauthorized or invalid token."),
            DomainUserDisabled: lambda: Forbidden("User disabled or not verified."),
            DomainExpiredToken: lambda: Gone("Token or session expired."),
            DomainRateLimited: lambda: TooManyRequests("Rate limit exceeded."),
            DomainInvariantViolation: lambda: InternalServerError(str(e)),
        }
        raise mapping.get(type(e), lambda: InternalServerError(str(e)))()

    # ─────────── Endpoints ───────────

    # POST /auth/forget → 204 | 400 | 404 | 429 | 500
    def forget(self, payload: ForgetRequest) -> NoContent:
        """
        Initiate password reset flow for a given username.
        """
        try:
            self.provider.start_password_reset(username=payload.username)
            return NoContent()
        except Exception as e:
            self._handle_error(e, "User not found or invalid request.")

    # POST /auth/login → 200 | 202 | 400 | 401 | 403 | 404 | 429 | 500
    def login(
        self, payload: LoginRequest
    ) -> OK[LoginOKBody] | Accepted[LoginAcceptedBody]:
        """
        Authenticate a user and issue tokens or return a challenge (if applicable).
        """
        try:
            result = self.provider.authenticate(
                username=payload.username, password=payload.password
            )
            if isinstance(result, AuthChallenge):
                return Accepted(
                    LoginAcceptedBody(
                        username=result.username,
                        session=result.session,
                        challenge=ChallengeType.NEW_PASSWORD_REQUIRED,
                    )
                )
            if isinstance(result, AuthTokens):
                return OK(
                    LoginOKBody(
                        user=result.user,
                        accessToken=result.access_token,
                        refreshToken=result.refresh_token,
                        expiresIn=result.expires_in,
                    )
                )
            raise DomainInvariantViolation("Unexpected authentication result shape.")
        except Exception as e:
            self._handle_error(e, "Authentication failed.")

    # POST /auth/logout → 204 | 400 | 401 | 500
    def logout(self, payload: LogoutRequest) -> NoContent:
        """
        Logout user and revoke active tokens.
        """
        try:
            self.provider.logout(refresh_token=payload.refreshToken)
            return NoContent()
        except Exception as e:
            self._handle_error(e, "Failed to log out user.")

    # POST /auth/refresh → 200 | 400 | 401 | 410 | 500
    def refresh(self, payload: RefreshRequest) -> OK[RefreshOKBody]:
        """
        Refresh the user's access token using a valid refresh token.
        """
        try:
            tokens = self.provider.refresh(
                username=payload.username, refresh_token=payload.refreshToken
            )
            return OK(
                RefreshOKBody(
                    user=tokens.user,
                    accessToken=tokens.access_token,
                    refreshToken=tokens.refresh_token,
                    expiresIn=tokens.expires_in,
                )
            )
        except Exception as e:
            self._handle_error(e, "Failed to refresh token.")

    # POST /auth/reset → 204 | 400 | 404 | 410 | 429 | 500
    def reset(self, payload: ResetRequest) -> NoContent:
        """
        Complete password reset or change flow.
        """
        try:
            self.provider.reset_password(
                username=payload.username,
                session=payload.session,
                new_password=payload.newPassword,
            )
            return NoContent()
        except Exception as e:
            self._handle_error(e, "Failed to reset password.")
