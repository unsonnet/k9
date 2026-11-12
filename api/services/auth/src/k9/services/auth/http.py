from typing import Literal

from k9.resolvers.http.requests import Body, Path
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from .provider import Challenge, Name, Password, UserID

__all__ = [
    "Request",
    "Response",
]


# ──── Request Payloads ────────────────────────────────────────────────────────────────


class Request:
    class Login(BaseModel, frozen=True):
        name: Body[Name]
        password: Body[Password]

    class Challenge(BaseModel, frozen=True):
        class Options(TypedDict, total=False, closed=True):
            name: Name
            password: Password
            code: str

        session: Body[str]
        challenge: Body[Challenge.Key]
        response: Body[Options]

    class Verify(BaseModel, frozen=True):
        code: Body[str]

    class Refresh(BaseModel, frozen=True):
        refreshToken: Body[str]

    class Logout(BaseModel, frozen=True):
        id: Path[UserID | Literal["me"]]


# ──── Response Payloads ───────────────────────────────────────────────────────────────


class Response:
    class Tokens(BaseModel, frozen=True, from_attributes=True):
        accessToken: str = Field(validation_alias="access_token")
        expiresIn: int = Field(validation_alias="expires_in")
        refreshToken: str | None = Field(validation_alias="refresh_token")
        idToken: str | None = Field(validation_alias="id_token")

    class Challenge(BaseModel, frozen=True, from_attributes=True):
        session: str
        challenge: Challenge.Key

    class MFA(BaseModel, frozen=True, from_attributes=True):
        secret: str
        url: str
