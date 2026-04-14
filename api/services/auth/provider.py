from abc import abstractmethod
from collections.abc import Mapping
from enum import StrEnum
from typing import Any, Literal, cast

import boto3
from shared.abc import (
    BaseProvider,
    DataModel,
    ExceptionMap,
    private_api,
)
from shared.config import settings
from shared.errors import (
    DomainExpiredToken,
    DomainInvalidCredentials,
    DomainInvalidTokens,
    DomainRateLimited,
    DomainUnknown,
    DomainUserNotConfirmed,
    DomainUserNotFound,
)
from types_boto3_cognito_idp import CognitoIdentityProviderClient


class Tokens(DataModel, frozen=True):
    access_token: str
    expires_in: int
    refresh_token: str | None = None
    id_token: str | None = None


class ChallengeKey(StrEnum):
    NEW_PASSWORD = "NEW_PASSWORD"
    MFA_REQUIRED = "MFA_REQUIRED"
    MFA_ENROLL = "MFA_ENROLL"
    MFA_VERIFY = "MFA_VERIFY"


# class Challenge(BaseModel):
#     session: str
#     challenge: ChallengeKey
#     parameters: dict[str, str] | None = None
#     branches: list[str] | None = None


class Challenge(DataModel, frozen=True):
    session: str
    challenge: str


class ChallengeNewPassword(Challenge, frozen=True):
    challenge: Literal["NEW_PASSWORD"]


# ──── Abstract Authentication Provider ────────────────────────────────────────────────


class AuthProvider(BaseProvider):
    @abstractmethod
    def authenticate(
        self,
        username: str,
        password: str,
    ) -> Tokens | Challenge: ...

    @abstractmethod
    def respond_to_challenge(
        self,
        session: str,
        challenge: ChallengeKey,
        response: dict[str, str],
    ) -> Tokens | Challenge: ...

    @abstractmethod
    def forgot_password(
        self,
        username: str,
    ) -> None: ...

    @abstractmethod
    def reset_password(
        self,
        username: str,
        confirmation_code: str,
        new_password: str,
    ) -> None: ...

    @abstractmethod
    def refresh_tokens(
        self,
        refresh_token: str,
    ) -> Tokens: ...

    @abstractmethod
    def revoke_tokens(
        self,
        access_token: str | None = None,
        refresh_token: str | None = None,
    ) -> None: ...


# ──── Cognito Provider ────────────────────────────────────────────────────────────────


class CognitoAuthProvider(AuthProvider):
    _client: CognitoIdentityProviderClient
    _client_id: str

    def __init__(self) -> None:
        self._client_id = settings.cognito_client_id
        self._client = boto3.client("cognito-idp", region_name=settings.aws_region)

    # ──── Helper Methods ────

    @staticmethod
    def _result(
        x: Mapping[str, Any],
    ) -> Tokens | Challenge:
        auth = x.get("AuthenticationResult")
        if auth is not None:
            return Tokens(
                access_token=auth["AccessToken"],
                expires_in=auth["ExpiresIn"],
                refresh_token=auth.get("RefreshToken"),
                id_token=auth.get("IdToken"),
            )

        challenge_name = x.get("ChallengeName")
        session = x.get("Session")
        if challenge_name is not None and session is not None:
            return Challenge(
                challenge=challenge_name,
                session=session,
                parameters=x.get("ChallengeParameters"),
                branches=x.get("AvailableChallenges"),
            )

        raise DomainUnknown("Unexpected Cognito response payload")

    @property
    def exception_map(self) -> ExceptionMap:
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

    # ──── Private APIs ────

    @private_api
    def authenticate(
        self,
        username: str,
        password: str,
    ) -> Tokens | Challenge:
        return self._result(
            self._client.initiate_auth(
                ClientId=self._client_id,
                AuthFlow="USER_PASSWORD_AUTH",
                AuthParameters={
                    "USERNAME": username,
                    "PASSWORD": password,
                },
            )
        )

    @private_api
    def respond_to_challenge(
        self,
        session: str,
        challenge: ChallengeKey,
        parameters: dict[str, str],
    ) -> Tokens | Challenge:
        match challenge:
            case ChallengeKey.NEW_PASSWORD:
                self._client.respond_to_auth_challenge(
                    ClientId=self._client_id,
                    Session=session,
                    ChallengeName="NEW_PASSWORD_REQUIRED",
                    ChallengeResponses={
                        "USERNAME": parameters["USERNAME"],
                        "NEW_PASSWORD": parameters["NEW_PASSWORD"],
                    },
                )
            case ChallengeKey.MFA_REQUIRED:
                self._client.respond_to_auth_challenge(
                    ClientId=self._client_id,
                    Session=session,
                    ChallengeName="SOFTWARE_TOKEN_MFA",
                    ChallengeResponses={
                        "USERNAME": parameters["USERNAME"],
                        "SOFTWARE_TOKEN_MFA_CODE": parameters["MFA_CODE"],
                    },
                )
            case ChallengeKey.MFA_ENROLL:
                self._client.associate_software_token(
                    Session=session,
                )
            case ChallengeKey.MFA_VERIFY:
                self._client.verify_software_token(
                    Session=session,
                    UserCode="",
                )
        return self._result(
            self._client.respond_to_auth_challenge(
                ClientId=self._client_id,
                Session=session,
                ChallengeName=cast(Any, challenge),
                ChallengeResponses=parameters,
            )
        )

    @private_api
    def forgot_password(
        self,
        username: str,
    ) -> None:
        self._client.forgot_password(
            ClientId=self._client_id,
            Username=username,
        )

    @private_api
    def reset_password(
        self,
        username: str,
        confirmation_code: str,
        new_password: str,
    ) -> None:
        self._client.confirm_forgot_password(
            ClientId=self._client_id,
            Username=username,
            ConfirmationCode=confirmation_code,
            Password=new_password,
        )

    @private_api
    def refresh_tokens(
        self,
        refresh_token: str,
    ) -> Tokens:
        match self._result(
            self._client.get_tokens_from_refresh_token(
                RefreshToken=refresh_token,
                ClientId=self._client_id,
            )
        ):
            case Tokens() as tokens:
                return tokens
            case Challenge():
                raise DomainInvalidTokens("Unexpected challenge while refreshing token")

    @private_api
    def revoke_tokens(
        self,
        access_token: str | None = None,
        refresh_token: str | None = None,
    ) -> None:
        match access_token, refresh_token:
            case None, None:
                raise DomainInvalidTokens(
                    "Either access_token or refresh_token must be provided"
                )
            case str() as token:
                self._client.global_sign_out(AccessToken=token)
            case None, str() as token:
                self._client.revoke_token(
                    ClientId=self._client_id,
                    Token=token,
                )
