from k9.types.common import Name, Password, Role, S3Url, UserID
from pydantic import BaseModel

__all__ = [
    "Credentials",
    "User",
]


class User(BaseModel, frozen=True, from_attributes=True):
    id: UserID
    role: Role
    name: Name
    picture: S3Url
    enabled: bool


class Credentials(BaseModel, frozen=True):
    id: UserID
    name: Name
    password: Password
