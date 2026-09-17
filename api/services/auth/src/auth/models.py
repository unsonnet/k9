from pydantic import BaseModel, Field, field_validator
from shared.helpers import validate_name, validate_password, validate_user_id
from shared.http.requests import Body, Path

from .provider import ChallengeKey

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
    class Tokens(BaseModel, frozen=True, from_attributes=True):
        accessToken: str = Field(validation_alias="access_token")
        expiresIn: int = Field(validation_alias="expires_in")
        refreshToken: str | None = Field(validation_alias="refresh_token")
        idToken: str | None = Field(validation_alias="id_token")

    class Challenge(BaseModel, frozen=True, from_attributes=True):
        session: str
        challenge: ChallengeKey

    class MFA(BaseModel, frozen=True, from_attributes=True):
        secret: str
        url: str
