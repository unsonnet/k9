from typing import Mapping, Self

from pydantic import Field, field_validator, model_validator
from shared.abc import ApiModel
from shared.http.requests import Body
from shared.providers.cognito import (
    validate_name,
    validate_password,
    validate_session,
    validate_token,
)

from .providers.auth import Challenge, Tokens

__all__ = [
    "Request",
    "Response",
]


# ──── Request Payloads ────────────────────────────────────────────────────────────────


class Request:
    class Login(ApiModel, frozen=True):
        name: Body[str]
        password: Body[str]

        @field_validator("name")
        @classmethod
        def validate_name(cls, value: str) -> str:
            return validate_name(value)

        @field_validator("password")
        @classmethod
        def validate_password(cls, value: str) -> str:
            return validate_password(value)

    class Challenge(ApiModel, frozen=True):
        session: Body[str]
        challenge: Body[Challenge.Key]
        response: Body[Mapping[str, str]] = Field(min_length=1)

        @field_validator("session")
        @classmethod
        def validate_session(cls, value: str) -> str:
            return validate_session(value)

        @field_validator("response")
        @classmethod
        def validate_response(cls, value: Mapping[str, str]) -> Mapping[str, str]:
            match value:
                case {"name": str(name)}:
                    return {**value, "name": validate_name(name)}
                case _:
                    return value

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
            if value is not None:
                return validate_token(value)
            return value

        @model_validator(mode="after")
        def verify_has_token(self) -> Self:
            match self.accessToken, self.refreshToken:
                case None, None:
                    raise ValueError("Either accessToken or refreshToken is required")
                case str(), str():
                    raise ValueError("Either accessToken or refreshToken is required")
                case _:
                    return self


# ──── Response Payloads ───────────────────────────────────────────────────────────────


class Response:
    class Tokens(ApiModel, frozen=True):
        accessToken: str
        expiresIn: int
        refreshToken: str | None = None
        idToken: str | None = None

        @classmethod
        def from_(cls, tokens: Tokens):
            return cls(
                accessToken=tokens.access_token,
                expiresIn=tokens.expires_in,
                refreshToken=tokens.refresh_token,
                idToken=tokens.id_token,
            )

    class Challenge(ApiModel, frozen=True):
        session: str
        challenge: Challenge.Key
        parameters: Mapping[str, str]

        @classmethod
        def from_(cls, challenge: Challenge):
            return cls(
                session=challenge.session,
                challenge=challenge.challenge,
                parameters=challenge.parameters,
            )
