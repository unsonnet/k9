from enum import StrEnum
from typing import Self

from pydantic import BaseModel, Field, field_validator, model_validator
from shared.http.requests import Body
from shared.provider.auth import validate_session, validate_token
from shared.provider.user import normalize_name, validate_name, validate_password

__all__ = [
    "Tokens",
    "ChallengeKey",
    "Challenge",
    "MFA",
    "Request",
    "Response",
]


class Tokens(BaseModel, frozen=True):
    access_token: str
    expires_in: int
    refresh_token: str
    id_token: str


class ChallengeKey(StrEnum):
    NEW_PASSWORD = "NEW_PASSWORD"
    MFA = "MFA"


class Challenge(BaseModel, frozen=True):
    session: str
    challenge: ChallengeKey


class MFA(BaseModel, frozen=True):
    secret: str
    url: str


# ──── Request Payloads ────────────────────────────────────────────────────────────────


class Request:
    class Login(BaseModel, frozen=True):
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

    class Challenge(BaseModel, frozen=True):
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

    class Verify(BaseModel, frozen=True):
        code: Body[str] = Field(min_length=1)

    class Refresh(BaseModel, frozen=True):
        refreshToken: Body[str]

        @field_validator("refreshToken")
        @classmethod
        def validate_token(cls, value: str) -> str:
            return validate_token(value)

    class Logout(BaseModel, frozen=True):
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


# ──── Response Payloads ───────────────────────────────────────────────────────────────


class Response:
    class Tokens(BaseModel, frozen=True):
        accessToken: str
        expiresIn: int
        refreshToken: str | None = None
        idToken: str | None = None

        @classmethod
        def pack(cls, tokens: Tokens) -> Self:
            return cls(
                accessToken=tokens.access_token,
                expiresIn=tokens.expires_in,
                refreshToken=tokens.refresh_token,
                idToken=tokens.id_token,
            )

    class Challenge(BaseModel, frozen=True):
        session: str
        challenge: ChallengeKey

        @classmethod
        def pack(cls, challenge: Challenge) -> Self:
            return cls(
                session=challenge.session,
                challenge=challenge.challenge,
            )

    class MFA(BaseModel, frozen=True):
        secret: str
        url: str

        @classmethod
        def pack(cls, mfa: MFA) -> Self:
            return cls(
                secret=mfa.secret,
                url=mfa.url,
            )
