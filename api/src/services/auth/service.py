#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
from typing import NoReturn

from config import settings
from utils.http import (
    HttpError,
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
from utils.errors import (
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
    """Orchestrate authentication flows using a configured provider."""

    provider: AuthProvider

    def __init__(self) -> None:
        from .provider import CognitoAuthProvider, _NoopAuthProvider

        cfg = settings()
        if (
            cfg.cognito_user_pool_id
            and cfg.cognito_client_id
            and cfg.cognito_client_secret
        ):
            self.provider = CognitoAuthProvider()
        elif cfg.platform in {"dev", "local"}:
            self.provider = _NoopAuthProvider()
        else:
            raise InternalServerError("Failed to initialize authentication provider.")

    # ─────────── Helpers ───────────
    @staticmethod
    def _handle_error(e: Exception) -> NoReturn:
        """Map domain-level errors to standardized HTTP responses."""
        mapping: dict[type[Exception], type[HttpError]] = {
            DomainNotFound: NotFound,
            DomainInvalidCredentials: Unauthorized,
            DomainUnauthorized: Unauthorized,
            DomainUserDisabled: Forbidden,
            DomainExpiredToken: Gone,
            DomainRateLimited: TooManyRequests,
            DomainInvariantViolation: InternalServerError,
        }
        raise mapping.get(type(e), InternalServerError).from_exception(e)

    # ─────────── Contract Methods ───────────

    # POST /auth/forget → 204 | 400 | 404 | 429 | 500
    def forget(self, payload: ForgetRequest) -> NoContent:
        """Initiate password reset flow."""
        try:
            self.provider.start_password_reset(username=payload.username)
            return NoContent()
        except Exception as e:
            self._handle_error(e)

    # POST /auth/login → 200 | 202 | 400 | 401 | 403 | 404 | 429 | 500
    def login(
        self, payload: LoginRequest
    ) -> OK[LoginOKBody] | Accepted[LoginAcceptedBody]:
        """Authenticate user and issue tokens or challenge."""
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
            raise DomainInvariantViolation("Failed to process authentication result.")
        except Exception as e:
            self._handle_error(e)

    # POST /auth/logout → 204 | 400 | 401 | 500
    def logout(self, payload: LogoutRequest) -> NoContent:
        """Logout user and revoke active tokens."""
        try:
            self.provider.logout(refresh_token=payload.refreshToken)
            return NoContent()
        except Exception as e:
            self._handle_error(e)

    # POST /auth/refresh → 200 | 400 | 401 | 410 | 500
    def refresh(self, payload: RefreshRequest) -> OK[RefreshOKBody]:
        """Refresh access token using a valid refresh token."""
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
            self._handle_error(e)

    # POST /auth/reset → 204 | 400 | 404 | 410 | 429 | 500
    def reset(self, payload: ResetRequest) -> NoContent:
        """Complete password reset."""
        try:
            self.provider.reset_password(
                username=payload.username,
                session=payload.session,
                new_password=payload.newPassword,
            )
            return NoContent()
        except Exception as e:
            self._handle_error(e)
