from dataclasses import dataclass

from shared.http.requests import ImageFormat

__all__ = [
    "UserCredentials",
    "ImageFormat",
]


@dataclass(frozen=True, slots=True)
class UserCredentials:
    id: str
    name: str
    password: str
