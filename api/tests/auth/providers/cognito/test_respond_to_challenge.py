import pytest
from auth.providers.base import Challenge, Tokens
from botocore.stub import Stubber

from .helpers import token_response

pytestmark = pytest.mark.unit


def test_new_password_uses_expected_payload_and_returns_tokens(
    provider,
    cognito_client,
):
    session = "challenge-session-token"

    expected_params = {
        "ClientId": "client-id",
        "Session": session,
        "ChallengeName": "NEW_PASSWORD_REQUIRED",
        "ChallengeResponses": {
            "SECRET_HASH": provider._secret_hash("alice"),
            "USERNAME": "alice",
            "NEW_PASSWORD": "new-secret",
        },
    }

    with Stubber(cognito_client) as stubber:
        stubber.add_response(
            "respond_to_auth_challenge",
            token_response(),
            expected_params,
        )

        result = provider.respond_to_challenge(
            session=session,
            challenge=Challenge.Key.NEW_PASSWORD,
            response={
                "username": "alice",
                "password": "new-secret",
            },
        )

    assert result == Tokens(
        access_token="access-token",
        expires_in=3600,
        refresh_token="refresh-token",
        id_token="id-token",
    )


def test_mfa_uses_expected_payload_and_returns_tokens(
    provider,
    cognito_client,
):
    session = "challenge-session-token"

    expected_params = {
        "ClientId": "client-id",
        "Session": session,
        "ChallengeName": "SOFTWARE_TOKEN_MFA",
        "ChallengeResponses": {
            "SECRET_HASH": provider._secret_hash("alice"),
            "USERNAME": "alice",
            "SOFTWARE_TOKEN_MFA_CODE": "123456",
        },
    }

    with Stubber(cognito_client) as stubber:
        stubber.add_response(
            "respond_to_auth_challenge",
            token_response(),
            expected_params,
        )

        result = provider.respond_to_challenge(
            session=session,
            challenge=Challenge.Key.MFA,
            response={
                "username": "alice",
                "code": "123456",
            },
        )

    assert result == Tokens(
        access_token="access-token",
        expires_in=3600,
        refresh_token="refresh-token",
        id_token="id-token",
    )


def test_new_mfa_verifies_token_then_returns_tokens(
    provider,
    cognito_client,
):
    initial_session = "initial-session-token"
    verified_session = "verified-session-token"

    expected_verify_params = {
        "Session": initial_session,
        "UserCode": "123456",
    }

    verify_response = {
        "Session": verified_session,
    }

    expected_challenge_params = {
        "ClientId": "client-id",
        "Session": verified_session,
        "ChallengeName": "MFA_SETUP",
        "ChallengeResponses": {
            "SECRET_HASH": provider._secret_hash("alice"),
            "USERNAME": "alice",
        },
    }

    with Stubber(cognito_client) as stubber:
        stubber.add_response(
            "verify_software_token",
            verify_response,
            expected_verify_params,
        )
        stubber.add_response(
            "respond_to_auth_challenge",
            token_response(),
            expected_challenge_params,
        )

        result = provider.respond_to_challenge(
            session=initial_session,
            challenge=Challenge.Key.NEW_MFA,
            response={
                "username": "alice",
                "code": "123456",
            },
        )

    assert result == Tokens(
        access_token="access-token",
        expires_in=3600,
        refresh_token="refresh-token",
        id_token="id-token",
    )
