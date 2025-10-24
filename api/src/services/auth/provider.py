#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from abc import ABC, abstractmethod
from typing import NoReturn
from uuid import UUID

from config import boto3_client, settings
from models.auth import AuthChallenge, AuthTokens
from models.common import PasswordStr, SessionStr, TokenStr, UsernameStr
from ..errors import (
    DomainExpiredToken,
    DomainInvalidCredentials,
    DomainInvariantViolation,
    DomainNotFound,
    DomainRateLimited,
    DomainUnauthorized,
    DomainUserDisabled,
)


# ──────────────────────────────────────────────────────────────────────────────
# Abstract Base: Auth Provider
# ──────────────────────────────────────────────────────────────────────────────
class AuthProvider(ABC):
    """
    Abstract contract for authentication backends.
    Implementations must raise domain errors rather than HTTP errors directly.
    """

    @abstractmethod
    def start_password_reset(self, username: UsernameStr) -> None: ...

    @abstractmethod
    def authenticate(
        self, username: UsernameStr, password: PasswordStr
    ) -> AuthTokens | AuthChallenge: ...

    @abstractmethod
    def logout(self, refresh_token: TokenStr) -> None: ...

    @abstractmethod
    def refresh(self, username: UsernameStr, refresh_token: TokenStr) -> AuthTokens: ...

    @abstractmethod
    def reset_password(
        self, username: UsernameStr, session: SessionStr, new_password: PasswordStr
    ) -> None: ...


# ──────────────────────────────────────────────────────────────────────────────
# Default / No-op Provider
# ──────────────────────────────────────────────────────────────────────────────
class _NoopAuthProvider(AuthProvider):
    """Fallback provider when no authentication backend is configured."""

    def _raise(self) -> NoReturn:
        raise DomainInvariantViolation("Auth provider not configured.")

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


# ──────────────────────────────────────────────────────────────────────────────
# Cognito-backed Provider
# ──────────────────────────────────────────────────────────────────────────────
class CognitoAuthProvider(AuthProvider):
    """
    AWS Cognito-based authentication provider.
    """

    def __init__(self) -> None:
        cfg = settings()

        if not cfg.cognito_user_pool_id or not cfg.cognito_client_id:
            raise DomainInvariantViolation("Cognito configuration incomplete.")
        if not cfg.cognito_client_secret:
            raise DomainInvariantViolation(
                "COGNITO_CLIENT_SECRET must be set for secret-enabled clients."
            )

        self.user_pool_id = cfg.cognito_user_pool_id
        self.client_id = cfg.cognito_client_id
        self.client_secret = cfg.cognito_client_secret
        self._cognito = boto3_client("cognito-idp")

    # ─────────── Helpers ───────────
    def _secret_hash(self, username: str) -> str:
        msg = (username + self.client_id).encode()
        digest = hmac.new(self.client_secret.encode(), msg, hashlib.sha256).digest()
        return base64.b64encode(digest).decode()

    @staticmethod
    def _decode_jwt_sub(token: str) -> UUID | None:
        """Decode JWT payload (no verification) to extract `sub` as UUID."""
        try:
            parts = token.split(".")
            if len(parts) < 2:
                return None
            payload_bytes = base64.urlsafe_b64decode(
                parts[1] + "=" * (-len(parts[1]) % 4)
            )
            payload = json.loads(payload_bytes)
            sub = payload.get("sub")
            return UUID(str(sub)) if sub else None
        except Exception:
            return None

    def _handle_error(self, e: Exception, msg: str) -> NoReturn:
        """Translate Cognito SDK exceptions to domain-level errors."""
        cx = self._cognito.exceptions
        mapping = {
            cx.UserNotFoundException: DomainNotFound(msg),
            cx.UserNotConfirmedException: DomainUserDisabled("User not confirmed."),
            cx.PasswordResetRequiredException: DomainUserDisabled(
                "Password reset required."
            ),
            cx.UnsupportedUserStateException: DomainUserDisabled(
                "User disabled or unsupported state."
            ),
            cx.NotAuthorizedException: DomainInvalidCredentials("Invalid credentials."),
            cx.ExpiredCodeException: DomainExpiredToken(
                "Expired or invalid code/session."
            ),
            cx.CodeMismatchException: DomainExpiredToken("Invalid verification code."),
            cx.TooManyRequestsException: DomainRateLimited("Rate limit exceeded."),
            cx.LimitExceededException: DomainRateLimited("Rate limit exceeded."),
            cx.InvalidParameterException: DomainUnauthorized("Invalid parameters."),
            cx.InternalErrorException: DomainInvariantViolation(
                "Identity provider internal error."
            ),
        }

        raise mapping.get(type(e), DomainUnauthorized(f"{msg}: {e}"))

    # ─────────── Contract Methods ───────────
    def start_password_reset(self, username: UsernameStr) -> None:
        """Initiate forgot-password flow."""
        try:
            self._cognito.forgot_password(
                ClientId=self.client_id,
                Username=str(username),
                SecretHash=self._secret_hash(str(username)),
            )
        except Exception as e:
            self._handle_error(e, "Failed to start password reset")

    def authenticate(
        self, username: UsernameStr, password: PasswordStr
    ) -> AuthTokens | AuthChallenge:
        """Authenticate user with username/password."""
        try:
            resp = self._cognito.initiate_auth(
                AuthFlow="USER_PASSWORD_AUTH",
                ClientId=self.client_id,
                AuthParameters={
                    "USERNAME": str(username),
                    "PASSWORD": str(password),
                    "SECRET_HASH": self._secret_hash(str(username)),
                },
            )

            if resp.get("ChallengeName") == "NEW_PASSWORD_REQUIRED":
                return AuthChallenge(username=username, session=resp.get("Session", ""))

            auth = resp.get("AuthenticationResult", {})
            id_token = auth.get("IdToken", "")
            user = self._decode_jwt_sub(id_token) or UUID(int=0)

            return AuthTokens(
                user=user,
                access_token=auth.get("AccessToken", ""),
                refresh_token=auth.get("RefreshToken", ""),
                expires_in=int(auth.get("ExpiresIn", 0)),
            )
        except Exception as e:
            self._handle_error(e, "Authentication failed")

    def logout(self, refresh_token: TokenStr) -> None:
        """Revoke refresh token and invalidate session."""
        try:
            self._cognito.revoke_token(
                Token=str(refresh_token),
                ClientId=self.client_id,
                ClientSecret=self.client_secret,
            )
        except Exception as e:
            self._handle_error(e, "Logout failed")

    def refresh(self, username: UsernameStr, refresh_token: TokenStr) -> AuthTokens:
        """Refresh access token using a valid refresh token."""
        try:
            resp = self._cognito.initiate_auth(
                AuthFlow="REFRESH_TOKEN_AUTH",
                ClientId=self.client_id,
                AuthParameters={
                    "USERNAME": str(username),
                    "REFRESH_TOKEN": str(refresh_token),
                    "SECRET_HASH": self._secret_hash(str(username)),
                },
            )

            auth = resp.get("AuthenticationResult", {})
            id_token = auth.get("IdToken", "")
            user = self._decode_jwt_sub(id_token) or UUID(int=0)

            return AuthTokens(
                user=user,
                access_token=auth.get("AccessToken", ""),
                refresh_token=str(refresh_token),  # no rotation on refresh
                expires_in=int(auth.get("ExpiresIn", 0)),
            )
        except Exception as e:
            self._handle_error(e, "Token refresh failed")

    def reset_password(
        self, username: UsernameStr, session: SessionStr, new_password: PasswordStr
    ) -> None:
        """Complete password reset (e.g., NEW_PASSWORD_REQUIRED)."""
        try:
            self._cognito.respond_to_auth_challenge(
                ClientId=self.client_id,
                ChallengeName="NEW_PASSWORD_REQUIRED",
                ChallengeResponses={
                    "USERNAME": str(username),
                    "NEW_PASSWORD": str(new_password),
                    "SECRET_HASH": self._secret_hash(str(username)),
                },
                Session=str(session),
            )
        except Exception as e:
            self._handle_error(e, "Password reset failed")
