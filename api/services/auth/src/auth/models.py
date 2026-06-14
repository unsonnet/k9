from enum import StrEnum
from typing import Any, Mapping, Self
from urllib.parse import quote

from pydantic import Field, field_validator, model_validator
from shared.abc import ApiModel, DataModel
from shared.errors import DomainInvariantViolation
from shared.http.requests import Body
from shared.providers.cognito import (
    normalize_name,
    validate_name,
    validate_password,
    validate_session,
    validate_token,
)

__all__ = [
    "Request",
    "Response",
]


class ChallengeKey(StrEnum):
    NEW_PASSWORD = "NEW_PASSWORD"
    MFA = "MFA"


# ──── Request Payloads ────────────────────────────────────────────────────────────────


class Request:
    class Login(ApiModel, frozen=True):
        name: Body[str]
        password: Body[str]

        @field_validator("name")
        @classmethod
        def validate_name(cls, value: str) -> str:
            return validate_name(normalize_name(value))

        @field_validator("password")
        @classmethod
        def validate_password(cls, value: str) -> str:
            return validate_password(value)

    class Challenge(ApiModel, frozen=True):
        session: Body[str]
        challenge: Body[ChallengeKey]
        response: Body[dict[str, str]] = Field(min_length=1)

        @field_validator("session")
        @classmethod
        def validate_session(cls, value: str) -> str:
            return validate_session(value)

        @field_validator("response")
        @classmethod
        def validate_response(cls, value: dict[str, str]) -> dict[str, str]:
            if "name" in value:
                value["name"] = validate_name(normalize_name(value["name"]))
            if "password" in value:
                value["password"] = validate_password(value["password"])
            return value

    class Verify(ApiModel, frozen=True):
        code: Body[str] = Field(min_length=1)

    class Refresh(ApiModel, frozen=True):
        refreshToken: Body[str]

        @field_validator("refreshToken")
        @classmethod
        def validate_token(cls, value: str) -> str:
            return validate_token(value)

    class Logout(ApiModel, frozen=True):
        accessToken: Body[str | None] = None
        refreshToken: Body[str | None] = None

        @field_validator("accessToken", "refreshToken")
        @classmethod
        def validate_token(cls, value: str | None) -> str | None:
            return validate_token(value) if value is not None else None

        @model_validator(mode="after")
        def verify_has_token(self) -> Self:
            match self.accessToken, self.refreshToken:
                case (None, None) | (str(), str()):
                    raise ValueError("Either access token or refresh token is required")
            return self


# ──── Provider Models ─────────────────────────────────────────────────────────────────


class Provider:
    class Tokens(DataModel, frozen=True):
        access_token: str
        expires_in: int
        refresh_token: str
        id_token: str

        @classmethod
        def from_cognito(cls, response: Mapping[str, Any]) -> Self:
            match response:
                case {
                    "AuthenticationResult": {
                        "AccessToken": str(access_token),
                        "ExpiresIn": int(expires_in),
                        "RefreshToken": str(refresh_token),
                        "IdToken": str(id_token),
                    }
                }:
                    return cls(
                        access_token=access_token,
                        expires_in=expires_in,
                        refresh_token=refresh_token,
                        id_token=id_token,
                    )
            raise DomainInvariantViolation(f"Unexpected cognito tokens: {response}")

    class Challenge(DataModel, frozen=True):
        session: str
        challenge: ChallengeKey

        @classmethod
        def from_cognito(cls, response: Mapping[str, Any]) -> Self:
            match response:
                case {"Session": str(session), "ChallengeName": str(challenge)}:
                    match challenge:
                        case "NEW_PASSWORD_REQUIRED":
                            return cls(
                                session=session,
                                challenge=ChallengeKey.NEW_PASSWORD,
                            )
                        case "SOFTWARE_TOKEN_MFA":
                            return cls(
                                session=session,
                                challenge=ChallengeKey.MFA,
                            )
            raise DomainInvariantViolation(f"Unexpected cognito challenge: {response}")

    class MFA(DataModel, frozen=True):
        secret: str
        url: str

        @classmethod
        def from_cognito(cls, response: Mapping[str, Any], *, name: str) -> Self:
            match response:
                case {
                    "SecretCode": str(secret),
                }:
                    issuer = quote("Amazon Web Services")
                    label = f"{issuer}:{quote(f'K9 - {name}')}"
                    return cls(
                        secret=secret,
                        url=f"otpauth://totp/{label}?secret={secret}&issuer={issuer}",
                    )
            raise DomainInvariantViolation(f"Unexpected cognito MFA: {response}")


# ──── Response Payloads ───────────────────────────────────────────────────────────────


class Response:
    class Tokens(ApiModel, frozen=True):
        accessToken: str
        expiresIn: int
        refreshToken: str | None = None
        idToken: str | None = None

        @classmethod
        def from_provider(cls, tokens: Provider.Tokens):
            return cls(
                accessToken=tokens.access_token,
                expiresIn=tokens.expires_in,
                refreshToken=tokens.refresh_token,
                idToken=tokens.id_token,
            )

    class Challenge(ApiModel, frozen=True):
        session: str
        challenge: ChallengeKey

        @classmethod
        def from_provider(cls, challenge: Provider.Challenge):
            return cls(
                session=challenge.session,
                challenge=challenge.challenge,
            )

    class MFA(ApiModel, frozen=True):
        secret: str
        url: str

        @classmethod
        def from_provider(cls, mfa: Provider.MFA):
            return cls(
                secret=mfa.secret,
                url=mfa.url,
            )
