import pytest
from auth.providers.auth import Challenge, Tokens
from shared.errors import DomainInvalidCredentials

pytestmark = pytest.mark.integration


def test_returns_tokens(
    auth_handler_module,
    dummy_provider,
    apigw_event,
    lambda_context,
    response_body,
):
    dummy_provider.authenticate_result = Tokens(
        access_token="access-token",
        expires_in=3600,
        refresh_token="refresh-token",
        id_token="id-token",
    )

    response = auth_handler_module.lambda_handler(
        apigw_event(
            "/auth/login",
            {
                "username": "alice",
                "password": "secret",
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


def test_returns_challenge(
    auth_handler_module,
    dummy_provider,
    apigw_event,
    lambda_context,
    response_body,
):
    dummy_provider.authenticate_result = Challenge(
        session="challenge-session",
        challenge=Challenge.Key.NEW_PASSWORD,
        parameters={},
    )

    response = auth_handler_module.lambda_handler(
        apigw_event(
            "/auth/login",
            {
                "username": "alice",
                "password": "secret",
            },
        ),
        lambda_context,
    )

    assert response["statusCode"] == 202
    assert response_body(response) == {
        "session": "challenge-session",
        "challenge": "NEW_PASSWORD",
        "parameters": {},
    }


def test_maps_invalid_credentials_to_401(
    auth_handler_module,
    dummy_provider,
    apigw_event,
    lambda_context,
    response_body,
):
    dummy_provider.authenticate_error = DomainInvalidCredentials()

    response = auth_handler_module.lambda_handler(
        apigw_event(
            "/auth/login",
            {
                "username": "alice",
                "password": "bad",
            },
        ),
        lambda_context,
    )

    assert response["statusCode"] == 401

    body = response_body(response)
    assert body["title"] == "Unauthorized"
    assert body["detail"] == "Invalid credentials"
