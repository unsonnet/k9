import pytest
from auth.providers.auth.base import Tokens
from shared.errors import DomainForbidden

pytestmark = pytest.mark.integration


def test_returns_tokens(
    auth_handler_module,
    dummy_provider,
    apigw_event,
    lambda_context,
    response_body,
):
    dummy_provider.refresh_result = Tokens(
        access_token="new-access-token",
        expires_in=3600,
        refresh_token="refresh-token",
        id_token="new-id-token",
    )

    response = auth_handler_module.lambda_handler(
        apigw_event(
            "/auth/refresh",
            {
                "refreshToken": "refresh-token",
            },
        ),
        lambda_context,
    )

    assert response["statusCode"] == 200
    assert response_body(response) == {
        "accessToken": "new-access-token",
        "expiresIn": 3600,
        "refreshToken": "refresh-token",
        "idToken": "new-id-token",
    }


def test_maps_forbidden_to_403(
    auth_handler_module,
    dummy_provider,
    apigw_event,
    lambda_context,
    response_body,
):
    dummy_provider.refresh_error = DomainForbidden()

    response = auth_handler_module.lambda_handler(
        apigw_event(
            "/auth/refresh",
            {
                "refreshToken": "refresh-token",
            },
        ),
        lambda_context,
    )

    assert response["statusCode"] == 403
    assert response_body(response)["title"] == "Forbidden"
