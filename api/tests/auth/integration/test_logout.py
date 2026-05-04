import pytest
from shared.errors import DomainInvalidCredentials, DomainInvariantViolation

pytestmark = pytest.mark.integration


def test_returns_204(
    auth_handler_module,
    apigw_event,
    lambda_context,
):
    response = auth_handler_module.lambda_handler(
        apigw_event(
            "/auth/logout",
            {
                "accessToken": "access-token",
            },
        ),
        lambda_context,
    )

    assert response["statusCode"] == 204
    assert response.get("body") in (None, "")


def test_is_idempotent_for_domain_unauthorized(
    auth_handler_module,
    dummy_provider,
    apigw_event,
    lambda_context,
):
    dummy_provider.revoke_error = DomainInvalidCredentials()

    response = auth_handler_module.lambda_handler(
        apigw_event(
            "/auth/logout",
            {
                "accessToken": "access-token",
            },
        ),
        lambda_context,
    )

    assert response["statusCode"] == 204


def test_unexpected_domain_error_falls_back_to_500(
    auth_handler_module,
    dummy_provider,
    apigw_event,
    lambda_context,
    response_body,
):
    dummy_provider.revoke_error = DomainInvariantViolation("unexpected")

    response = auth_handler_module.lambda_handler(
        apigw_event(
            "/auth/logout",
            {
                "accessToken": "access-token",
            },
        ),
        lambda_context,
    )

    assert response["statusCode"] == 500
    assert response_body(response)["title"] == "Internal Server Error"
