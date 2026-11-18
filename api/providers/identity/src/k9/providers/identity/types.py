from __future__ import annotations

from datetime import datetime

from k9.types.base import Page, ResourceModel
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


class Challenge(ResourceModel, frozen=True):
    type Key = ChallengeNameTypeType
    session: str
    challenge: Key


class MFA(ResourceModel, frozen=True):
    secret: str
    url: str


class Tokens(ResourceModel, frozen=True):
    access_token: str
    expires_in: int
    refresh_token: str | None
    id_token: str | None


class User(ResourceModel, frozen=True):
    username: str
    enabled: bool
    attributes: dict[str, str | None]
    created_at: datetime
    updated_at: datetime | None
    last_login_at: datetime | None

    def __getattr__(self, key: str) -> str | None:
        return self.attributes.get(key)
