from abc import abstractmethod
from enum import StrEnum
from typing import Mapping

from shared.abc import BaseProvider, DataModel, private_api


class Tokens(DataModel, frozen=True):
    access_token: str
    expires_in: int
    refresh_token: str
    id_token: str


class Challenge(DataModel, frozen=True):
    class Key(StrEnum):
        NEW_PASSWORD = "NEW_PASSWORD"
        NEW_MFA = "NEW_MFA"
        MFA = "MFA"

    session: str
    challenge: Key
    parameters: Mapping[str, str]


# ──── Abstract Authentication Provider ────────────────────────────────────────────────


class AuthProvider(BaseProvider):
    # ──── Private APIs ────

    @private_api
    @abstractmethod
    def authenticate(
        self,
        *,
        username: str,
        password: str,
    ) -> Tokens | Challenge: ...

    @private_api
    @abstractmethod
    def respond_to_challenge(
        self,
        *,
        session: str,
        challenge: Challenge.Key,
        response: Mapping[str, str],
    ) -> Tokens | Challenge: ...

    @private_api
    @abstractmethod
    def refresh_tokens(
        self,
        *,
        refresh_token: str,
    ) -> Tokens: ...

    @private_api
    @abstractmethod
    def revoke_tokens(
        self,
        *,
        access_token: str | None = None,
        refresh_token: str | None = None,
    ) -> None: ...
