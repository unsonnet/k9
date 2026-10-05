from dataclasses import dataclass

__all__ = [
    "UserCredentials",
]


@dataclass(frozen=True, slots=True)
class UserCredentials:
    id: str
    name: str
    password: str
