from typing import Self

from pydantic import BaseModel, field_validator
from shared.helpers import validate_name, validate_password, validate_user_id
from shared.http.requests import Body, Path

from .provider import MFA, Challenge, ChallengeKey, Tokens

__all__ = [
    "Request",
    "Response",
]


# ──── Request Payloads ────────────────────────────────────────────────────────────────


class Request:
    class Login(BaseModel, frozen=True):
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

    class Challenge(BaseModel, frozen=True):
        session: Body[str]
        challenge: Body[ChallengeKey]
        response: Body[dict[str, str]]

        @field_validator("response")
        @classmethod
        def validate_response(cls, value: dict[str, str]) -> dict[str, str]:
            if "name" in value:
                value["name"] = validate_name(value["name"])
            if "password" in value:
                value["password"] = validate_password(value["password"])
            return value

    class Verify(BaseModel, frozen=True):
        code: Body[str]

    class Refresh(BaseModel, frozen=True):
        refreshToken: Body[str]

    class Logout(BaseModel, frozen=True):
        id: Path[str]

        @field_validator("id")
        @classmethod
        def validate_id(cls, value: str) -> str:
            return value if value == "me" else validate_user_id(value)


# ──── Response Payloads ───────────────────────────────────────────────────────────────


class Response:
    class Tokens(BaseModel, frozen=True):
        accessToken: str
        expiresIn: int
        refreshToken: str | None
        idToken: str | None

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
