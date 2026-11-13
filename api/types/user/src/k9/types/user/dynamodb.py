from k9.types.common import Name, Role, UserID
from pydantic import BaseModel, HttpUrl

__all__ = [
    "User",
]


class User(BaseModel, frozen=True, from_attributes=True):
    id: UserID
    role: Role
    name: Name
    picture: HttpUrl
    enabled: bool
