import pytest

pytestmark = pytest.mark.integration


def test_list_users_rejects_invalid_limit(
    user_handler_module,
    admin_caller,
    use_caller,
    apigw_event,
    lambda_context,
):
    use_caller(user_handler_module, admin_caller)

    response = user_handler_module.lambda_handler(
        apigw_event(
            "/user",
            method="GET",
            query_params={"limit": "not-an-int"},
        ),
        lambda_context,
    )

    assert response["statusCode"] in {400, 422}


def test_list_reports_rejects_invalid_limit(
    user_handler_module,
    user_caller,
    use_caller,
    apigw_event,
    lambda_context,
):
    use_caller(user_handler_module, user_caller)

    response = user_handler_module.lambda_handler(
        apigw_event(
            "/user/me/reports",
            method="GET",
            query_params={"limit": "not-an-int"},
        ),
        lambda_context,
    )

    assert response["statusCode"] in {400, 422}


def test_update_user_rejects_invalid_body(
    user_handler_module,
    user_caller,
    use_caller,
    apigw_event,
    lambda_context,
):
    use_caller(user_handler_module, user_caller)

    response = user_handler_module.lambda_handler(
        apigw_event(
            "/user/me",
            {"status": "NOT_A_REAL_STATUS"},
            method="PATCH",
        ),
        lambda_context,
    )

    assert response["statusCode"] in {400, 422}
