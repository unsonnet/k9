import pytest
from auth.providers.base import Challenge, Tokens
from botocore.stub import Stubber
from shared.errors import (
    DomainForbidden,
    DomainInvalidCredentials,
    DomainInvariantViolation,
    DomainRateLimited,
)

from .helpers import auth_params, token_response

pytestmark = pytest.mark.unit


def test_uses_expected_payload_and_returns_tokens(provider, cognito_client):
    with Stubber(cognito_client) as stubber:
        stubber.add_response(
            "initiate_auth",
            token_response(),
            auth_params(provider),
        )

        result = provider.authenticate(username="alice", password="secret")

    assert result == Tokens(
        access_token="access-token",
        expires_in=3600,
        refresh_token="refresh-token",
        id_token="id-token",
    )


def test_returns_new_password_challenge(provider, cognito_client):
    response = {
        "Session": "session-token-00000000",
        "ChallengeName": "NEW_PASSWORD_REQUIRED",
    }

    with Stubber(cognito_client) as stubber:
        stubber.add_response(
            "initiate_auth",
            response,
            auth_params(provider),
        )

        result = provider.authenticate(username="alice", password="secret")

    assert result == Challenge(
        session="session-token-00000000",
        challenge=Challenge.Key.NEW_PASSWORD,
        parameters={},
    )


def test_returns_mfa_challenge(provider, cognito_client):
    response = {
        "Session": "session-token-00000000",
        "ChallengeName": "SOFTWARE_TOKEN_MFA",
    }

    with Stubber(cognito_client) as stubber:
        stubber.add_response(
            "initiate_auth",
            response,
            auth_params(provider),
        )

        result = provider.authenticate(username="alice", password="secret")

    assert result == Challenge(
        session="session-token-00000000",
        challenge=Challenge.Key.MFA,
        parameters={},
    )


def test_returns_new_mfa_challenge(provider, cognito_client):
    initiate_auth_response = {
        "Session": "session-token-00000000",
        "ChallengeName": "MFA_SETUP",
    }

    associate_token_response = {
        "Session": "mfa-setup-session-token",
        "SecretCode": "software-token-secret",
    }

    with Stubber(cognito_client) as stubber:
        stubber.add_response(
            "initiate_auth",
            initiate_auth_response,
            auth_params(provider),
        )
        stubber.add_response(
            "associate_software_token",
            associate_token_response,
            {"Session": "session-token-00000000"},
        )

        result = provider.authenticate(username="alice", password="secret")

    assert result == Challenge(
        session="mfa-setup-session-token",
        challenge=Challenge.Key.NEW_MFA,
        parameters={"secret": "software-token-secret"},
    )


def test_maps_not_authorized_exception(provider, cognito_client):
    with Stubber(cognito_client) as stubber:
        stubber.add_client_error(
            "initiate_auth",
            service_error_code="NotAuthorizedException",
            service_message="invalid credentials",
            http_status_code=400,
            expected_params=auth_params(provider, password="bad"),
        )

        with pytest.raises(DomainInvalidCredentials):
            provider.authenticate(username="alice", password="bad")


def test_maps_forbidden_exception(provider, cognito_client):
    with Stubber(cognito_client) as stubber:
        stubber.add_client_error(
            "initiate_auth",
            service_error_code="ForbiddenException",
            service_message="forbidden",
            http_status_code=400,
            expected_params=auth_params(provider),
        )

        with pytest.raises(DomainForbidden):
            provider.authenticate(username="alice", password="secret")


def test_maps_too_many_requests_exception(provider, cognito_client):
    with Stubber(cognito_client) as stubber:
        stubber.add_client_error(
            "initiate_auth",
            service_error_code="TooManyRequestsException",
            service_message="rate limited",
            http_status_code=429,
            expected_params=auth_params(provider),
        )

        with pytest.raises(DomainRateLimited):
            provider.authenticate(username="alice", password="secret")


def test_malformed_cognito_payload_raises_domain_invariant(provider, cognito_client):
    with Stubber(cognito_client) as stubber:
        stubber.add_response(
            "initiate_auth",
            {},
            auth_params(provider),
        )

        with pytest.raises(DomainInvariantViolation):
            provider.authenticate(username="alice", password="secret")


def test_unknown_cognito_challenge_raises_domain_invariant(provider, cognito_client):
    response = {
        "Session": "session-token-00000000",
        "ChallengeName": "CUSTOM_CHALLENGE",
    }

    with Stubber(cognito_client) as stubber:
        stubber.add_response(
            "initiate_auth",
            response,
            auth_params(provider),
        )

        with pytest.raises(DomainInvariantViolation):
            provider.authenticate(username="alice", password="secret")
