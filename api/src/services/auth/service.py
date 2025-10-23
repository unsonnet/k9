#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
from typing import NoReturn

from config import settings
from utils.http import (
    Accepted,
    Gone,
    InternalServerError,
    NoContent,
    NotFound,
    OK,
    Unauthorized,
)
from models.auth import (
    AuthChallenge,
    AuthTokens,
    AuthContext,
    ForgotRequest,
    LoginAcceptedBody,
    LoginOKBody,
    LoginRequest,
    RefreshOKBody,
    RefreshRequest,
    ResetRequest,
)
from ..errors import (
    DomainExpiredToken,
    DomainInvalidCredentials,
    DomainInvariantViolation,
    DomainNotFound,
    DomainUnauthorized,
)
from .provider import AuthProvider


# ──────────────────────────────────────────────────────────────────────────────
# Auth Service
# ──────────────────────────────────────────────────────────────────────────────
class AuthService:
    """
    API-facing orchestrator for authentication.
    Mirrors provider contract and matches product/report/user service patterns.
    """

    provider: AuthProvider

    def __init__(self):
        # Choose provider by stage from config settings
        from .provider import LocalAuthProvider, _NoopAuthProvider

        stage = settings().stage.lower().strip()
        if stage == "dev":
            self.provider = LocalAuthProvider()
        elif stage == "prod":
            self.provider = _NoopAuthProvider()
        else:
            # Unknown stage should fail fast with a 5xx
            raise InternalServerError(f"Unsupported stage: {stage}")

    # ─────────── Helpers ───────────
    @staticmethod
    def _handle_error(e: Exception, msg: str = "Internal error") -> NoReturn:
        mapping = {
            DomainNotFound: lambda: NotFound(msg),
            DomainInvalidCredentials: lambda: Unauthorized("Invalid credentials."),
            DomainUnauthorized: lambda: Unauthorized("Not authorized."),
            DomainExpiredToken: lambda: Gone("Token expired or invalid."),
            DomainInvariantViolation: lambda: InternalServerError(str(e)),
        }
        raise mapping.get(type(e), lambda: InternalServerError(str(e)))()

    # ─────────── Endpoints ───────────
    # POST /auth/forgot → 204 | 404 | 500
    def forgot(self, payload: ForgotRequest) -> NoContent:
        try:
            self.provider.start_password_reset(username=payload.username)
            return NoContent()
        except Exception as e:
            self._handle_error(e, "User not found.")

    # POST /auth/login → 200 | 202 | 401 | 404 | 500
    def login(
        self, payload: LoginRequest
    ) -> OK[LoginOKBody] | Accepted[LoginAcceptedBody]:
        try:
            result = self.provider.authenticate(
                username=payload.username, password=payload.password
            )
            if isinstance(result, AuthChallenge):
                return Accepted(
                    LoginAcceptedBody(username=result.username, session=result.session)
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
            raise DomainInvariantViolation("unexpected authentication result shape")
        except Exception as e:
            self._handle_error(e, "Failed to authenticate.")

    # POST /auth/logout → 204 | 401 | 500
    def logout(self, ctx: AuthContext) -> NoContent:
        try:
            self.provider.logout(bearer_token=ctx.bearerToken)
            return NoContent()
        except Exception as e:
            self._handle_error(e, "Failed to log out.")

    # POST /auth/refresh → 200 | 404 | 410 | 500
    def refresh(self, payload: RefreshRequest) -> OK[RefreshOKBody]:
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
            self._handle_error(e, "Failed to refresh tokens.")

    # POST /auth/reset → 204 | 404 | 410 | 500
    def reset(self, payload: ResetRequest) -> NoContent:
        try:
            self.provider.reset_password(
                username=payload.username,
                session=payload.session,
                new_password=payload.newPassword,
            )
            return NoContent()
        except Exception as e:
            self._handle_error(e, "Failed to reset password.")
