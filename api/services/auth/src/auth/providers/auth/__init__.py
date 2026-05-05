from typing import Mapping, Protocol

from .base import Challenge, Tokens
from .cognito import CognitoAuthProvider

__all__ = [
    "Challenge",
    "Tokens",
    "AuthProvider",
    "CognitoAuthProvider",
]


class AuthProvider(Protocol):
    def authenticate(
        self,
        *,
        username: str,
        password: str,
    ) -> Tokens | Challenge: ...

    def respond_to_challenge(
        self,
        *,
        session: str,
        challenge: Challenge.Key,
        response: Mapping[str, str],
    ) -> Tokens | Challenge: ...

    def refresh_tokens(
        self,
        *,
        refresh_token: str,
    ) -> Tokens: ...

    def revoke_tokens(
        self,
        *,
        access_token: str | None = None,
        refresh_token: str | None = None,
    ) -> None: ...
