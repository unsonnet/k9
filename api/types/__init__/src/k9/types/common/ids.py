import re
import secrets
import string
from datetime import datetime, timezone
from typing import Self

from k9.types.base import ValidatedStr

__all__ = [
    "DateID",
    "ResourceID",
    "SubresourceID",
    "UserID",
]


def _random_chars(alphabet: str, length: int) -> str:
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _digits(length: int) -> str:
    return _random_chars(string.digits, length)


class UserID(ValidatedStr):
    _pattern = re.compile(r"[a-z]{3}\d{3}")

    @classmethod
    def random(cls) -> Self:
        return cls(_random_chars(string.ascii_lowercase, 3) + _digits(3))


class ResourceID(ValidatedStr):
    _pattern = re.compile(r"\d{3}-\d{3}-\d{3}")

    @classmethod
    def random(cls) -> Self:
        return cls("-".join(_digits(3) for _ in range(3)))


class SubresourceID(ValidatedStr):
    _pattern = re.compile(r"\d{4}")

    @classmethod
    def random(cls) -> Self:
        return cls(_digits(4))


class DateID(ValidatedStr):
    _pattern = re.compile(r"\d{4}-\d{2}-\d{2}")

    @classmethod
    def _validate(cls, value: str) -> str:
        value = super()._validate(value)
        return datetime.strptime(value, "%Y-%m-%d").date().isoformat()

    @classmethod
    def now(cls) -> Self:
        return cls(datetime.now(timezone.utc).date().isoformat())
