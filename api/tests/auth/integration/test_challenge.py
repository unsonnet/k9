import pytest
from auth.providers.base import Challenge, Tokens
from shared.errors import DomainRateLimited

pytestmark = pytest.mark.integration


def test_returns_tokens(
    auth_handler_module,
    dummy_provider,
    apigw_event,
    lambda_context,
    response_body,
):
    dummy_provider.challenge_result = Tokens(
        access_token="access-token",
        expires_in=3600,
        refresh_token="refresh-token",
        id_token="id-token",
    )

    response = auth_handler_module.lambda_handler(
        apigw_event(
            "/auth/challenge",
            {
                "session": "challenge-session",
                "challenge": "MFA",
                "response": {
                    "username": "alice",
                    "code": "123456",
                },
            },
        ),
        lambda_context,
    )

    assert response["statusCode"] == 200
    assert response_body(response) == {
        "accessToken": "access-token",
        "expiresIn": 3600,
        "refreshToken": "refresh-token",
        "idToken": "id-token",
    }


def test_returns_followup_challenge(
    auth_handler_module,
    dummy_provider,
    apigw_event,
    lambda_context,
    response_body,
):
    dummy_provider.challenge_result = Challenge(
        session="next-session",
        challenge=Challenge.Key.NEW_MFA,
        parameters={"secret": "software-token-secret"},
    )

    response = auth_handler_module.lambda_handler(
        apigw_event(
            "/auth/challenge",
            {
                "session": "challenge-session",
                "challenge": "NEW_PASSWORD",
                "response": {
                    "username": "alice",
                    "password": "new-secret",
                },
            },
        ),
        lambda_context,
    )

    assert response["statusCode"] == 202
    assert response_body(response) == {
        "session": "next-session",
        "challenge": "NEW_MFA",
        "parameters": {"secret": "software-token-secret"},
    }


def test_maps_rate_limit_to_429(
    auth_handler_module,
    dummy_provider,
    apigw_event,
    lambda_context,
    response_body,
):
    dummy_provider.challenge_error = DomainRateLimited()

    response = auth_handler_module.lambda_handler(
        apigw_event(
            "/auth/challenge",
            {
                "session": "challenge-session",
                "challenge": "MFA",
                "response": {
                    "username": "alice",
                    "code": "123456",
                },
            },
        ),
        lambda_context,
    )

    assert response["statusCode"] == 429
    assert response_body(response)["title"] == "Too Many Requests"
