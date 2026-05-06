import pytest
from shared.errors import DomainNotFound
from user.providers.user import User

from .conftest import make_user

pytestmark = pytest.mark.integration


def test_user_updates_me(
    user_handler_module,
    dummy_user_provider,
    user_caller,
    use_caller,
    apigw_event,
    lambda_context,
    response_body,
):
    use_caller(user_handler_module, user_caller)
    dummy_user_provider.update_result = make_user(id="user-1", name="Alice Updated")

    response = user_handler_module.lambda_handler(
        apigw_event(
            "/user/me",
            {"name": "Alice Updated"},
            method="PATCH",
        ),
        lambda_context,
    )

    assert response["statusCode"] == 200
    assert dummy_user_provider.update_calls[0]["id"] == "user-1"

    body = response_body(response)
    assert body["id"] == "user-1"
    assert body["name"] == "Alice Updated"


def test_user_cannot_update_another_user(
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
        apigw_event(
            "/user/user-2",
            {"name": "Bob Updated"},
            method="PATCH",
        ),
        lambda_context,
    )

    assert response["statusCode"] == 403
    assert response_body(response)["title"] == "Forbidden"
    assert dummy_user_provider.update_calls == []


def test_user_cannot_update_role(
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
        apigw_event(
            "/user/me",
            {"role": "admin"},
            method="PATCH",
        ),
        lambda_context,
    )

    assert response["statusCode"] == 403
    assert response_body(response)["title"] == "Forbidden"
    assert dummy_user_provider.update_calls == []


def test_user_cannot_update_status(
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
        apigw_event(
            "/user/me",
            {"status": "inactive"},
            method="PATCH",
        ),
        lambda_context,
    )

    assert response["statusCode"] == 403
    assert response_body(response)["title"] == "Forbidden"
    assert dummy_user_provider.update_calls == []


def test_admin_updates_another_user_role_and_status(
    user_handler_module,
    dummy_user_provider,
    admin_caller,
    use_caller,
    apigw_event,
    lambda_context,
    response_body,
):
    use_caller(user_handler_module, admin_caller)
    dummy_user_provider.update_result = make_user(
        id="user-2",
        name="Bob",
        role=User.Role.ADMIN,
        status=User.Status.INACTIVE,
    )

    response = user_handler_module.lambda_handler(
        apigw_event(
            "/user/user-2",
            {
                "role": "admin",
                "status": "inactive",
            },
            method="PATCH",
        ),
        lambda_context,
    )

    assert response["statusCode"] == 200
    assert dummy_user_provider.update_calls[0]["id"] == "user-2"

    body = response_body(response)
    assert body["id"] == "user-2"
    assert body["role"] == "admin"
    assert body["status"] == "inactive"


def test_update_user_maps_not_found_to_404(
    user_handler_module,
    dummy_user_provider,
    admin_caller,
    use_caller,
    apigw_event,
    lambda_context,
    response_body,
):
    use_caller(user_handler_module, admin_caller)
    dummy_user_provider.update_error = DomainNotFound("User not found")

    response = user_handler_module.lambda_handler(
        apigw_event(
            "/user/missing-user",
            {"name": "Missing"},
            method="PATCH",
        ),
        lambda_context,
    )

    assert response["statusCode"] == 404
    assert response_body(response)["title"] == "Not Found"
