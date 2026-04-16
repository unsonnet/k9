from typing import Any, Mapping

import boto3
from shared.abc import ExceptionMap, private_api
from shared.config import settings
from shared.errors import (
    DomainExpiredToken,
    DomainInvalidCredentials,
    DomainInvariantViolation,
    DomainRateLimited,
    DomainUserNotConfirmed,
    DomainUserNotFound,
    assert_unreachable,
)
from types_boto3_cognito_idp import CognitoIdentityProviderClient

from .base import AuthProvider, Challenge, ChallengeKey, Tokens

# ──── Helper Methods ──────────────────────────────────────────────────────────────────


def _challenge_key(name: str) -> ChallengeKey:
    match name:
        case "NEW_PASSWORD_REQUIRED":
            return ChallengeKey.NEW_PASSWORD
        case "MFA_SETUP":
            return ChallengeKey.NEW_MFA
        case "SOFTWARE_TOKEN_MFA":
            return ChallengeKey.MFA
    raise DomainInvariantViolation()


def _result(response: Mapping[str, Any]) -> Tokens | Challenge:
    match response:
        case {
            "AuthenticationResult": {
                "AccessToken": str(AccessToken),
                "ExpiresIn": int(ExpiresIn),
                "RefreshToken": str(RefreshToken),
                "IdToken": str(IdToken),
            }
        }:
            return Tokens(
                access_token=AccessToken,
                expires_in=ExpiresIn,
                refresh_token=RefreshToken,
                id_token=IdToken,
            )
        case {
            "Session": str(Session),
            "ChallengeName": str(ChallengeName),
            "ChallengeParameters": dict(ChallengeParameters),
        }:
            return Challenge(
                session=Session,
                challenge=_challenge_key(ChallengeName),
                parameters=list(ChallengeParameters.keys()),
            )
    raise DomainInvariantViolation()


def _tokens(response: Mapping[str, Any]) -> Tokens:
    match _result(response):
        case Tokens() as tokens:
            return tokens
        case Challenge():
            raise DomainInvariantViolation()
        case _ as never:
            assert_unreachable(never)


def _none(response: dict) -> None:
    if not response:
        return None
    raise DomainInvariantViolation()


# ──── Cognito Provider ────────────────────────────────────────────────────────────────


class CognitoAuthProvider(AuthProvider):
    _client: CognitoIdentityProviderClient
    _client_id: str
    _client_secret: str

    def __init__(self) -> None:
        self._client = boto3.client("cognito-idp", region_name=settings.aws_region)
        self._client_id = settings.cognito_client_id
        self._client_secret = settings.cognito_client_secret

    # ──── Helper Methods ────

    @property
    def _exception_map(self) -> ExceptionMap:
        cx = self._client.exceptions
        return {
            DomainRateLimited: [
                cx.TooManyRequestsException,
                cx.LimitExceededException,
            ],
            DomainUserNotFound: [
                cx.UserNotFoundException,
            ],
            DomainUserNotConfirmed: [
                cx.UserNotConfirmedException,
            ],
            DomainExpiredToken: [
                cx.ExpiredCodeException,
                cx.PasswordResetRequiredException,
            ],
            DomainInvalidCredentials: [
                cx.NotAuthorizedException,
                cx.InvalidPasswordException,
                cx.CodeMismatchException,
            ],
        }

    def _challenge_new_password(
        self,
        session: str,
        response: dict[str, str],
    ) -> Tokens | Challenge:
        return _result(
            self._client.respond_to_auth_challenge(
                ClientId=self._client_id,
                Session=session,
                ChallengeName="NEW_PASSWORD_REQUIRED",
                ChallengeResponses={
                    "SECRET_HASH": self._client_secret,
                    "USERNAME": response["username"],
                    "NEW_PASSWORD": response["password"],
                },
            )
        )

    def _challenge_new_mfa(
        self,
        session: str,
        response: dict[str, str],
    ) -> Tokens:
        return _tokens(
            self._client.respond_to_auth_challenge(
                ClientId=self._client_id,
                Session=self._client.verify_software_token(
                    Session=session,
                    UserCode=response["code"],
                )["Session"],
                ChallengeName="MFA_SETUP",
                ChallengeResponses={
                    "SECRET_HASH": self._client_secret,
                    "USERNAME": response["username"],
                },
            )
        )

    def _challenge_mfa(
        self,
        session: str,
        response: dict[str, str],
    ) -> Tokens:
        return _tokens(
            self._client.respond_to_auth_challenge(
                ClientId=self._client_id,
                Session=session,
                ChallengeName="SOFTWARE_TOKEN_MFA",
                ChallengeResponses={
                    "SECRET_HASH": self._client_secret,
                    "USERNAME": response["username"],
                    "SOFTWARE_TOKEN_MFA_CODE": response["code"],
                },
            )
        )

    # ──── Private APIs ────

    @private_api
    def authenticate(
        self,
        *,
        username: str,
        password: str,
    ) -> Tokens | Challenge:
        return _result(
            self._client.initiate_auth(
                ClientId=self._client_id,
                AuthFlow="USER_PASSWORD_AUTH",
                AuthParameters={
                    "SECRET_HASH": self._client_secret,
                    "USERNAME": username,
                    "PASSWORD": password,
                },
            )
        )

    @private_api
    def respond_to_challenge(
        self,
        *,
        session: str,
        challenge: ChallengeKey,
        response: dict[str, str],
    ) -> Tokens | Challenge:
        match challenge:
            case ChallengeKey.NEW_PASSWORD:
                return self._challenge_new_password(session, response)
            case ChallengeKey.NEW_MFA:
                return self._challenge_new_mfa(session, response)
            case ChallengeKey.MFA:
                return self._challenge_mfa(session, response)
            case _ as never:
                assert_unreachable(never)

    @private_api
    def refresh_tokens(
        self,
        *,
        refresh_token: str,
    ) -> Tokens:
        return _tokens(
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
                return _none(
                    self._client.global_sign_out(
                        AccessToken=token,
                    )
                )
            case None, str() as token:
                return _none(
                    self._client.revoke_token(
                        ClientId=self._client_id,
                        ClientSecret=self._client_secret,
                        Token=token,
                    )
                )
        raise DomainInvariantViolation()
