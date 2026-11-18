from k9.types.common import Name, Password, Role, UserID
from pydantic import BaseModel, HttpUrl

__all__ = [
    "Credentials",
    "User",
]


class User(BaseModel, frozen=True, from_attributes=True):
    id: UserID
    role: Role
    name: Name
    picture: HttpUrl
    enabled: bool


class Credentials(BaseModel, frozen=True):
    id: UserID
    name: Name
    password: Password
