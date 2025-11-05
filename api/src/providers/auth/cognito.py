#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from typing import NoReturn
from uuid import UUID

from config import boto3_client, settings
from models.domain.auth import AuthChallenge, AuthTokens
from models.shared.types import PasswordStr, SessionStr, TokenStr, UsernameStr
from utils.errors import (
    DomainError,
    DomainExpiredToken,
    DomainInvalidCredentials,
    DomainInvariantViolation,
    DomainNotFound,
    DomainRateLimited,
    DomainUnauthorized,
    DomainUserDisabled,
)

from .base import AuthProvider


# ──────────────────────────────────────────────────────────────────────────────
# Cognito Provider
# ──────────────────────────────────────────────────────────────────────────────
class CognitoAuthProvider(AuthProvider):
    """Manage authentication operations using AWS Cognito."""

    def __init__(self) -> None:
        cfg = settings()
        if not (
            cfg.cognito_user_pool_id
            and cfg.cognito_client_id
            and cfg.cognito_client_secret
        ):
            raise DomainInvariantViolation(
                "Failed to initialize authentication provider."
            )
        self.user_pool_id: str = cfg.cognito_user_pool_id
        self.client_id: str = cfg.cognito_client_id
        self.client_secret: str = cfg.cognito_client_secret
        self._cognito = boto3_client("cognito-idp")

    # ─────────── Helpers ───────────
    def _secret_hash(self, username: str) -> str:
        msg = (username + self.client_id).encode("utf-8")
        key = self.client_secret.encode("utf-8")
        digest = hmac.new(key, msg, hashlib.sha256).digest()
        return base64.b64encode(digest).decode("utf-8")

    @staticmethod
    def _decode_jwt_sub(token: str) -> UUID:
        try:
            parts = token.split(".")
            if len(parts) < 2:
                raise ValueError
            padded = parts[1] + "=" * (-len(parts[1]) % 4)
            payload = json.loads(base64.urlsafe_b64decode(padded).decode("utf-8"))
            return UUID(payload["sub"])
        except Exception as e:
            raise DomainInvariantViolation("Failed to parse identity token.") from e

    def _handle_error(self, e: Exception, msg: str) -> NoReturn:
        cx = self._cognito.exceptions
        mapping: dict[type[Exception], type[DomainError]] = {
            cx.UserNotFoundException: DomainNotFound,
            cx.UserNotConfirmedException: DomainUserDisabled,
            cx.PasswordResetRequiredException: DomainUserDisabled,
            cx.UnsupportedUserStateException: DomainUserDisabled,
            cx.NotAuthorizedException: DomainInvalidCredentials,
            cx.ExpiredCodeException: DomainExpiredToken,
            cx.CodeMismatchException: DomainExpiredToken,
            cx.TooManyRequestsException: DomainRateLimited,
            cx.LimitExceededException: DomainRateLimited,
            cx.InvalidParameterException: DomainUnauthorized,
        }
        raise mapping.get(type(e), DomainInvariantViolation)(msg) from e

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
            self._handle_error(e, "Failed to initiate password reset.")

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
                return AuthChallenge(username=username, session=resp["Session"])
            auth = resp["AuthenticationResult"]
            user = self._decode_jwt_sub(auth["IdToken"])
            return AuthTokens(
                user=user,
                access_token=auth["AccessToken"],
                refresh_token=auth["RefreshToken"],
                expires_in=int(auth["ExpiresIn"]),
            )
        except Exception as e:
            self._handle_error(e, "Failed to authenticate user.")

    def logout(self, refresh_token: TokenStr) -> None:
        """Revoke refresh token and invalidate session."""
        try:
            self._cognito.revoke_token(
                Token=str(refresh_token),
                ClientId=self.client_id,
                ClientSecret=self.client_secret,
            )
        except Exception as e:
            self._handle_error(e, "Failed to revoke refresh token.")

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
            auth = resp["AuthenticationResult"]
            user = self._decode_jwt_sub(auth["IdToken"])
            return AuthTokens(
                user=user,
                access_token=auth["AccessToken"],
                refresh_token=str(refresh_token),
                expires_in=int(auth["ExpiresIn"]),
            )
        except Exception as e:
            self._handle_error(e, "Failed to refresh access token.")

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
            self._handle_error(e, "Failed to complete password reset.")
