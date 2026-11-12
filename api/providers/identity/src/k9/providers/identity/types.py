from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel
from types_boto3_cognito_idp.literals import ChallengeNameTypeType

__all__ = [
    "Challenge",
    "MFA",
    "Page",
    "STANDARD_ATTRIBUTES",
    "Tokens",
    "User",
]


STANDARD_ATTRIBUTES: set[str] = {
    "address",
    "birthdate",
    "email",
    "family_name",
    "gender",
    "given_name",
    "locale",
    "middle_name",
    "name",
    "nickname",
    "phone_number",
    "picture",
    "preferred_username",
    "profile",
    "updated_at",
    "website",
    "zoneinfo",
}


@dataclass(frozen=True, slots=True)
class Challenge:
    type Key = ChallengeNameTypeType
    session: str
    challenge: Key


@dataclass(frozen=True, slots=True)
class MFA:
    secret: str
    url: str


@dataclass(frozen=True, slots=True)
class Tokens:
    access_token: str
    expires_in: int
    refresh_token: str | None
    id_token: str | None


@dataclass(frozen=True, slots=True)
class User:
    username: str
    enabled: bool
    attributes: dict[str, str | None]
    created_at: datetime
    updated_at: datetime | None
    last_login_at: datetime | None

    def __getattr__(self, key: str) -> str | None:
        return self.attributes.get(key)


@dataclass(frozen=True, slots=True)
class Page[T]:
    items: list[T]
    cursor: str | None

    def hydrate[M: BaseModel](self, model: type[M]) -> Page[M]:
        return Page(
            items=[model.model_validate(item) for item in self.items],
            cursor=self.cursor,
        )
