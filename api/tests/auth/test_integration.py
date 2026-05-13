import importlib
from collections.abc import Callable
from typing import Any

import pytest
from auth.providers.auth import Challenge, Tokens
from shared.errors import (
    DomainForbidden,
    DomainInvalidCredentials,
    DomainInvariantViolation,
    DomainRateLimited,
    DomainUnauthorized,
)

from tests.helpers import (
    ProviderMethod,
    assert_body,
    assert_no_body,
    assert_problem,
    assert_status,
)

pytestmark = pytest.mark.integration


# ──── Helpers ─────────────────────────────────────────────────────────────────────────


class FakeAuthProvider:
    def __init__(self) -> None:
        self.authenticate = ProviderMethod()
        self.respond_to_challenge = ProviderMethod()
        self.refresh_tokens = ProviderMethod()
        self.revoke_tokens = ProviderMethod(result=None)


AUTH_ERRORS = [
    pytest.param(
        DomainForbidden(),
        403,
        "Forbidden",
        None,
        id="forbidden",
    ),
    pytest.param(
        DomainRateLimited(),
        429,
        "Too Many Requests",
        None,
        id="rate-limited",
    ),
]

LOGIN_ERRORS = [
    pytest.param(
        DomainInvalidCredentials(),
        401,
        "Unauthorized",
        "Invalid credentials",
        id="invalid-credentials",
    ),
    pytest.param(
        DomainUnauthorized(),
        401,
        "Unauthorized",
        "Invalid credentials",
        id="unauthorized",
    ),
    *AUTH_ERRORS,
]

CHALLENGE_ERRORS = [
    pytest.param(
        DomainInvalidCredentials(),
        401,
        "Unauthorized",
        "Invalid challenge response",
        id="invalid-challenge-response",
    ),
    pytest.param(
        DomainUnauthorized(),
        401,
        "Unauthorized",
        "Invalid challenge response",
        id="unauthorized",
    ),
    *AUTH_ERRORS,
]

REFRESH_ERRORS = [
    pytest.param(
        DomainInvalidCredentials(),
        401,
        "Unauthorized",
        "Invalid refresh token",
        id="invalid-refresh-token",
    ),
    pytest.param(
        DomainUnauthorized(),
        401,
        "Unauthorized",
        "Invalid refresh token",
        id="unauthorized",
    ),
    *AUTH_ERRORS,
]


def token_body(
    *,
    access_token: str = "access-token",
    refresh_token: str = "refresh-token",
    id_token: str = "id-token",
    expires_in: int = 3600,
) -> dict[str, Any]:
    return {
        "accessToken": access_token,
        "expiresIn": expires_in,
        "refreshToken": refresh_token,
        "idToken": id_token,
    }


def challenge_body(
    *,
    session: str = "challenge-session",
    challenge: str = "NEW_PASSWORD",
    parameters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "session": session,
        "challenge": challenge,
        "parameters": parameters or {},
    }


# ──── Fixtures ───────────────────────────────────────────────────────────────────────


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
def tokens() -> Tokens:
    return Tokens(
        access_token="access-token",
        expires_in=3600,
        refresh_token="refresh-token",
        id_token="id-token",
    )


@pytest.fixture
def refreshed_tokens() -> Tokens:
    return Tokens(
        access_token="new-access-token",
        expires_in=3600,
        refresh_token="refresh-token",
        id_token="new-id-token",
    )


@pytest.fixture
def password_challenge() -> Challenge:
    return Challenge(
        session="challenge-session",
        challenge=Challenge.Key.NEW_PASSWORD,
        parameters={},
    )


@pytest.fixture
def mfa_challenge() -> Challenge:
    return Challenge(
        session="next-session",
        challenge=Challenge.Key.NEW_MFA,
        parameters={"secret": "software-token-secret"},
    )


# ──── POST /auth/login ────────────────────────────────────────────────────────────────


class TestLogin:
    def test_returns_tokens(
        self,
        auth_provider: FakeAuthProvider,
        invoke_auth_api,
        tokens: Tokens,
    ) -> None:
        auth_provider.authenticate.result = tokens

        response = invoke_auth_api(
            "/auth/login",
            {
                "name": "alice",
                "password": "Secret@1!",
            },
        )

        assert_status(response, 200)
        assert_body(response, token_body())
        assert auth_provider.authenticate.calls == [
            {
                "name": "alice",
                "password": "Secret@1!",
            }
        ]

    def test_returns_challenge(
        self,
        auth_provider: FakeAuthProvider,
        invoke_auth_api,
        password_challenge: Challenge,
    ) -> None:
        auth_provider.authenticate.result = password_challenge

        response = invoke_auth_api(
            "/auth/login",
            {
                "name": "alice",
                "password": "Secret@1!",
            },
        )

        assert_status(response, 202)
        assert_body(response, challenge_body())
        assert auth_provider.authenticate.calls == [
            {
                "name": "alice",
                "password": "Secret@1!",
            }
        ]

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
                "password": "Bad-Secret@1!",
            },
        )

        assert_problem(
            response,
            status=expected_status,
            title=expected_title,
            detail=expected_detail,
        )

    @pytest.mark.parametrize(
        "payload",
        [
            pytest.param({}, id="missing-all-fields"),
            pytest.param({"name": "alice"}, id="missing-password"),
            pytest.param({"password": "secret"}, id="missing-name"),
            pytest.param({"name": "", "password": "secret"}, id="blank-name"),
            pytest.param({"name": "alice", "password": ""}, id="blank-password"),
        ],
    )
    def test_rejects_invalid_body(
        self,
        invoke_auth_api,
        payload: dict[str, Any],
    ) -> None:
        response = invoke_auth_api("/auth/login", payload)

        assert_status(response, 422)


# ──── POST /auth/challenge ────────────────────────────────────────────────────────────


class TestChallenge:
    def test_returns_tokens(
        self,
        auth_provider: FakeAuthProvider,
        invoke_auth_api,
        tokens: Tokens,
    ) -> None:
        auth_provider.respond_to_challenge.result = tokens

        response = invoke_auth_api(
            "/auth/challenge",
            {
                "session": "long-challenge-session",
                "challenge": "MFA",
                "response": {
                    "name": "alice",
                    "code": "123456",
                },
            },
        )

        assert_status(response, 200)
        assert_body(response, token_body())
        assert auth_provider.respond_to_challenge.calls == [
            {
                "session": "long-challenge-session",
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
        mfa_challenge: Challenge,
    ) -> None:
        auth_provider.respond_to_challenge.result = mfa_challenge

        response = invoke_auth_api(
            "/auth/challenge",
            {
                "session": "long-challenge-session",
                "challenge": "NEW_PASSWORD",
                "response": {
                    "name": "alice",
                    "password": "new-secret",
                },
            },
        )

        assert_status(response, 202)
        assert_body(
            response,
            challenge_body(
                session="next-session",
                challenge="NEW_MFA",
                parameters={"secret": "software-token-secret"},
            ),
        )
        assert auth_provider.respond_to_challenge.calls == [
            {
                "session": "long-challenge-session",
                "challenge": Challenge.Key.NEW_PASSWORD,
                "response": {
                    "name": "alice",
                    "password": "new-secret",
                },
            }
        ]

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
                "session": "long-challenge-session",
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

    @pytest.mark.parametrize(
        "payload",
        [
            pytest.param({}, id="missing-all-fields"),
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
                    "session": "challenge-session",
                    "response": {
                        "name": "alice",
                        "code": "123456",
                    },
                },
                id="missing-challenge",
            ),
            pytest.param(
                {
                    "session": "challenge-session",
                    "challenge": "MFA",
                },
                id="missing-response",
            ),
            pytest.param(
                {
                    "session": "challenge-session",
                    "challenge": "NOT_A_REAL_CHALLENGE",
                    "response": {
                        "name": "alice",
                        "code": "123456",
                    },
                },
                id="invalid-challenge-value",
            ),
        ],
    )
    def test_rejects_invalid_body(
        self,
        invoke_auth_api,
        payload: dict[str, Any],
    ) -> None:
        response = invoke_auth_api("/auth/challenge", payload)

        assert_status(response, 422)


# ──── POST /auth/refresh ──────────────────────────────────────────────────────────────


class TestRefresh:
    def test_returns_tokens(
        self,
        auth_provider: FakeAuthProvider,
        invoke_auth_api,
        refreshed_tokens: Tokens,
    ) -> None:
        auth_provider.refresh_tokens.result = refreshed_tokens

        response = invoke_auth_api(
            "/auth/refresh",
            {
                "refreshToken": "refresh-token",
            },
        )

        assert_status(response, 200)
        assert_body(
            response,
            token_body(
                access_token="new-access-token",
                refresh_token="refresh-token",
                id_token="new-id-token",
            ),
        )
        assert auth_provider.refresh_tokens.calls == [
            {
                "refresh_token": "refresh-token",
            }
        ]

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
                "refreshToken": "invalid-refresh-token",
            },
        )

        assert_problem(
            response,
            status=expected_status,
            title=expected_title,
            detail=expected_detail,
        )

    @pytest.mark.parametrize(
        "payload",
        [
            pytest.param({}, id="missing-refresh-token"),
            pytest.param({"refreshToken": ""}, id="blank-refresh-token"),
        ],
    )
    def test_rejects_invalid_body(
        self,
        invoke_auth_api,
        payload: dict[str, Any],
    ) -> None:
        response = invoke_auth_api("/auth/refresh", payload)

        assert_status(response, 422)


# ──── POST /auth/logout ───────────────────────────────────────────────────────────────


class TestLogout:
    def test_returns_no_content(
        self,
        auth_provider: FakeAuthProvider,
        invoke_auth_api,
    ) -> None:
        response = invoke_auth_api(
            "/auth/logout",
            {
                "accessToken": "access-token",
            },
        )

        assert_status(response, 204)
        assert_no_body(response)
        assert auth_provider.revoke_tokens.calls == [
            {
                "access_token": "access-token",
                "refresh_token": None,
            }
        ]

    def test_accepts_refresh_token(
        self,
        auth_provider: FakeAuthProvider,
        invoke_auth_api,
    ) -> None:
        response = invoke_auth_api(
            "/auth/logout",
            {
                "refreshToken": "refresh-token",
            },
        )

        assert_status(response, 204)
        assert_no_body(response)
        assert auth_provider.revoke_tokens.calls == [
            {
                "access_token": None,
                "refresh_token": "refresh-token",
            }
        ]

    def test_rejects_both_tokens(
        self,
        invoke_auth_api,
    ) -> None:
        response = invoke_auth_api(
            "/auth/logout",
            {
                "accessToken": "access-token",
                "refreshToken": "refresh-token",
            },
        )

        assert_status(response, 422)

    @pytest.mark.parametrize(
        "provider_error",
        [
            pytest.param(DomainInvalidCredentials(), id="invalid-credentials"),
            pytest.param(DomainUnauthorized(), id="unauthorized"),
        ],
    )
    def test_handles_unauthorized_token_idempotently(
        self,
        auth_provider: FakeAuthProvider,
        invoke_auth_api,
        provider_error: Exception,
    ) -> None:
        auth_provider.revoke_tokens.error = provider_error

        response = invoke_auth_api(
            "/auth/logout",
            {
                "accessToken": "access-token",
            },
        )

        assert_status(response, 204)
        assert_no_body(response)

    @pytest.mark.parametrize(
        ("provider_error", "expected_status", "expected_title"),
        [
            pytest.param(DomainForbidden(), 403, "Forbidden", id="forbidden"),
            pytest.param(
                DomainRateLimited(),
                429,
                "Too Many Requests",
                id="rate-limited",
            ),
        ],
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

    def test_maps_unexpected_domain_error(
        self,
        auth_provider: FakeAuthProvider,
        invoke_auth_api,
    ) -> None:
        auth_provider.revoke_tokens.error = DomainInvariantViolation("unexpected")

        response = invoke_auth_api(
            "/auth/logout",
            {
                "accessToken": "access-token",
            },
        )

        assert_problem(
            response,
            status=500,
            title="Internal Server Error",
        )

    @pytest.mark.parametrize(
        "payload",
        [
            pytest.param({}, id="missing-all-tokens"),
            pytest.param({"accessToken": "", "refreshToken": ""}, id="blank-tokens"),
        ],
    )
    def test_rejects_invalid_body(
        self,
        invoke_auth_api,
        payload: dict[str, Any],
    ) -> None:
        response = invoke_auth_api("/auth/logout", payload)

        assert_status(response, 422)


# ──── Routing ────────────────────────────────────────────────────────────────────────


class TestRouting:
    @pytest.mark.parametrize(
        "path",
        [
            pytest.param("/auth/login", id="login"),
            pytest.param("/auth/challenge", id="challenge"),
            pytest.param("/auth/refresh", id="refresh"),
            pytest.param("/auth/logout", id="logout"),
        ],
    )
    def test_rejects_unsupported_methods(
        self,
        auth_handler_module,
        apigw_event,
        lambda_context,
        path: str,
    ) -> None:
        response = auth_handler_module.lambda_handler(
            apigw_event(path, {}, method="GET"),
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
            apigw_event("/auth/unknown", {}),
            lambda_context,
        )

        assert_status(response, 404)
