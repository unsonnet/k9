from typing import Any

import auth.providers.auth as auth
import boto3
import pytest
from auth.providers.auth import Challenge, Tokens
from botocore.stub import Stubber
from shared.errors import (
    DomainExpiredToken,
    DomainForbidden,
    DomainInvalidCredentials,
    DomainInvalidTokens,
    DomainInvariantViolation,
    DomainNotFound,
    DomainRateLimited,
)
from shared.providers.cognito import encode_name

pytestmark = pytest.mark.unit


# ──── Helpers ─────────────────────────────────────────────────────────────────────────


def admin_initiate_auth_params(
    provider: auth.CognitoAuthProvider,
    *,
    name: str = "alice",
    password: str = "secret",
) -> dict[str, Any]:
    xname = encode_name(name)

    return {
        "ClientId": "client-id",
        "UserPoolId": "user-pool-id",
        "AuthFlow": "ADMIN_USER_PASSWORD_AUTH",
        "AuthParameters": {
            "SECRET_HASH": provider._secret_hash(xname),
            "USERNAME": xname,
            "PASSWORD": password,
        },
    }


def admin_respond_to_auth_challenge_params(
    provider: auth.CognitoAuthProvider,
    *,
    session: str = "challenge-session-token",
    name: str = "alice",
    challenge_name: str,
    challenge_responses: dict[str, str] | None = None,
) -> dict[str, Any]:
    xname = encode_name(name)

    return {
        "ClientId": "client-id",
        "UserPoolId": "user-pool-id",
        "Session": session,
        "ChallengeName": challenge_name,
        "ChallengeResponses": {
            "SECRET_HASH": provider._secret_hash(xname),
            "USERNAME": xname,
            **(challenge_responses or {}),
        },
    }


def token_response(
    *,
    access_token: str = "access-token",
    expires_in: int = 3600,
    refresh_token: str = "refresh-token",
    id_token: str = "id-token",
) -> dict[str, Any]:
    return {
        "AuthenticationResult": {
            "AccessToken": access_token,
            "ExpiresIn": expires_in,
            "RefreshToken": refresh_token,
            "IdToken": id_token,
        }
    }


def challenge_response(
    *,
    challenge_name: str,
    session: str = "challenge-session-token",
) -> dict[str, str]:
    return {
        "Session": session,
        "ChallengeName": challenge_name,
    }


def add_client_error(
    stubber: Stubber,
    *,
    method: str,
    service_error_code: str,
    expected_params: dict[str, Any],
    service_message: str = "provider error",
    http_status_code: int = 400,
) -> None:
    stubber.add_client_error(
        method,
        service_error_code=service_error_code,
        service_message=service_message,
        http_status_code=http_status_code,
        expected_params=expected_params,
    )


# ──── Fixtures ───────────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def aws_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Prevent boto3 from attempting to discover real AWS credentials.

    These tests use botocore Stubber, so no real AWS calls are made, but boto3
    still needs credentials available when constructing/signing requests.
    """
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setenv("AWS_SECURITY_TOKEN", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")


@pytest.fixture
def cognito_client():
    return boto3.client("cognito-idp", region_name="us-east-1")


@pytest.fixture
def provider(
    monkeypatch: pytest.MonkeyPatch,
    cognito_client,
) -> auth.CognitoAuthProvider:
    monkeypatch.setattr(
        auth.boto3,
        "client",
        lambda service_name, region_name=None: cognito_client,
    )

    return auth.CognitoAuthProvider(
        region="us-east-1",
        client_id="client-id",
        user_pool_id="user-pool-id",
        client_secret="client-secret-value-1234",
    )


@pytest.fixture
def stubber(cognito_client):
    with Stubber(cognito_client) as stubber:
        yield stubber


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
        session="challenge-session-token",
        challenge=Challenge.Key.NEW_PASSWORD,
        parameters={},
    )


@pytest.fixture
def mfa_challenge() -> Challenge:
    return Challenge(
        session="challenge-session-token",
        challenge=Challenge.Key.MFA,
        parameters={},
    )


@pytest.fixture
def new_mfa_challenge() -> Challenge:
    return Challenge(
        session="mfa-setup-session-token",
        challenge=Challenge.Key.NEW_MFA,
        parameters={"secret": "software-token-secret"},
    )


# ──── Tests ───────────────────────────────────────────────────────────────────────────


# ──── authenticate() ──────────────────────────────────────────────────────────────────


class TestAuthenticate:
    def test_uses_expected_payload_and_returns_tokens(
        self,
        provider: auth.CognitoAuthProvider,
        stubber: Stubber,
        tokens: Tokens,
    ) -> None:
        stubber.add_response(
            "admin_initiate_auth",
            token_response(),
            admin_initiate_auth_params(provider),
        )

        result = provider.authenticate(
            name="alice",
            password="secret",
        )

        assert result == tokens

    @pytest.mark.parametrize(
        ("challenge_name", "expected_challenge"),
        [
            pytest.param(
                "NEW_PASSWORD_REQUIRED",
                Challenge(
                    session="challenge-session-token",
                    challenge=Challenge.Key.NEW_PASSWORD,
                    parameters={},
                ),
                id="new-password",
            ),
            pytest.param(
                "SOFTWARE_TOKEN_MFA",
                Challenge(
                    session="challenge-session-token",
                    challenge=Challenge.Key.MFA,
                    parameters={},
                ),
                id="mfa",
            ),
        ],
    )
    def test_returns_password_challenge(
        self,
        provider: auth.CognitoAuthProvider,
        stubber: Stubber,
        challenge_name: str,
        expected_challenge: Challenge,
    ) -> None:
        stubber.add_response(
            "admin_initiate_auth",
            challenge_response(challenge_name=challenge_name),
            admin_initiate_auth_params(provider),
        )

        result = provider.authenticate(
            name="alice",
            password="secret",
        )

        assert result == expected_challenge

    def test_returns_new_mfa_challenge(
        self,
        provider: auth.CognitoAuthProvider,
        stubber: Stubber,
        new_mfa_challenge: Challenge,
    ) -> None:
        stubber.add_response(
            "admin_initiate_auth",
            challenge_response(
                session="challenge-session-token",
                challenge_name="MFA_SETUP",
            ),
            admin_initiate_auth_params(provider),
        )
        stubber.add_response(
            "associate_software_token",
            {
                "Session": "mfa-setup-session-token",
                "SecretCode": "software-token-secret",
            },
            {
                "Session": "challenge-session-token",
            },
        )

        result = provider.authenticate(
            name="alice",
            password="secret",
        )

        assert result == new_mfa_challenge

    @pytest.mark.parametrize(
        ("service_error_code", "expected_error"),
        [
            pytest.param(
                "PasswordResetRequiredException",
                DomainExpiredToken,
                id="password-reset-required",
            ),
            pytest.param(
                "ForbiddenException",
                DomainForbidden,
                id="forbidden",
            ),
            pytest.param(
                "UnauthorizedException",
                DomainForbidden,
                id="unauthorized",
            ),
            pytest.param(
                "NotAuthorizedException",
                DomainInvalidCredentials,
                id="not-authorized",
            ),
            pytest.param(
                "InvalidPasswordException",
                DomainInvalidCredentials,
                id="invalid-password",
            ),
            pytest.param(
                "TooManyRequestsException",
                DomainRateLimited,
                id="too-many-requests",
            ),
            pytest.param(
                "LimitExceededException",
                DomainRateLimited,
                id="limit-exceeded",
            ),
            pytest.param(
                "UserNotFoundException",
                DomainNotFound,
                id="user-not-found",
            ),
        ],
    )
    def test_maps_provider_errors(
        self,
        provider: auth.CognitoAuthProvider,
        stubber: Stubber,
        service_error_code: str,
        expected_error: type[Exception],
    ) -> None:
        add_client_error(
            stubber,
            method="admin_initiate_auth",
            service_error_code=service_error_code,
            expected_params=admin_initiate_auth_params(provider),
        )

        with pytest.raises(expected_error):
            provider.authenticate(
                name="alice",
                password="secret",
            )


# ──── respond_to_challenge() ──────────────────────────────────────────────────────────


class TestRespondToChallenge:
    def test_new_password_uses_expected_payload_and_returns_tokens(
        self,
        provider: auth.CognitoAuthProvider,
        stubber: Stubber,
        tokens: Tokens,
    ) -> None:
        stubber.add_response(
            "admin_respond_to_auth_challenge",
            token_response(),
            admin_respond_to_auth_challenge_params(
                provider,
                challenge_name="NEW_PASSWORD_REQUIRED",
                challenge_responses={"NEW_PASSWORD": "new-secret"},
            ),
        )

        result = provider.respond_to_challenge(
            session="challenge-session-token",
            challenge=Challenge.Key.NEW_PASSWORD,
            response={
                "name": "alice",
                "password": "new-secret",
            },
        )

        assert result == tokens

    def test_new_password_returns_followup_challenge(
        self,
        provider: auth.CognitoAuthProvider,
        stubber: Stubber,
        mfa_challenge: Challenge,
    ) -> None:
        stubber.add_response(
            "admin_respond_to_auth_challenge",
            challenge_response(
                session="challenge-session-token",
                challenge_name="SOFTWARE_TOKEN_MFA",
            ),
            admin_respond_to_auth_challenge_params(
                provider,
                challenge_name="NEW_PASSWORD_REQUIRED",
                challenge_responses={"NEW_PASSWORD": "new-secret"},
            ),
        )

        result = provider.respond_to_challenge(
            session="challenge-session-token",
            challenge=Challenge.Key.NEW_PASSWORD,
            response={
                "name": "alice",
                "password": "new-secret",
            },
        )

        assert result == mfa_challenge

    def test_new_mfa_verifies_token_then_uses_expected_payload_and_returns_tokens(
        self,
        provider: auth.CognitoAuthProvider,
        stubber: Stubber,
        tokens: Tokens,
    ) -> None:
        stubber.add_response(
            "verify_software_token",
            {
                "Session": "verified-session-token",
            },
            {
                "Session": "challenge-session-token",
                "UserCode": "123456",
            },
        )
        stubber.add_response(
            "admin_respond_to_auth_challenge",
            token_response(),
            admin_respond_to_auth_challenge_params(
                provider,
                session="verified-session-token",
                challenge_name="MFA_SETUP",
            ),
        )

        result = provider.respond_to_challenge(
            session="challenge-session-token",
            challenge=Challenge.Key.NEW_MFA,
            response={
                "name": "alice",
                "code": "123456",
            },
        )

        assert result == tokens

    def test_mfa_uses_expected_payload_and_returns_tokens(
        self,
        provider: auth.CognitoAuthProvider,
        stubber: Stubber,
        tokens: Tokens,
    ) -> None:
        stubber.add_response(
            "admin_respond_to_auth_challenge",
            token_response(),
            admin_respond_to_auth_challenge_params(
                provider,
                challenge_name="SOFTWARE_TOKEN_MFA",
                challenge_responses={"SOFTWARE_TOKEN_MFA_CODE": "123456"},
            ),
        )

        result = provider.respond_to_challenge(
            session="challenge-session-token",
            challenge=Challenge.Key.MFA,
            response={
                "name": "alice",
                "code": "123456",
            },
        )

        assert result == tokens

    @pytest.mark.parametrize(
        ("service_error_code", "expected_error"),
        [
            pytest.param(
                "CodeMismatchException",
                DomainInvalidCredentials,
                id="code-mismatch",
            ),
            pytest.param(
                "ForbiddenException",
                DomainForbidden,
                id="forbidden",
            ),
            pytest.param(
                "TooManyRequestsException",
                DomainRateLimited,
                id="too-many-requests",
            ),
            pytest.param(
                "LimitExceededException",
                DomainRateLimited,
                id="limit-exceeded",
            ),
        ],
    )
    def test_new_password_maps_provider_errors(
        self,
        provider: auth.CognitoAuthProvider,
        stubber: Stubber,
        service_error_code: str,
        expected_error: type[Exception],
    ) -> None:
        add_client_error(
            stubber,
            method="admin_respond_to_auth_challenge",
            service_error_code=service_error_code,
            expected_params=admin_respond_to_auth_challenge_params(
                provider,
                challenge_name="NEW_PASSWORD_REQUIRED",
                challenge_responses={"NEW_PASSWORD": "new-secret"},
            ),
        )

        with pytest.raises(expected_error):
            provider.respond_to_challenge(
                session="challenge-session-token",
                challenge=Challenge.Key.NEW_PASSWORD,
                response={
                    "name": "alice",
                    "password": "new-secret",
                },
            )

    @pytest.mark.parametrize(
        ("service_error_code", "expected_error"),
        [
            pytest.param(
                "CodeMismatchException",
                DomainInvalidCredentials,
                id="code-mismatch",
            ),
            pytest.param(
                "ForbiddenException",
                DomainForbidden,
                id="forbidden",
            ),
            pytest.param(
                "TooManyRequestsException",
                DomainRateLimited,
                id="too-many-requests",
            ),
            pytest.param(
                "LimitExceededException",
                DomainRateLimited,
                id="limit-exceeded",
            ),
        ],
    )
    def test_new_mfa_maps_verify_token_provider_errors(
        self,
        provider: auth.CognitoAuthProvider,
        stubber: Stubber,
        service_error_code: str,
        expected_error: type[Exception],
    ) -> None:
        add_client_error(
            stubber,
            method="verify_software_token",
            service_error_code=service_error_code,
            expected_params={
                "Session": "challenge-session-token",
                "UserCode": "123456",
            },
        )

        with pytest.raises(expected_error):
            provider.respond_to_challenge(
                session="challenge-session-token",
                challenge=Challenge.Key.NEW_MFA,
                response={
                    "name": "alice",
                    "code": "123456",
                },
            )

    @pytest.mark.parametrize(
        ("service_error_code", "expected_error"),
        [
            pytest.param(
                "CodeMismatchException",
                DomainInvalidCredentials,
                id="code-mismatch",
            ),
            pytest.param(
                "ForbiddenException",
                DomainForbidden,
                id="forbidden",
            ),
            pytest.param(
                "TooManyRequestsException",
                DomainRateLimited,
                id="too-many-requests",
            ),
            pytest.param(
                "LimitExceededException",
                DomainRateLimited,
                id="limit-exceeded",
            ),
        ],
    )
    def test_new_mfa_maps_challenge_provider_errors(
        self,
        provider: auth.CognitoAuthProvider,
        stubber: Stubber,
        service_error_code: str,
        expected_error: type[Exception],
    ) -> None:
        stubber.add_response(
            "verify_software_token",
            {
                "Session": "verified-session-token",
            },
            {
                "Session": "challenge-session-token",
                "UserCode": "123456",
            },
        )
        add_client_error(
            stubber,
            method="admin_respond_to_auth_challenge",
            service_error_code=service_error_code,
            expected_params=admin_respond_to_auth_challenge_params(
                provider,
                session="verified-session-token",
                challenge_name="MFA_SETUP",
            ),
        )

        with pytest.raises(expected_error):
            provider.respond_to_challenge(
                session="challenge-session-token",
                challenge=Challenge.Key.NEW_MFA,
                response={
                    "name": "alice",
                    "code": "123456",
                },
            )

    @pytest.mark.parametrize(
        ("service_error_code", "expected_error"),
        [
            pytest.param(
                "CodeMismatchException",
                DomainInvalidCredentials,
                id="code-mismatch",
            ),
            pytest.param(
                "ForbiddenException",
                DomainForbidden,
                id="forbidden",
            ),
            pytest.param(
                "TooManyRequestsException",
                DomainRateLimited,
                id="too-many-requests",
            ),
            pytest.param(
                "LimitExceededException",
                DomainRateLimited,
                id="limit-exceeded",
            ),
        ],
    )
    def test_mfa_maps_provider_errors(
        self,
        provider: auth.CognitoAuthProvider,
        stubber: Stubber,
        service_error_code: str,
        expected_error: type[Exception],
    ) -> None:
        add_client_error(
            stubber,
            method="admin_respond_to_auth_challenge",
            service_error_code=service_error_code,
            expected_params=admin_respond_to_auth_challenge_params(
                provider,
                challenge_name="SOFTWARE_TOKEN_MFA",
                challenge_responses={"SOFTWARE_TOKEN_MFA_CODE": "123456"},
            ),
        )

        with pytest.raises(expected_error):
            provider.respond_to_challenge(
                session="challenge-session-token",
                challenge=Challenge.Key.MFA,
                response={
                    "name": "alice",
                    "code": "123456",
                },
            )


# ──── refresh_tokens() ────────────────────────────────────────────────────────────────


class TestRefreshTokens:
    def test_uses_expected_payload_and_returns_tokens(
        self,
        provider: auth.CognitoAuthProvider,
        stubber: Stubber,
        refreshed_tokens: Tokens,
    ) -> None:
        stubber.add_response(
            "get_tokens_from_refresh_token",
            token_response(
                access_token="new-access-token",
                refresh_token="refresh-token",
                id_token="new-id-token",
            ),
            {
                "ClientId": "client-id",
                "ClientSecret": "client-secret-value-1234",
                "RefreshToken": "refresh-token",
            },
        )

        result = provider.refresh_tokens(refresh_token="refresh-token")

        assert result == refreshed_tokens

    @pytest.mark.parametrize(
        ("service_error_code", "expected_error"),
        [
            pytest.param(
                "ExpiredCodeException",
                DomainExpiredToken,
                id="expired-code",
            ),
            pytest.param(
                "ForbiddenException",
                DomainForbidden,
                id="forbidden",
            ),
            pytest.param(
                "NotAuthorizedException",
                DomainInvalidCredentials,
                id="not-authorized",
            ),
            pytest.param(
                "RefreshTokenReuseException",
                DomainInvalidTokens,
                id="refresh-token-reuse",
            ),
            pytest.param(
                "UnsupportedTokenTypeException",
                DomainInvalidTokens,
                id="unsupported-token-type",
            ),
            pytest.param(
                "TooManyRequestsException",
                DomainRateLimited,
                id="too-many-requests",
            ),
            pytest.param(
                "LimitExceededException",
                DomainRateLimited,
                id="limit-exceeded",
            ),
        ],
    )
    def test_maps_provider_errors(
        self,
        provider: auth.CognitoAuthProvider,
        stubber: Stubber,
        service_error_code: str,
        expected_error: type[Exception],
    ) -> None:
        add_client_error(
            stubber,
            method="get_tokens_from_refresh_token",
            service_error_code=service_error_code,
            expected_params={
                "ClientId": "client-id",
                "ClientSecret": "client-secret-value-1234",
                "RefreshToken": "refresh-token",
            },
        )

        with pytest.raises(expected_error):
            provider.refresh_tokens(refresh_token="refresh-token")


# ──── revoke_tokens() ────────────────────────────────────────────────────────────────


class TestRevokeTokens:
    def test_uses_expected_payload_with_access_token(
        self,
        provider: auth.CognitoAuthProvider,
        stubber: Stubber,
    ) -> None:
        stubber.add_response(
            "global_sign_out",
            {},
            {
                "AccessToken": "access-token",
            },
        )

        response = provider.revoke_tokens(access_token="access-token")

        assert response is None

    def test_uses_expected_payload_with_refresh_token(
        self,
        provider: auth.CognitoAuthProvider,
        stubber: Stubber,
    ) -> None:
        stubber.add_response(
            "revoke_token",
            {},
            {
                "ClientId": "client-id",
                "ClientSecret": "client-secret-value-1234",
                "Token": "refresh-token",
            },
        )

        response = provider.revoke_tokens(refresh_token="refresh-token")

        assert response is None

    @pytest.mark.parametrize(
        ("access_token", "refresh_token"),
        [
            pytest.param(None, None, id="missing-token"),
            pytest.param(
                "access-token",
                "refresh-token",
                id="multiple-tokens",
            ),
        ],
    )
    def test_rejects_missing_or_multiple_tokens(
        self,
        provider: auth.CognitoAuthProvider,
        access_token: str | None,
        refresh_token: str | None,
    ) -> None:
        with pytest.raises(DomainInvariantViolation):
            provider.revoke_tokens(
                access_token=access_token,
                refresh_token=refresh_token,
            )

    @pytest.mark.parametrize(
        ("service_error_code", "expected_error"),
        [
            pytest.param(
                "NotAuthorizedException",
                DomainInvalidCredentials,
                id="not-authorized",
            ),
            pytest.param(
                "ForbiddenException",
                DomainForbidden,
                id="forbidden",
            ),
            pytest.param(
                "TooManyRequestsException",
                DomainRateLimited,
                id="too-many-requests",
            ),
            pytest.param(
                "LimitExceededException",
                DomainRateLimited,
                id="limit-exceeded",
            ),
        ],
    )
    def test_access_token_maps_provider_errors(
        self,
        provider: auth.CognitoAuthProvider,
        stubber: Stubber,
        service_error_code: str,
        expected_error: type[Exception],
    ) -> None:
        add_client_error(
            stubber,
            method="global_sign_out",
            service_error_code=service_error_code,
            expected_params={
                "AccessToken": "access-token",
            },
        )

        with pytest.raises(expected_error):
            provider.revoke_tokens(access_token="access-token")

    @pytest.mark.parametrize(
        ("service_error_code", "expected_error"),
        [
            pytest.param(
                "NotAuthorizedException",
                DomainInvalidCredentials,
                id="not-authorized",
            ),
            pytest.param(
                "RefreshTokenReuseException",
                DomainInvalidTokens,
                id="refresh-token-reuse",
            ),
            pytest.param(
                "UnsupportedTokenTypeException",
                DomainInvalidTokens,
                id="unsupported-token-type",
            ),
            pytest.param(
                "ForbiddenException",
                DomainForbidden,
                id="forbidden",
            ),
            pytest.param(
                "TooManyRequestsException",
                DomainRateLimited,
                id="too-many-requests",
            ),
            pytest.param(
                "LimitExceededException",
                DomainRateLimited,
                id="limit-exceeded",
            ),
        ],
    )
    def test_refresh_token_maps_provider_errors(
        self,
        provider: auth.CognitoAuthProvider,
        stubber: Stubber,
        service_error_code: str,
        expected_error: type[Exception],
    ) -> None:
        add_client_error(
            stubber,
            method="revoke_token",
            service_error_code=service_error_code,
            expected_params={
                "ClientId": "client-id",
                "ClientSecret": "client-secret-value-1234",
                "Token": "refresh-token",
            },
        )

        with pytest.raises(expected_error):
            provider.revoke_tokens(refresh_token="refresh-token")


# ──── Provider Responses ──────────────────────────────────────────────────────────────


class TestResponseParsing:
    @pytest.mark.parametrize(
        "response",
        [
            pytest.param({}, id="empty-response"),
            pytest.param({"AuthenticationResult": {}}, id="empty-auth-result"),
            pytest.param(
                {
                    "AuthenticationResult": {
                        "AccessToken": "access-token",
                    },
                },
                id="partial-auth-result",
            ),
            pytest.param(
                {
                    "Session": "challenge-session-token",
                },
                id="missing-challenge-name",
            ),
            pytest.param(
                {
                    "ChallengeName": "SOFTWARE_TOKEN_MFA",
                },
                id="missing-session",
            ),
        ],
    )
    def test_rejects_unexpected_result_response(
        self,
        provider: auth.CognitoAuthProvider,
        stubber: Stubber,
        response: dict[str, Any],
    ) -> None:
        stubber.add_response(
            "admin_initiate_auth",
            response,
            admin_initiate_auth_params(provider),
        )

        with pytest.raises(DomainInvariantViolation):
            provider.authenticate(
                name="alice",
                password="secret",
            )

    @pytest.mark.parametrize(
        "challenge_name",
        [
            pytest.param("CUSTOM_CHALLENGE", id="custom-challenge"),
            pytest.param("SMS_MFA", id="sms-mfa"),
            pytest.param("UNKNOWN_CHALLENGE", id="unknown-challenge"),
        ],
    )
    def test_rejects_unsupported_challenge(
        self,
        provider: auth.CognitoAuthProvider,
        stubber: Stubber,
        challenge_name: str,
    ) -> None:
        stubber.add_response(
            "admin_initiate_auth",
            challenge_response(
                session="challenge-session-token",
                challenge_name=challenge_name,
            ),
            admin_initiate_auth_params(provider),
        )

        with pytest.raises(DomainInvariantViolation):
            provider.authenticate(
                name="alice",
                password="secret",
            )
