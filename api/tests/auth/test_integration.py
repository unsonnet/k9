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

pytestmark = pytest.mark.integration


# ──── Helpers ─────────────────────────────────────────────────────────────────────────


class FakeAuthProvider:
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


def assert_problem_response(
    response: dict[str, Any],
    response_body: Callable[[dict[str, Any]], dict[str, Any]],
    *,
    status: int,
    title: str,
    detail: str | None = None,
) -> None:
    assert response["statusCode"] == status

    body = response_body(response)
    assert body["title"] == title

    if detail is not None:
        assert body["detail"] == detail


# ──── Fixtures ───────────────────────────────────────────────────────────────────────


@pytest.fixture
def auth_provider() -> FakeAuthProvider:
    return FakeAuthProvider()


@pytest.fixture
def auth_handler_module(
    monkeypatch: pytest.MonkeyPatch,
    auth_provider: FakeAuthProvider,
):
    import auth.providers.auth as auth

    monkeypatch.setattr(auth, "CognitoAuthProvider", lambda: auth_provider)

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


# ──── Tests ───────────────────────────────────────────────────────────────────────────


# ──── POST /auth/login ────────────────────────────────────────────────────────────────


class TestLogin:
    def test_returns_tokens(
        self,
        auth_provider: FakeAuthProvider,
        invoke_auth_api,
        tokens: Tokens,
        response_body,
    ) -> None:
        auth_provider.authenticate_result = tokens

        response = invoke_auth_api(
            "/auth/login",
            {
                "username": "alice",
                "password": "secret",
            },
        )

        assert response["statusCode"] == 200
        assert response_body(response) == {
            "accessToken": "access-token",
            "expiresIn": 3600,
            "refreshToken": "refresh-token",
            "idToken": "id-token",
        }

    def test_returns_challenge(
        self,
        auth_provider: FakeAuthProvider,
        invoke_auth_api,
        password_challenge: Challenge,
        response_body,
    ) -> None:
        auth_provider.authenticate_result = password_challenge

        response = invoke_auth_api(
            "/auth/login",
            {
                "username": "alice",
                "password": "secret",
            },
        )

        assert response["statusCode"] == 202
        assert response_body(response) == {
            "session": "challenge-session",
            "challenge": "NEW_PASSWORD",
            "parameters": {},
        }

    @pytest.mark.parametrize(
        ("provider_error", "expected_status", "expected_title", "expected_detail"),
        [
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
            pytest.param(DomainForbidden(), 403, "Forbidden", None, id="forbidden"),
            pytest.param(
                DomainRateLimited(),
                429,
                "Too Many Requests",
                None,
                id="rate-limited",
            ),
        ],
    )
    def test_maps_domain_errors(
        self,
        auth_provider: FakeAuthProvider,
        invoke_auth_api,
        provider_error: Exception,
        expected_status: int,
        expected_title: str,
        expected_detail: str | None,
        response_body,
    ) -> None:
        auth_provider.authenticate_error = provider_error

        response = invoke_auth_api(
            "/auth/login",
            {
                "username": "alice",
                "password": "bad-secret",
            },
        )

        assert_problem_response(
            response,
            response_body,
            status=expected_status,
            title=expected_title,
            detail=expected_detail,
        )

    @pytest.mark.parametrize(
        "payload",
        [
            pytest.param({}, id="missing-all-fields"),
            pytest.param({"username": "alice"}, id="missing-password"),
            pytest.param({"password": "secret"}, id="missing-username"),
            pytest.param({"username": "", "password": "secret"}, id="blank-username"),
            pytest.param({"username": "alice", "password": ""}, id="blank-password"),
        ],
    )
    def test_rejects_invalid_body(
        self,
        invoke_auth_api,
        payload: dict[str, Any],
    ) -> None:
        response = invoke_auth_api("/auth/login", payload)

        assert response["statusCode"] == 422


# ──── POST /auth/challenge ────────────────────────────────────────────────────────────


class TestChallenge:
    def test_returns_tokens(
        self,
        auth_provider: FakeAuthProvider,
        invoke_auth_api,
        tokens: Tokens,
        response_body,
    ) -> None:
        auth_provider.challenge_result = tokens

        response = invoke_auth_api(
            "/auth/challenge",
            {
                "session": "challenge-session",
                "challenge": "MFA",
                "response": {
                    "username": "alice",
                    "code": "123456",
                },
            },
        )

        assert response["statusCode"] == 200
        assert response_body(response) == {
            "accessToken": "access-token",
            "expiresIn": 3600,
            "refreshToken": "refresh-token",
            "idToken": "id-token",
        }

    def test_returns_followup_challenge(
        self,
        auth_provider: FakeAuthProvider,
        invoke_auth_api,
        mfa_challenge: Challenge,
        response_body,
    ) -> None:
        auth_provider.challenge_result = mfa_challenge

        response = invoke_auth_api(
            "/auth/challenge",
            {
                "session": "challenge-session",
                "challenge": "NEW_PASSWORD",
                "response": {
                    "username": "alice",
                    "password": "new-secret",
                },
            },
        )

        assert response["statusCode"] == 202
        assert response_body(response) == {
            "session": "next-session",
            "challenge": "NEW_MFA",
            "parameters": {"secret": "software-token-secret"},
        }

    @pytest.mark.parametrize(
        ("provider_error", "expected_status", "expected_title", "expected_detail"),
        [
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
            pytest.param(DomainForbidden(), 403, "Forbidden", None, id="forbidden"),
            pytest.param(
                DomainRateLimited(),
                429,
                "Too Many Requests",
                None,
                id="rate-limited",
            ),
        ],
    )
    def test_maps_domain_errors(
        self,
        auth_provider: FakeAuthProvider,
        invoke_auth_api,
        provider_error: Exception,
        expected_status: int,
        expected_title: str,
        expected_detail: str | None,
        response_body,
    ) -> None:
        auth_provider.challenge_error = provider_error

        response = invoke_auth_api(
            "/auth/challenge",
            {
                "session": "challenge-session",
                "challenge": "MFA",
                "response": {
                    "username": "alice",
                    "code": "123456",
                },
            },
        )

        assert_problem_response(
            response,
            response_body,
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
                        "username": "alice",
                        "code": "123456",
                    },
                },
                id="missing-session",
            ),
            pytest.param(
                {
                    "session": "challenge-session",
                    "response": {
                        "username": "alice",
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
                        "username": "alice",
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

        assert response["statusCode"] == 422


# ──── POST /auth/refresh ──────────────────────────────────────────────────────────────


class TestRefresh:
    def test_returns_tokens(
        self,
        auth_provider: FakeAuthProvider,
        invoke_auth_api,
        refreshed_tokens: Tokens,
        response_body,
    ) -> None:
        auth_provider.refresh_result = refreshed_tokens

        response = invoke_auth_api(
            "/auth/refresh",
            {
                "refreshToken": "refresh-token",
            },
        )

        assert response["statusCode"] == 200
        assert response_body(response) == {
            "accessToken": "new-access-token",
            "expiresIn": 3600,
            "refreshToken": "refresh-token",
            "idToken": "new-id-token",
        }

    @pytest.mark.parametrize(
        ("provider_error", "expected_status", "expected_title", "expected_detail"),
        [
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
            pytest.param(DomainForbidden(), 403, "Forbidden", None, id="forbidden"),
            pytest.param(
                DomainRateLimited(),
                429,
                "Too Many Requests",
                None,
                id="rate-limited",
            ),
        ],
    )
    def test_maps_domain_errors(
        self,
        auth_provider: FakeAuthProvider,
        invoke_auth_api,
        provider_error: Exception,
        expected_status: int,
        expected_title: str,
        expected_detail: str | None,
        response_body,
    ) -> None:
        auth_provider.refresh_error = provider_error

        response = invoke_auth_api(
            "/auth/refresh",
            {
                "refreshToken": "invalid-refresh-token",
            },
        )

        assert_problem_response(
            response,
            response_body,
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

        assert response["statusCode"] == 422


# ──── POST /auth/logout ───────────────────────────────────────────────────────────────


class TestLogout:
    def test_returns_no_content(
        self,
        invoke_auth_api,
    ) -> None:
        response = invoke_auth_api(
            "/auth/logout",
            {
                "accessToken": "access-token",
            },
        )

        assert response["statusCode"] == 204
        assert response.get("body") in (None, "")

    @pytest.mark.parametrize(
        "provider_error",
        [
            pytest.param(DomainInvalidCredentials(), id="invalid-credentials"),
            pytest.param(DomainUnauthorized(), id="unauthorized"),
        ],
    )
    def test_is_idempotent_for_unauthorized_token(
        self,
        auth_provider: FakeAuthProvider,
        invoke_auth_api,
        provider_error: Exception,
    ) -> None:
        auth_provider.revoke_error = provider_error

        response = invoke_auth_api(
            "/auth/logout",
            {
                "accessToken": "access-token",
            },
        )

        assert response["statusCode"] == 204
        assert response.get("body") in (None, "")

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
    def test_maps_domain_errors(
        self,
        auth_provider: FakeAuthProvider,
        invoke_auth_api,
        provider_error: Exception,
        expected_status: int,
        expected_title: str,
        response_body,
    ) -> None:
        auth_provider.revoke_error = provider_error

        response = invoke_auth_api(
            "/auth/logout",
            {
                "accessToken": "access-token",
            },
        )

        assert_problem_response(
            response,
            response_body,
            status=expected_status,
            title=expected_title,
        )

    def test_unexpected_domain_error_returns_internal_server_error(
        self,
        auth_provider: FakeAuthProvider,
        invoke_auth_api,
        response_body,
    ) -> None:
        auth_provider.revoke_error = DomainInvariantViolation("unexpected")

        response = invoke_auth_api(
            "/auth/logout",
            {
                "accessToken": "access-token",
            },
        )

        assert_problem_response(
            response,
            response_body,
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

        assert response["statusCode"] == 422


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

        assert response["statusCode"] == 405

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

        assert response["statusCode"] == 404
