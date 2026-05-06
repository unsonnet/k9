import pytest
from shared.errors import DomainNotFound

from .conftest import make_user

pytestmark = pytest.mark.integration


def test_user_gets_me(
    user_handler_module,
    dummy_user_provider,
    user_caller,
    use_caller,
    apigw_event,
    lambda_context,
    response_body,
):
    use_caller(user_handler_module, user_caller)
    dummy_user_provider.get_result = make_user(id="user-1", name="Alice")

    response = user_handler_module.lambda_handler(
        apigw_event("/user/me", method="GET"),
        lambda_context,
    )

    assert response["statusCode"] == 200
    assert dummy_user_provider.get_calls == [{"id": "user-1"}]

    body = response_body(response)
    assert body["id"] == "user-1"
    assert body["name"] == "Alice"
    assert body["role"] == "user"
    assert body["status"] == "active"


def test_user_gets_self_by_id(
    user_handler_module,
    dummy_user_provider,
    user_caller,
    use_caller,
    apigw_event,
    lambda_context,
):
    use_caller(user_handler_module, user_caller)
    dummy_user_provider.get_result = make_user(id="user-1", name="Alice")

    response = user_handler_module.lambda_handler(
        apigw_event("/user/user-1", method="GET"),
        lambda_context,
    )

    assert response["statusCode"] == 200
    assert dummy_user_provider.get_calls == [{"id": "user-1"}]


def test_user_cannot_get_another_user(
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
        apigw_event("/user/user-2", method="GET"),
        lambda_context,
    )

    assert response["statusCode"] == 403
    assert response_body(response)["title"] == "Forbidden"
    assert dummy_user_provider.get_calls == []


def test_admin_gets_another_user(
    user_handler_module,
    dummy_user_provider,
    admin_caller,
    use_caller,
    apigw_event,
    lambda_context,
    response_body,
):
    use_caller(user_handler_module, admin_caller)
    dummy_user_provider.get_result = make_user(id="user-2", name="Bob")

    response = user_handler_module.lambda_handler(
        apigw_event("/user/user-2", method="GET"),
        lambda_context,
    )

    assert response["statusCode"] == 200
    assert dummy_user_provider.get_calls == [{"id": "user-2"}]
    assert response_body(response)["id"] == "user-2"


def test_get_user_maps_not_found_to_404(
    user_handler_module,
    dummy_user_provider,
    admin_caller,
    use_caller,
    apigw_event,
    lambda_context,
    response_body,
):
    use_caller(user_handler_module, admin_caller)
    dummy_user_provider.get_error = DomainNotFound("User not found")

    response = user_handler_module.lambda_handler(
        apigw_event("/user/missing-user", method="GET"),
        lambda_context,
    )

    assert response["statusCode"] == 404
    assert response_body(response)["title"] == "Not Found"
