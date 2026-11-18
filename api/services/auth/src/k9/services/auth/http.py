from typing import Literal

from k9.resolvers.http.requests import Body, Path
from k9.types.common import Name, Password, UserID
from pydantic import BaseModel
from typing_extensions import TypedDict

from .provider import Challenge

__all__ = [
    "Login",
    "LoginChallenge",
    "Logout",
    "Refresh",
    "Verify",
]


class Login(BaseModel, frozen=True):
    name: Body[Name]
    password: Body[Password]


class LoginChallenge(BaseModel, frozen=True):
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
