import pytest
from shared.errors import DomainRateLimited
from user.providers.user import User, UserPage

from .conftest import make_user

pytestmark = pytest.mark.integration


def test_admin_lists_users(
    user_handler_module,
    dummy_user_provider,
    admin_caller,
    use_caller,
    apigw_event,
    lambda_context,
    response_body,
):
    use_caller(user_handler_module, admin_caller)
    dummy_user_provider.list_result = UserPage(
        users=[
            make_user(id="user-1", name="Alice", role=User.Role.USER),
            make_user(id="admin-1", name="Admin", role=User.Role.ADMIN),
        ],
        cursor="next-cursor",
    )

    response = user_handler_module.lambda_handler(
        apigw_event(
            "/user",
            method="GET",
            query_params={
                "q": "ali",
                "limit": 10,
                "cursor": "cursor-1",
            },
        ),
        lambda_context,
    )

    assert response["statusCode"] == 200
    assert dummy_user_provider.list_calls == [
        {"q": "ali", "limit": 10, "cursor": "cursor-1"}
    ]

    body = response_body(response)
    assert body["cursor"] == "next-cursor"
    assert body["users"][0]["id"] == "user-1"
    assert body["users"][0]["name"] == "Alice"
    assert body["users"][0]["role"] == "user"


def test_user_cannot_list_users(
    user_handler_module,
    dummy_user_provider,
    user_caller,
    use_caller,
    apigw_event,
    lambda_context,
    response_body,
):
    use_caller(user_handler_module, user_caller)

    response = user_handler_module.lambda_handler(
        apigw_event("/user", method="GET"),
        lambda_context,
    )

    assert response["statusCode"] == 403
    assert response_body(response)["title"] == "Forbidden"
    assert dummy_user_provider.list_calls == []


def test_list_users_requires_authentication(
    user_handler_module,
    use_unauthorized_caller,
    apigw_event,
    lambda_context,
    response_body,
):
    use_unauthorized_caller(user_handler_module)

    response = user_handler_module.lambda_handler(
        apigw_event("/user", method="GET"),
        lambda_context,
    )

    assert response["statusCode"] == 401
    assert response_body(response)["title"] == "Unauthorized"


def test_list_users_maps_rate_limit_to_429(
    user_handler_module,
    dummy_user_provider,
    admin_caller,
    use_caller,
    apigw_event,
    lambda_context,
    response_body,
):
    use_caller(user_handler_module, admin_caller)
    dummy_user_provider.list_error = DomainRateLimited()

    response = user_handler_module.lambda_handler(
        apigw_event("/user", method="GET"),
        lambda_context,
    )

    assert response["statusCode"] == 429
    assert response_body(response)["title"] == "Too Many Requests"
