import importlib

import pytest
from auth.providers.auth.base import Challenge, Tokens


class DummyAuthProvider:
    def __init__(self) -> None:
        self.authenticate_result: Tokens | Challenge | None = None
        self.authenticate_error: Exception | None = None

        self.challenge_result: Tokens | Challenge | None = None
        self.challenge_error: Exception | None = None

        self.refresh_result: Tokens | None = None
        self.refresh_error: Exception | None = None

        self.revoke_error: Exception | None = None

    def authenticate(self, *, username: str, password: str) -> Tokens | Challenge:
        if self.authenticate_error is not None:
            raise self.authenticate_error
        if self.authenticate_result is None:
            raise AssertionError("authenticate_result not configured")
        return self.authenticate_result

    def respond_to_challenge(
        self,
        *,
        session: str,
        challenge: Challenge.Key,
        response: dict[str, str],
    ) -> Tokens | Challenge:
        if self.challenge_error is not None:
            raise self.challenge_error
        if self.challenge_result is None:
            raise AssertionError("challenge_result not configured")
        return self.challenge_result

    def refresh_tokens(self, *, refresh_token: str) -> Tokens:
        if self.refresh_error is not None:
            raise self.refresh_error
        if self.refresh_result is None:
            raise AssertionError("refresh_result not configured")
        return self.refresh_result

    def revoke_tokens(
        self,
        *,
        access_token: str | None = None,
        refresh_token: str | None = None,
    ) -> None:
        if self.revoke_error is not None:
            raise self.revoke_error


@pytest.fixture
def dummy_provider() -> DummyAuthProvider:
    return DummyAuthProvider()


@pytest.fixture
def auth_handler_module(
    monkeypatch: pytest.MonkeyPatch,
    dummy_provider: DummyAuthProvider,
):
    import auth.providers.auth as auth

    monkeypatch.setattr(auth, "CognitoAuthProvider", lambda: dummy_provider)

    import auth.handler as handler

    return importlib.reload(handler)
