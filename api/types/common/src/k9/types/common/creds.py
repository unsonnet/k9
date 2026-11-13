import re
import secrets
import string
import unicodedata
from typing import Annotated, Literal, NewType, Self

from pydantic import AfterValidator, BaseModel, StringConstraints

from .base import ValidatedStr
from .ids import UserID

__all__ = [
    "Caller",
    "Name",
    "Password",
    "Role",
]


def _normalize_name(name: str) -> str:
    name = unicodedata.normalize("NFKC", name)
    return re.sub(r"\s+", " ", name.strip()).casefold()


Name = Annotated[
    NewType("Name", str),
    AfterValidator(_normalize_name),
    StringConstraints(min_length=1, max_length=1024),
]


class Password(ValidatedStr):
    _pattern = re.compile(
        r"\A(?=.*[A-Z])(?=.*[a-z])(?=.*\d)"
        r"(?=.*[!@#$%^&*()_=+\[\]{}:,.?\-])\S+\Z"
    )
    _min_length = 8
    _max_length = 256

    @classmethod
    def random(cls, length: int = 24) -> Self:
        special = "!@#$%^&*()_=+[]{}:,.?-"
        alphabet = string.ascii_letters + string.digits + special
        chars = [
            secrets.choice(string.ascii_uppercase),
            secrets.choice(string.ascii_lowercase),
            secrets.choice(string.digits),
            secrets.choice(special),
        ]
        chars.extend(secrets.choice(alphabet) for _ in range(length - len(chars)))
        secrets.SystemRandom().shuffle(chars)
        return cls("".join(chars))


type Role = Literal["admin", "user"]


class Caller(BaseModel):
    id: UserID
    role: Role
    name: Name
    token: str

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"
