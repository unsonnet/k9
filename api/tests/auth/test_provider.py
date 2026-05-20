from typing import Any

import auth.provider as provider_module
import boto3
import pytest
from auth.provider import MFA, Challenge, Tokens
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

REGION = "us-east-1"
CLIENT_ID = "client-id"
USER_POOL_ID = "pool-id"
CLIENT_SECRET = "client-secret-1234567890AB"

SESSION = "session-token-1234567890"
NEXT_SESSION = "next-session-token-1234567890"

PROVIDER_ERROR_CASES = [
    pytest.param("ExpiredCodeException", DomainExpiredToken, id="expired-code"),
    pytest.param(
        "PasswordResetRequiredException",
        DomainExpiredToken,
        id="password-reset-required",
    ),
    pytest.param("ForbiddenException", DomainForbidden, id="forbidden"),
    pytest.param("UnauthorizedException", DomainForbidden, id="unauthorized"),
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
        "CodeMismatchException",
        DomainInvalidCredentials,
        id="code-mismatch",
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
    pytest.param("TooManyRequestsException", DomainRateLimited, id="too-many-requests"),
    pytest.param("LimitExceededException", DomainRateLimited, id="limit-exceeded"),
    pytest.param("UserNotFoundException", DomainNotFound, id="user-not-found"),
]


def add_provider_error(
    stubber: Stubber,
    *,
    method: str,
    code: str,
    expected_params: dict[str, Any],
) -> None:
    stubber.add_client_error(
        method,
        service_error_code=code,
        service_message="provider error",
        http_status_code=400,
        expected_params=expected_params,
    )


def tokens_response(
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


def expected_tokens(
    *,
    access_token: str = "access-token",
    expires_in: int = 3600,
    refresh_token: str = "refresh-token",
    id_token: str = "id-token",
) -> Tokens:
    return Tokens(
        access_token=access_token,
        expires_in=expires_in,
        refresh_token=refresh_token,
        id_token=id_token,
    )


def expected_mfa(
    *,
    secret: str = "ABCDEFGHIJKLMNOP",
    name: str = "Alice",
) -> MFA:
    return MFA(
        secret=secret,
        url=(
            "otpauth://totp/Amazon%20Web%20Services:"
            f"K9%20-%20{name}?secret={secret}&issuer=Amazon%20Web%20Services"
        ),
    )


# ──── Fixtures ────────────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def aws_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setenv("AWS_SECURITY_TOKEN", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", REGION)


@pytest.fixture
def cognito_client():
    return boto3.client("cognito-idp", region_name=REGION)


@pytest.fixture
def provider(
    monkeypatch: pytest.MonkeyPatch,
    cognito_client,
) -> provider_module.CognitoAuthProvider:
    monkeypatch.setattr(
        provider_module.boto3,
        "client",
        lambda service_name, region_name=None: cognito_client,
    )

    return provider_module.CognitoAuthProvider(
        region=REGION,
        client_id=CLIENT_ID,
        user_pool_id=USER_POOL_ID,
        client_secret=CLIENT_SECRET,
    )


@pytest.fixture
def stubber(cognito_client):
    with Stubber(cognito_client) as stubber:
        yield stubber


# ──── authenticate() ──────────────────────────────────────────────────────────────────


class TestAuthenticate:
    def test_returns_tokens(
        self,
        provider: provider_module.CognitoAuthProvider,
        stubber: Stubber,
    ) -> None:
        xname = encode_name("alice")
        stubber.add_response(
            "admin_initiate_auth",
            tokens_response(),
            {
                "ClientId": CLIENT_ID,
                "UserPoolId": USER_POOL_ID,
                "AuthFlow": "ADMIN_USER_PASSWORD_AUTH",
                "AuthParameters": {
                    "SECRET_HASH": provider._secret_hash(xname),
                    "USERNAME": xname,
                    "PASSWORD": "Passw0rd!",
                },
            },
        )

        result = provider.authenticate(name="alice", password="Passw0rd!")

        assert result == expected_tokens()

    def test_returns_new_password_challenge(
        self,
        provider: provider_module.CognitoAuthProvider,
        stubber: Stubber,
    ) -> None:
        xname = encode_name("alice")
        stubber.add_response(
            "admin_initiate_auth",
            {
                "Session": SESSION,
                "ChallengeName": "NEW_PASSWORD_REQUIRED",
            },
            {
                "ClientId": CLIENT_ID,
                "UserPoolId": USER_POOL_ID,
                "AuthFlow": "ADMIN_USER_PASSWORD_AUTH",
                "AuthParameters": {
                    "SECRET_HASH": provider._secret_hash(xname),
                    "USERNAME": xname,
                    "PASSWORD": "Passw0rd!",
                },
            },
        )

        result = provider.authenticate(name="alice", password="Passw0rd!")

        assert result == Challenge(
            session=SESSION,
            challenge=Challenge.Key.NEW_PASSWORD,
            parameters={},
        )

    def test_returns_new_mfa_challenge(
        self,
        provider: provider_module.CognitoAuthProvider,
        stubber: Stubber,
    ) -> None:
        xname = encode_name("alice")
        stubber.add_response(
            "admin_initiate_auth",
            {
                "Session": SESSION,
                "ChallengeName": "MFA_SETUP",
            },
            {
                "ClientId": CLIENT_ID,
                "UserPoolId": USER_POOL_ID,
                "AuthFlow": "ADMIN_USER_PASSWORD_AUTH",
                "AuthParameters": {
                    "SECRET_HASH": provider._secret_hash(xname),
                    "USERNAME": xname,
                    "PASSWORD": "Passw0rd!",
                },
            },
        )
        stubber.add_response(
            "associate_software_token",
            {
                "Session": NEXT_SESSION,
                "SecretCode": "ABCDEFGHIJKLMNOP",
            },
            {
                "Session": SESSION,
            },
        )

        result = provider.authenticate(name="alice", password="Passw0rd!")

        assert result == Challenge(
            session=NEXT_SESSION,
            challenge=Challenge.Key.NEW_MFA,
            parameters={"secret": "ABCDEFGHIJKLMNOP"},
        )

    @pytest.mark.parametrize(
        ("code", "expected_error"),
        PROVIDER_ERROR_CASES,
    )
    def test_maps_provider_errors(
        self,
        provider: provider_module.CognitoAuthProvider,
        stubber: Stubber,
        code: str,
        expected_error: type[Exception],
    ) -> None:
        xname = encode_name("alice")
        add_provider_error(
            stubber,
            method="admin_initiate_auth",
            code=code,
            expected_params={
                "ClientId": CLIENT_ID,
                "UserPoolId": USER_POOL_ID,
                "AuthFlow": "ADMIN_USER_PASSWORD_AUTH",
                "AuthParameters": {
                    "SECRET_HASH": provider._secret_hash(xname),
                    "USERNAME": xname,
                    "PASSWORD": "Passw0rd!",
                },
            },
        )

        with pytest.raises(expected_error):
            provider.authenticate(name="alice", password="Passw0rd!")


# ──── respond_to_challenge() ──────────────────────────────────────────────────────────


class TestRespondToChallenge:
    def test_returns_tokens_for_new_password_challenge(
        self,
        provider: provider_module.CognitoAuthProvider,
        stubber: Stubber,
    ) -> None:
        xname = encode_name("alice")
        stubber.add_response(
            "admin_respond_to_auth_challenge",
            tokens_response(),
            {
                "ClientId": CLIENT_ID,
                "UserPoolId": USER_POOL_ID,
                "Session": SESSION,
                "ChallengeName": "NEW_PASSWORD_REQUIRED",
                "ChallengeResponses": {
                    "SECRET_HASH": provider._secret_hash(xname),
                    "USERNAME": xname,
                    "NEW_PASSWORD": "NextPassw0rd!",
                },
            },
        )

        result = provider.respond_to_challenge(
            session=SESSION,
            challenge=Challenge.Key.NEW_PASSWORD,
            response={
                "name": "alice",
                "password": "NextPassw0rd!",
            },
        )

        assert result == expected_tokens()

    def test_returns_tokens_for_new_mfa_challenge(
        self,
        provider: provider_module.CognitoAuthProvider,
        stubber: Stubber,
    ) -> None:
        xname = encode_name("alice")
        stubber.add_response(
            "verify_software_token",
            {
                "Session": NEXT_SESSION,
                "Status": "SUCCESS",
            },
            {
                "Session": SESSION,
                "UserCode": "123456",
            },
        )
        stubber.add_response(
            "admin_respond_to_auth_challenge",
            tokens_response(),
            {
                "ClientId": CLIENT_ID,
                "UserPoolId": USER_POOL_ID,
                "Session": NEXT_SESSION,
                "ChallengeName": "MFA_SETUP",
                "ChallengeResponses": {
                    "SECRET_HASH": provider._secret_hash(xname),
                    "USERNAME": xname,
                },
            },
        )

        result = provider.respond_to_challenge(
            session=SESSION,
            challenge=Challenge.Key.NEW_MFA,
            response={
                "name": "alice",
                "code": "123456",
            },
        )

        assert result == expected_tokens()

    def test_returns_tokens_for_mfa_challenge(
        self,
        provider: provider_module.CognitoAuthProvider,
        stubber: Stubber,
    ) -> None:
        xname = encode_name("alice")
        stubber.add_response(
            "admin_respond_to_auth_challenge",
            tokens_response(),
            {
                "ClientId": CLIENT_ID,
                "UserPoolId": USER_POOL_ID,
                "Session": SESSION,
                "ChallengeName": "SOFTWARE_TOKEN_MFA",
                "ChallengeResponses": {
                    "SECRET_HASH": provider._secret_hash(xname),
                    "USERNAME": xname,
                    "SOFTWARE_TOKEN_MFA_CODE": "123456",
                },
            },
        )

        result = provider.respond_to_challenge(
            session=SESSION,
            challenge=Challenge.Key.MFA,
            response={
                "name": "alice",
                "code": "123456",
            },
        )

        assert result == expected_tokens()

    @pytest.mark.parametrize(
        ("code", "expected_error"),
        PROVIDER_ERROR_CASES,
    )
    def test_maps_challenge_response_provider_errors(
        self,
        provider: provider_module.CognitoAuthProvider,
        stubber: Stubber,
        code: str,
        expected_error: type[Exception],
    ) -> None:
        xname = encode_name("alice")
        add_provider_error(
            stubber,
            method="admin_respond_to_auth_challenge",
            code=code,
            expected_params={
                "ClientId": CLIENT_ID,
                "UserPoolId": USER_POOL_ID,
                "Session": SESSION,
                "ChallengeName": "SOFTWARE_TOKEN_MFA",
                "ChallengeResponses": {
                    "SECRET_HASH": provider._secret_hash(xname),
                    "USERNAME": xname,
                    "SOFTWARE_TOKEN_MFA_CODE": "123456",
                },
            },
        )

        with pytest.raises(expected_error):
            provider.respond_to_challenge(
                session=SESSION,
                challenge=Challenge.Key.MFA,
                response={
                    "name": "alice",
                    "code": "123456",
                },
            )


# ──── setup_mfa() ────────────────────────────────────────────────────────────────────


class TestSetupMfa:
    def test_returns_mfa(
        self,
        provider: provider_module.CognitoAuthProvider,
        stubber: Stubber,
    ) -> None:
        stubber.add_response(
            "associate_software_token",
            {
                "SecretCode": "ABCDEFGHIJKLMNOP",
            },
            {
                "AccessToken": "access-token",
            },
        )

        result = provider.setup_mfa(access_token="access-token", name="Alice")

        assert result == expected_mfa()

    @pytest.mark.parametrize(
        ("code", "expected_error"),
        PROVIDER_ERROR_CASES,
    )
    def test_maps_provider_errors(
        self,
        provider: provider_module.CognitoAuthProvider,
        stubber: Stubber,
        code: str,
        expected_error: type[Exception],
    ) -> None:
        add_provider_error(
            stubber,
            method="associate_software_token",
            code=code,
            expected_params={
                "AccessToken": "access-token",
            },
        )

        with pytest.raises(expected_error):
            provider.setup_mfa(access_token="access-token", name="Alice")

    def test_rejects_unexpected_provider_response_shape(
        self,
        provider: provider_module.CognitoAuthProvider,
        stubber: Stubber,
    ) -> None:
        stubber.add_response(
            "associate_software_token",
            {
                "Session": SESSION,
            },
            {
                "AccessToken": "access-token",
            },
        )

        with pytest.raises(
            DomainInvariantViolation,
            match="Unexpected cognito MFA",
        ):
            provider.setup_mfa(access_token="access-token", name="Alice")


# ──── verify_mfa() ───────────────────────────────────────────────────────────────────


class TestVerifyMfa:
    def test_returns_none(
        self,
        provider: provider_module.CognitoAuthProvider,
        stubber: Stubber,
    ) -> None:
        stubber.add_response(
            "verify_software_token",
            {},
            {
                "AccessToken": "access-token",
                "UserCode": "123456",
            },
        )
        stubber.add_response(
            "set_user_mfa_preference",
            {},
            {
                "AccessToken": "access-token",
                "SoftwareTokenMfaSettings": {
                    "Enabled": True,
                    "PreferredMfa": True,
                },
            },
        )

        result = provider.verify_mfa(access_token="access-token", code="123456")

        assert result is None

    @pytest.mark.parametrize(
        ("code", "expected_error"),
        PROVIDER_ERROR_CASES,
    )
    def test_maps_verify_token_provider_errors(
        self,
        provider: provider_module.CognitoAuthProvider,
        stubber: Stubber,
        code: str,
        expected_error: type[Exception],
    ) -> None:
        add_provider_error(
            stubber,
            method="verify_software_token",
            code=code,
            expected_params={
                "AccessToken": "access-token",
                "UserCode": "123456",
            },
        )

        with pytest.raises(expected_error):
            provider.verify_mfa(access_token="access-token", code="123456")

    @pytest.mark.parametrize(
        ("code", "expected_error"),
        PROVIDER_ERROR_CASES,
    )
    def test_maps_set_mfa_preference_provider_errors(
        self,
        provider: provider_module.CognitoAuthProvider,
        stubber: Stubber,
        code: str,
        expected_error: type[Exception],
    ) -> None:
        stubber.add_response(
            "verify_software_token",
            {},
            {
                "AccessToken": "access-token",
                "UserCode": "123456",
            },
        )
        add_provider_error(
            stubber,
            method="set_user_mfa_preference",
            code=code,
            expected_params={
                "AccessToken": "access-token",
                "SoftwareTokenMfaSettings": {
                    "Enabled": True,
                    "PreferredMfa": True,
                },
            },
        )

        with pytest.raises(expected_error):
            provider.verify_mfa(access_token="access-token", code="123456")


# ──── refresh_tokens() ────────────────────────────────────────────────────────────────


class TestRefreshTokens:
    def test_returns_tokens(
        self,
        provider: provider_module.CognitoAuthProvider,
        stubber: Stubber,
    ) -> None:
        stubber.add_response(
            "get_tokens_from_refresh_token",
            tokens_response(),
            {
                "ClientId": CLIENT_ID,
                "ClientSecret": CLIENT_SECRET,
                "RefreshToken": "refresh-token",
            },
        )

        result = provider.refresh_tokens(refresh_token="refresh-token")

        assert result == expected_tokens()

    @pytest.mark.parametrize(
        ("code", "expected_error"),
        PROVIDER_ERROR_CASES,
    )
    def test_maps_provider_errors(
        self,
        provider: provider_module.CognitoAuthProvider,
        stubber: Stubber,
        code: str,
        expected_error: type[Exception],
    ) -> None:
        add_provider_error(
            stubber,
            method="get_tokens_from_refresh_token",
            code=code,
            expected_params={
                "ClientId": CLIENT_ID,
                "ClientSecret": CLIENT_SECRET,
                "RefreshToken": "refresh-token",
            },
        )

        with pytest.raises(expected_error):
            provider.refresh_tokens(refresh_token="refresh-token")


# ──── revoke_tokens() ─────────────────────────────────────────────────────────────────


class TestRevokeTokens:
    def test_returns_none_for_access_token(
        self,
        provider: provider_module.CognitoAuthProvider,
        stubber: Stubber,
    ) -> None:
        stubber.add_response(
            "global_sign_out",
            {},
            {
                "AccessToken": "access-token",
            },
        )

        result = provider.revoke_tokens(access_token="access-token")

        assert result is None

    def test_returns_none_for_refresh_token(
        self,
        provider: provider_module.CognitoAuthProvider,
        stubber: Stubber,
    ) -> None:
        stubber.add_response(
            "revoke_token",
            {},
            {
                "ClientId": CLIENT_ID,
                "ClientSecret": CLIENT_SECRET,
                "Token": "refresh-token",
            },
        )

        result = provider.revoke_tokens(refresh_token="refresh-token")

        assert result is None

    @pytest.mark.parametrize(
        ("access_token", "refresh_token"),
        [
            pytest.param(None, None, id="missing-both"),
            pytest.param("access-token", "refresh-token", id="provided-both"),
        ],
    )
    def test_rejects_invalid_token_combination(
        self,
        provider: provider_module.CognitoAuthProvider,
        access_token: str | None,
        refresh_token: str | None,
    ) -> None:
        with pytest.raises(
            DomainInvariantViolation,
            match="Unexpected combination of access and refresh tokens",
        ):
            provider.revoke_tokens(
                access_token=access_token,
                refresh_token=refresh_token,
            )

    @pytest.mark.parametrize(
        ("code", "expected_error"),
        PROVIDER_ERROR_CASES,
    )
    def test_maps_access_token_provider_errors(
        self,
        provider: provider_module.CognitoAuthProvider,
        stubber: Stubber,
        code: str,
        expected_error: type[Exception],
    ) -> None:
        add_provider_error(
            stubber,
            method="global_sign_out",
            code=code,
            expected_params={
                "AccessToken": "access-token",
            },
        )

        with pytest.raises(expected_error):
            provider.revoke_tokens(access_token="access-token")

    @pytest.mark.parametrize(
        ("code", "expected_error"),
        PROVIDER_ERROR_CASES,
    )
    def test_maps_refresh_token_provider_errors(
        self,
        provider: provider_module.CognitoAuthProvider,
        stubber: Stubber,
        code: str,
        expected_error: type[Exception],
    ) -> None:
        add_provider_error(
            stubber,
            method="revoke_token",
            code=code,
            expected_params={
                "ClientId": CLIENT_ID,
                "ClientSecret": CLIENT_SECRET,
                "Token": "refresh-token",
            },
        )

        with pytest.raises(expected_error):
            provider.revoke_tokens(refresh_token="refresh-token")


# ──── Provider Responses ──────────────────────────────────────────────────────────────


class TestResponseParsing:
    def test_rejects_unexpected_authenticate_response_shape(
        self,
        provider: provider_module.CognitoAuthProvider,
        stubber: Stubber,
    ) -> None:
        xname = encode_name("alice")
        stubber.add_response(
            "admin_initiate_auth",
            {
                "AuthenticationResult": {
                    "AccessToken": "access-token",
                }
            },
            {
                "ClientId": CLIENT_ID,
                "UserPoolId": USER_POOL_ID,
                "AuthFlow": "ADMIN_USER_PASSWORD_AUTH",
                "AuthParameters": {
                    "SECRET_HASH": provider._secret_hash(xname),
                    "USERNAME": xname,
                    "PASSWORD": "Passw0rd!",
                },
            },
        )

        with pytest.raises(
            DomainInvariantViolation,
            match="Unexpected cognito tokens",
        ):
            provider.authenticate(name="alice", password="Passw0rd!")

    def test_rejects_unexpected_challenge_name(
        self,
        provider: provider_module.CognitoAuthProvider,
        stubber: Stubber,
    ) -> None:
        xname = encode_name("alice")
        stubber.add_response(
            "admin_initiate_auth",
            {
                "Session": SESSION,
                "ChallengeName": "UNKNOWN_CHALLENGE",
            },
            {
                "ClientId": CLIENT_ID,
                "UserPoolId": USER_POOL_ID,
                "AuthFlow": "ADMIN_USER_PASSWORD_AUTH",
                "AuthParameters": {
                    "SECRET_HASH": provider._secret_hash(xname),
                    "USERNAME": xname,
                    "PASSWORD": "Passw0rd!",
                },
            },
        )

        with pytest.raises(
            DomainInvariantViolation,
            match="Unexpected cognito challenge",
        ):
            provider.authenticate(name="alice", password="Passw0rd!")
