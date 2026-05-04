import pytest

pytestmark = pytest.mark.integration


def test_login_rejects_invalid_body(
    auth_handler_module,
    apigw_event,
    lambda_context,
):
    response = auth_handler_module.lambda_handler(
        apigw_event(
            "/auth/login",
            {
                "username": "alice",
            },
        ),
        lambda_context,
    )

    assert response["statusCode"] in {400, 422}


def test_challenge_rejects_invalid_challenge_value(
    auth_handler_module,
    apigw_event,
    lambda_context,
):
    response = auth_handler_module.lambda_handler(
        apigw_event(
            "/auth/challenge",
            {
                "session": "challenge-session",
                "challenge": "NOT_A_REAL_CHALLENGE",
                "response": {
                    "username": "alice",
                    "code": "123456",
                },
            },
        ),
        lambda_context,
    )

    assert response["statusCode"] in {400, 422}


def test_refresh_rejects_invalid_body(
    auth_handler_module,
    apigw_event,
    lambda_context,
):
    response = auth_handler_module.lambda_handler(
        apigw_event(
            "/auth/refresh",
            {},
        ),
        lambda_context,
    )

    assert response["statusCode"] in {400, 422}
