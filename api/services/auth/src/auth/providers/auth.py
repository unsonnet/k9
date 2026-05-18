import base64
import hashlib
import hmac
from enum import StrEnum
from typing import Any, Mapping, Protocol

import boto3
from shared.abc import BaseProvider, DataModel, ExceptionMap, private_api
from shared.config import settings
from shared.errors import (
    DomainExpiredToken,
    DomainForbidden,
    DomainInvalidCredentials,
    DomainInvalidTokens,
    DomainInvariantViolation,
    DomainNotFound,
    DomainRateLimited,
)
from shared.providers.cognito import encode_name
from types_boto3_cognito_idp import CognitoIdentityProviderClient

__all__ = [
    "Tokens",
    "Challenge",
    "AuthProvider",
    "CognitoAuthProvider",
]

# ──── Authentication Models ───────────────────────────────────────────────────────────


class Tokens(DataModel, frozen=True):
    access_token: str
    expires_in: int
    refresh_token: str
    id_token: str


class Challenge(DataModel, frozen=True):
    class Key(StrEnum):
        NEW_PASSWORD = "NEW_PASSWORD"
        NEW_MFA = "NEW_MFA"
        MFA = "MFA"

    session: str
    challenge: Key
    parameters: Mapping[str, str]


# ──── Authentication Protocol ─────────────────────────────────────────────────────────


class AuthProvider(Protocol):
    def authenticate(
        self,
        *,
        name: str,
        password: str,
    ) -> Tokens | Challenge: ...

    def respond_to_challenge(
        self,
        *,
        session: str,
        challenge: Challenge.Key,
        response: Mapping[str, str],
    ) -> Tokens | Challenge: ...

    def refresh_tokens(
        self,
        *,
        refresh_token: str,
    ) -> Tokens: ...

    def revoke_tokens(
        self,
        *,
        access_token: str | None = None,
        refresh_token: str | None = None,
    ) -> None: ...


# ──── AWS Authentication Provider ─────────────────────────────────────────────────────


class CognitoAuthProvider(BaseProvider):
    _client: CognitoIdentityProviderClient
    _client_id: str
    _user_pool_id: str
    _client_secret: str

    def __init__(
        self,
        *,
        region: str | None = None,
        client_id: str | None = None,
        user_pool_id: str | None = None,
        client_secret: str | None = None,
    ) -> None:
        region = region or settings.aws_region
        self._client = boto3.client("cognito-idp", region_name=region)
        self._client_id = client_id or settings.cognito_client_id
        self._user_pool_id = user_pool_id or settings.cognito_user_pool_id
        self._client_secret = client_secret or settings.cognito_client_secret

    @property
    def _exception_map(self) -> ExceptionMap:
        cx = self._client.exceptions
        return {
            DomainExpiredToken: [
                cx.ExpiredCodeException,
                cx.PasswordResetRequiredException,
            ],
            DomainForbidden: [
                cx.ForbiddenException,
                cx.UnauthorizedException,
            ],
            DomainInvalidCredentials: [
                cx.NotAuthorizedException,
                cx.InvalidPasswordException,
                cx.CodeMismatchException,
            ],
            DomainInvalidTokens: [
                cx.RefreshTokenReuseException,
                cx.UnsupportedTokenTypeException,
            ],
            DomainRateLimited: [
                cx.TooManyRequestsException,
                cx.LimitExceededException,
            ],
            DomainNotFound: [
                cx.UserNotFoundException,
            ],
        }

    # ──── Helper Methods ────

    def _secret_hash(self, xname: str) -> str:
        message = f"{xname}{self._client_id}".encode("utf-8")
        key = self._client_secret.encode("utf-8")
        digest = hmac.new(key, message, hashlib.sha256).digest()
        return base64.b64encode(digest).decode("utf-8")

    def _tokens(self, response: Mapping[str, Any]) -> Tokens:
        match response:
            case {
                "AuthenticationResult": {
                    "AccessToken": str(access_token),
                    "ExpiresIn": int(expires_in),
                    "RefreshToken": str(refresh_token),
                    "IdToken": str(id_token),
                }
            }:
                return Tokens(
                    access_token=access_token,
                    expires_in=expires_in,
                    refresh_token=refresh_token,
                    id_token=id_token,
                )
        raise DomainInvariantViolation(f"Unexpected cognito tokens: {response}")

    def _challenge(self, session: str, challenge: str) -> Challenge:
        match challenge:
            case "NEW_PASSWORD_REQUIRED":
                return Challenge(
                    session=session,
                    challenge=Challenge.Key.NEW_PASSWORD,
                    parameters={},
                )
            case "MFA_SETUP":
                response = self._client.associate_software_token(Session=session)
                return Challenge(
                    session=response["Session"],
                    challenge=Challenge.Key.NEW_MFA,
                    parameters={"secret": response["SecretCode"]},
                )
            case "SOFTWARE_TOKEN_MFA":
                return Challenge(
                    session=session,
                    challenge=Challenge.Key.MFA,
                    parameters={},
                )
        raise DomainInvariantViolation(f"Unexpected cognito challenge: {challenge}")

    def _result(self, response: Mapping[str, Any]) -> Tokens | Challenge:
        match response:
            case {"AuthenticationResult": dict()}:
                return self._tokens(response)
            case {"Session": str(session), "ChallengeName": str(challenge)}:
                return self._challenge(session, challenge)
        raise DomainInvariantViolation(f"Unexpected cognito response: {response}")

    # ──── Private APIs ────

    @private_api
    def authenticate(
        self,
        *,
        name: str,
        password: str,
    ) -> Tokens | Challenge:
        xname = encode_name(name)
        return self._result(
            self._client.admin_initiate_auth(
                ClientId=self._client_id,
                UserPoolId=self._user_pool_id,
                AuthFlow="ADMIN_USER_PASSWORD_AUTH",
                AuthParameters={
                    "SECRET_HASH": self._secret_hash(xname),
                    "USERNAME": xname,
                    "PASSWORD": password,
                },
            )
        )

    @private_api
    def respond_to_challenge(
        self,
        *,
        session: str,
        challenge: Challenge.Key,
        response: Mapping[str, str],
    ) -> Tokens | Challenge:
        match challenge:
            case Challenge.Key.NEW_PASSWORD:
                xname = encode_name(response["name"])
                return self._result(
                    self._client.admin_respond_to_auth_challenge(
                        ClientId=self._client_id,
                        UserPoolId=self._user_pool_id,
                        Session=session,
                        ChallengeName="NEW_PASSWORD_REQUIRED",
                        ChallengeResponses={
                            "SECRET_HASH": self._secret_hash(xname),
                            "USERNAME": xname,
                            "NEW_PASSWORD": response["password"],
                        },
                    )
                )
            case Challenge.Key.NEW_MFA:
                xname = encode_name(response["name"])
                return self._tokens(
                    self._client.admin_respond_to_auth_challenge(
                        ClientId=self._client_id,
                        UserPoolId=self._user_pool_id,
                        Session=self._client.verify_software_token(
                            Session=session,
                            UserCode=response["code"],
                        )["Session"],
                        ChallengeName="MFA_SETUP",
                        ChallengeResponses={
                            "SECRET_HASH": self._secret_hash(xname),
                            "USERNAME": xname,
                        },
                    )
                )
            case Challenge.Key.MFA:
                xname = encode_name(response["name"])
                return self._tokens(
                    self._client.admin_respond_to_auth_challenge(
                        ClientId=self._client_id,
                        UserPoolId=self._user_pool_id,
                        Session=session,
                        ChallengeName="SOFTWARE_TOKEN_MFA",
                        ChallengeResponses={
                            "SECRET_HASH": self._secret_hash(xname),
                            "USERNAME": xname,
                            "SOFTWARE_TOKEN_MFA_CODE": response["code"],
                        },
                    )
                )

    @private_api
    def refresh_tokens(
        self,
        *,
        refresh_token: str,
    ) -> Tokens:
        return self._tokens(
            self._client.get_tokens_from_refresh_token(
                ClientId=self._client_id,
                ClientSecret=self._client_secret,
                RefreshToken=refresh_token,
            )
        )

    @private_api
    def revoke_tokens(
        self,
        *,
        access_token: str | None = None,
        refresh_token: str | None = None,
    ) -> None:
        match access_token, refresh_token:
            case str() as token, None:
                self._client.global_sign_out(
                    AccessToken=token,
                )
                return
            case None, str() as token:
                self._client.revoke_token(
                    ClientId=self._client_id,
                    ClientSecret=self._client_secret,
                    Token=token,
                )
                return
        raise DomainInvariantViolation(
            "Unexpected combination of access and refresh tokens"
        )
