import importlib
from collections.abc import Callable
from typing import Any

import pytest
from auth.providers.auth import Challenge, Tokens
from shared.errors import DomainForbidden, DomainRateLimited, DomainUnauthorized

from tests.helpers import (
    ProviderMethod,
    assert_body,
    assert_no_body,
    assert_problem,
    assert_status,
)

pytestmark = pytest.mark.integration


# ──── Helpers ─────────────────────────────────────────────────────────────────────────

LOGIN_ERRORS = [
    pytest.param(
        DomainUnauthorized(),
        401,
        "Unauthorized",
        "Invalid credentials",
        id="unauthorized",
    ),
    pytest.param(DomainForbidden(), 403, "Forbidden", None, id="forbidden"),
    pytest.param(
        DomainRateLimited(),
        429,
        "Too Many Requests",
        None,
        id="rate-limited",
    ),
]

CHALLENGE_ERRORS = [
    pytest.param(
        DomainUnauthorized(),
        401,
        "Unauthorized",
        "Invalid challenge response",
        id="unauthorized",
    ),
    pytest.param(DomainForbidden(), 403, "Forbidden", None, id="forbidden"),
    pytest.param(
        DomainRateLimited(),
        429,
        "Too Many Requests",
        None,
        id="rate-limited",
    ),
]

REFRESH_ERRORS = [
    pytest.param(
        DomainUnauthorized(),
        401,
        "Unauthorized",
        "Invalid refresh token",
        id="unauthorized",
    ),
    pytest.param(DomainForbidden(), 403, "Forbidden", None, id="forbidden"),
    pytest.param(
        DomainRateLimited(),
        429,
        "Too Many Requests",
        None,
        id="rate-limited",
    ),
]

LOGOUT_ERRORS = [
    pytest.param(DomainForbidden(), 403, "Forbidden", id="forbidden"),
    pytest.param(DomainRateLimited(), 429, "Too Many Requests", id="rate-limited"),
]


class FakeAuthProvider:
    def __init__(self) -> None:
        self.authenticate = ProviderMethod()
        self.respond_to_challenge = ProviderMethod()
        self.refresh_tokens = ProviderMethod()
        self.revoke_tokens = ProviderMethod(result=None)


def tokens_body(
    *,
    access_token: str = "access-token",
    expires_in: int = 3600,
    refresh_token: str | None = "refresh-token",
    id_token: str | None = "id-token",
) -> dict[str, Any]:
    return {
        "accessToken": access_token,
        "expiresIn": expires_in,
        "refreshToken": refresh_token,
        "idToken": id_token,
    }


def challenge_body(
    *,
    session: str = "session-token-1234567890",
    challenge: str = "MFA",
    parameters: dict[str, str] | None = None,
) -> dict[str, Any]:
    return {
        "session": session,
        "challenge": challenge,
        "parameters": parameters or {},
    }


# ──── Fixtures ────────────────────────────────────────────────────────────────────────


@pytest.fixture
def auth_provider() -> FakeAuthProvider:
    return FakeAuthProvider()


@pytest.fixture
def auth_handler_module(
    monkeypatch: pytest.MonkeyPatch,
    auth_provider: FakeAuthProvider,
):
    import auth.providers.auth as auth_provider_module

    monkeypatch.setattr(
        auth_provider_module,
        "CognitoAuthProvider",
        lambda: auth_provider,
    )

    import auth.handler as handler

    return importlib.reload(handler)


@pytest.fixture
def invoke_auth_api(
    auth_handler_module,
    apigw_event,
    lambda_context,
) -> Callable[[str, dict[str, Any]], dict[str, Any]]:
    def invoke(path: str, body: dict[str, Any]) -> dict[str, Any]:
        return auth_handler_module.lambda_handler(
            apigw_event(path, body),
            lambda_context,
        )

    return invoke


@pytest.fixture
def tokens_record() -> Tokens:
    return Tokens(
        access_token="access-token",
        expires_in=3600,
        refresh_token="refresh-token",
        id_token="id-token",
    )


@pytest.fixture
def challenge_record() -> Challenge:
    return Challenge(
        session="session-token-1234567890",
        challenge=Challenge.Key.MFA,
        parameters={},
    )


# ──── POST /auth/login ────────────────────────────────────────────────────────────────


class TestLogin:
    def test_returns_tokens(
        self,
        auth_provider: FakeAuthProvider,
        invoke_auth_api,
        tokens_record: Tokens,
    ) -> None:
        auth_provider.authenticate.result = tokens_record

        response = invoke_auth_api(
            "/auth/login",
            {
                "name": "alice",
                "password": "Passw0rd!",
            },
        )

        assert_status(response, 200)
        assert_body(response, tokens_body())
        assert auth_provider.authenticate.calls == [
            {
                "name": "alice",
                "password": "Passw0rd!",
            }
        ]

    def test_returns_challenge(
        self,
        auth_provider: FakeAuthProvider,
        invoke_auth_api,
        challenge_record: Challenge,
    ) -> None:
        auth_provider.authenticate.result = challenge_record

        response = invoke_auth_api(
            "/auth/login",
            {
                "name": "alice",
                "password": "Passw0rd!",
            },
        )

        assert_status(response, 202)
        assert_body(response, challenge_body())
        assert auth_provider.authenticate.calls == [
            {
                "name": "alice",
                "password": "Passw0rd!",
            }
        ]

    @pytest.mark.parametrize(
        "body",
        [
            pytest.param(
                {
                    "password": "Passw0rd!",
                },
                id="missing-name",
            ),
            pytest.param(
                {
                    "name": "alice",
                },
                id="missing-password",
            ),
            pytest.param(
                {
                    "name": "alice",
                    "password": "short",
                },
                id="invalid-password",
            ),
        ],
    )
    def test_rejects_invalid_body(
        self,
        invoke_auth_api,
        body: dict[str, Any],
    ) -> None:
        response = invoke_auth_api("/auth/login", body)

        assert_status(response, 422)

    @pytest.mark.parametrize(
        ("provider_error", "expected_status", "expected_title", "expected_detail"),
        LOGIN_ERRORS,
    )
    def test_maps_provider_errors(
        self,
        auth_provider: FakeAuthProvider,
        invoke_auth_api,
        provider_error: Exception,
        expected_status: int,
        expected_title: str,
        expected_detail: str | None,
    ) -> None:
        auth_provider.authenticate.error = provider_error

        response = invoke_auth_api(
            "/auth/login",
            {
                "name": "alice",
                "password": "Passw0rd!",
            },
        )

        assert_problem(
            response,
            status=expected_status,
            title=expected_title,
            detail=expected_detail,
        )


# ──── POST /auth/challenge ────────────────────────────────────────────────────────────


class TestChallenge:
    def test_returns_tokens(
        self,
        auth_provider: FakeAuthProvider,
        invoke_auth_api,
        tokens_record: Tokens,
    ) -> None:
        auth_provider.respond_to_challenge.result = tokens_record

        response = invoke_auth_api(
            "/auth/challenge",
            {
                "session": "session-token-1234567890",
                "challenge": "MFA",
                "response": {
                    "name": "alice",
                    "code": "123456",
                },
            },
        )

        assert_status(response, 200)
        assert_body(response, tokens_body())
        assert auth_provider.respond_to_challenge.calls == [
            {
                "session": "session-token-1234567890",
                "challenge": Challenge.Key.MFA,
                "response": {
                    "name": "alice",
                    "code": "123456",
                },
            }
        ]

    def test_returns_followup_challenge(
        self,
        auth_provider: FakeAuthProvider,
        invoke_auth_api,
    ) -> None:
        auth_provider.respond_to_challenge.result = Challenge(
            session="session-token-1234567890",
            challenge=Challenge.Key.NEW_MFA,
            parameters={"secret": "ABCDEF"},
        )

        response = invoke_auth_api(
            "/auth/challenge",
            {
                "session": "session-token-1234567890",
                "challenge": "MFA",
                "response": {
                    "name": "alice",
                    "code": "123456",
                },
            },
        )

        assert_status(response, 202)
        assert_body(
            response,
            challenge_body(
                challenge="NEW_MFA",
                parameters={"secret": "ABCDEF"},
            ),
        )

    def test_passes_normalized_body_to_provider(
        self,
        auth_provider: FakeAuthProvider,
        invoke_auth_api,
        tokens_record: Tokens,
    ) -> None:
        auth_provider.respond_to_challenge.result = tokens_record

        response = invoke_auth_api(
            "/auth/challenge",
            {
                "session": "session-token-1234567890",
                "challenge": "MFA",
                "response": {
                    "name": "  ALICE  ",
                    "code": "123456",
                },
            },
        )

        assert_status(response, 200)
        assert auth_provider.respond_to_challenge.calls == [
            {
                "session": "session-token-1234567890",
                "challenge": Challenge.Key.MFA,
                "response": {
                    "name": "alice",
                    "code": "123456",
                },
            }
        ]

    @pytest.mark.parametrize(
        "body",
        [
            pytest.param(
                {
                    "challenge": "MFA",
                    "response": {
                        "name": "alice",
                        "code": "123456",
                    },
                },
                id="missing-session",
            ),
            pytest.param(
                {
                    "session": "short-session",
                    "challenge": "MFA",
                    "response": {
                        "name": "alice",
                        "code": "123456",
                    },
                },
                id="invalid-session",
            ),
            pytest.param(
                {
                    "session": "session-token-1234567890",
                    "challenge": "SMS",
                    "response": {
                        "name": "alice",
                        "code": "123456",
                    },
                },
                id="invalid-challenge",
            ),
            pytest.param(
                {
                    "session": "session-token-1234567890",
                    "challenge": "MFA",
                    "response": {},
                },
                id="empty-response",
            ),
        ],
    )
    def test_rejects_invalid_body(
        self,
        invoke_auth_api,
        body: dict[str, Any],
    ) -> None:
        response = invoke_auth_api("/auth/challenge", body)

        assert_status(response, 422)

    @pytest.mark.parametrize(
        ("provider_error", "expected_status", "expected_title", "expected_detail"),
        CHALLENGE_ERRORS,
    )
    def test_maps_provider_errors(
        self,
        auth_provider: FakeAuthProvider,
        invoke_auth_api,
        provider_error: Exception,
        expected_status: int,
        expected_title: str,
        expected_detail: str | None,
    ) -> None:
        auth_provider.respond_to_challenge.error = provider_error

        response = invoke_auth_api(
            "/auth/challenge",
            {
                "session": "session-token-1234567890",
                "challenge": "MFA",
                "response": {
                    "name": "alice",
                    "code": "123456",
                },
            },
        )

        assert_problem(
            response,
            status=expected_status,
            title=expected_title,
            detail=expected_detail,
        )


# ──── POST /auth/refresh ──────────────────────────────────────────────────────────────


class TestRefresh:
    def test_returns_tokens(
        self,
        auth_provider: FakeAuthProvider,
        invoke_auth_api,
        tokens_record: Tokens,
    ) -> None:
        auth_provider.refresh_tokens.result = tokens_record

        response = invoke_auth_api(
            "/auth/refresh",
            {
                "refreshToken": "refresh-token",
            },
        )

        assert_status(response, 200)
        assert_body(response, tokens_body())
        assert auth_provider.refresh_tokens.calls == [
            {
                "refresh_token": "refresh-token",
            }
        ]

    @pytest.mark.parametrize(
        "body",
        [
            pytest.param({}, id="missing-refresh-token"),
            pytest.param(
                {
                    "refreshToken": "token with spaces",
                },
                id="invalid-refresh-token",
            ),
        ],
    )
    def test_rejects_invalid_body(
        self,
        invoke_auth_api,
        body: dict[str, Any],
    ) -> None:
        response = invoke_auth_api("/auth/refresh", body)

        assert_status(response, 422)

    @pytest.mark.parametrize(
        ("provider_error", "expected_status", "expected_title", "expected_detail"),
        REFRESH_ERRORS,
    )
    def test_maps_provider_errors(
        self,
        auth_provider: FakeAuthProvider,
        invoke_auth_api,
        provider_error: Exception,
        expected_status: int,
        expected_title: str,
        expected_detail: str | None,
    ) -> None:
        auth_provider.refresh_tokens.error = provider_error

        response = invoke_auth_api(
            "/auth/refresh",
            {
                "refreshToken": "refresh-token",
            },
        )

        assert_problem(
            response,
            status=expected_status,
            title=expected_title,
            detail=expected_detail,
        )


# ──── POST /auth/logout ───────────────────────────────────────────────────────────────


class TestLogout:
    @pytest.mark.parametrize(
        ("body", "expected_provider_call"),
        [
            pytest.param(
                {
                    "accessToken": "access-token",
                },
                {
                    "access_token": "access-token",
                    "refresh_token": None,
                },
                id="access-token",
            ),
            pytest.param(
                {
                    "refreshToken": "refresh-token",
                },
                {
                    "access_token": None,
                    "refresh_token": "refresh-token",
                },
                id="refresh-token",
            ),
        ],
    )
    def test_returns_no_content(
        self,
        auth_provider: FakeAuthProvider,
        invoke_auth_api,
        body: dict[str, Any],
        expected_provider_call: dict[str, Any],
    ) -> None:
        response = invoke_auth_api("/auth/logout", body)

        assert_status(response, 204)
        assert_no_body(response)
        assert auth_provider.revoke_tokens.calls == [expected_provider_call]

    def test_is_idempotent(
        self,
        auth_provider: FakeAuthProvider,
        invoke_auth_api,
    ) -> None:
        auth_provider.revoke_tokens.error = DomainUnauthorized()

        response = invoke_auth_api(
            "/auth/logout",
            {
                "accessToken": "access-token",
            },
        )

        assert_status(response, 204)
        assert_no_body(response)

    @pytest.mark.parametrize(
        "body",
        [
            pytest.param({}, id="missing-tokens"),
            pytest.param(
                {
                    "accessToken": "access-token",
                    "refreshToken": "refresh-token",
                },
                id="both-tokens",
            ),
            pytest.param(
                {
                    "refreshToken": "invalid token",
                },
                id="invalid-refresh-token",
            ),
        ],
    )
    def test_rejects_invalid_body(
        self,
        invoke_auth_api,
        body: dict[str, Any],
    ) -> None:
        response = invoke_auth_api("/auth/logout", body)

        assert_status(response, 422)

    @pytest.mark.parametrize(
        ("provider_error", "expected_status", "expected_title"),
        LOGOUT_ERRORS,
    )
    def test_maps_provider_errors(
        self,
        auth_provider: FakeAuthProvider,
        invoke_auth_api,
        provider_error: Exception,
        expected_status: int,
        expected_title: str,
    ) -> None:
        auth_provider.revoke_tokens.error = provider_error

        response = invoke_auth_api(
            "/auth/logout",
            {
                "accessToken": "access-token",
            },
        )

        assert_problem(
            response,
            status=expected_status,
            title=expected_title,
        )


# ──── Routing ─────────────────────────────────────────────────────────────────────────


class TestRouting:
    @pytest.mark.parametrize(
        ("method", "path"),
        [
            pytest.param("GET", "/auth/login", id="login"),
            pytest.param("GET", "/auth/challenge", id="challenge"),
            pytest.param("GET", "/auth/refresh", id="refresh"),
            pytest.param("GET", "/auth/logout", id="logout"),
        ],
    )
    def test_rejects_unsupported_methods(
        self,
        auth_handler_module,
        apigw_event,
        lambda_context,
        method: str,
        path: str,
    ) -> None:
        response = auth_handler_module.lambda_handler(
            apigw_event(path, {}, method=method),
            lambda_context,
        )

        assert_status(response, 405)

    def test_returns_not_found_for_unknown_route(
        self,
        auth_handler_module,
        apigw_event,
        lambda_context,
    ) -> None:
        response = auth_handler_module.lambda_handler(
            apigw_event("/auth/unknown", {}, method="POST"),
            lambda_context,
        )

        assert_status(response, 404)
