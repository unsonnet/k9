import importlib
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

import pytest
from shared.abc import Role
from shared.errors import (
    DomainForbidden,
    DomainNotFound,
    DomainRateLimited,
    DomainUnauthorized,
)
from user.provider import User, UserCreds, UserPage

from tests.helpers import (
    ProviderMethod,
    assert_body,
    assert_no_body,
    assert_problem,
    assert_status,
)

pytestmark = pytest.mark.integration


# ──── Helpers ─────────────────────────────────────────────────────────────────────────

TEST_NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)
DATE_FROM = datetime(2026, 1, 1, tzinfo=timezone.utc)
DATE_TO = datetime(2026, 1, 31, 23, 59, tzinfo=timezone.utc)
USER_ID = "user_001"
ADMIN_ID = "admin_001"
OTHER_USER_ID = "user_002"

PROVIDER_ERRORS = [
    pytest.param(DomainUnauthorized(), 401, "Unauthorized", id="unauthorized"),
    pytest.param(DomainForbidden(), 403, "Forbidden", id="forbidden"),
    pytest.param(DomainRateLimited(), 429, "Too Many Requests", id="rate-limited"),
]

PROVIDER_ERRORS_WITH_NOT_FOUND = [
    PROVIDER_ERRORS[0],
    PROVIDER_ERRORS[1],
    pytest.param(DomainNotFound(), 404, "Not Found", id="not-found"),
    PROVIDER_ERRORS[2],
]


class FakeUserProvider:
    def __init__(self) -> None:
        self.list_users = ProviderMethod()
        self.create_user = ProviderMethod()
        self.read_user = ProviderMethod()
        self.update_user = ProviderMethod()
        self.delete_user = ProviderMethod(result=None)
        self.reset_user = ProviderMethod()


def make_user(
    *,
    id: str = USER_ID,
    name: str = "alice",
    role: Role = Role.USER,
    enabled: bool = True,
    created_at: datetime = TEST_NOW,
    updated_at: datetime | None = None,
    last_login_at: datetime | None = None,
) -> User:
    return User(
        id=id,
        name=name,
        role=role,
        enabled=enabled,
        created_at=created_at,
        updated_at=updated_at,
        last_login_at=last_login_at,
    )


def user_body(
    *,
    id: str = USER_ID,
    name: str = "alice",
    role: str = "user",
    enabled: bool = True,
    created_at: str = "2026-01-01T00:00:00Z",
    updated_at: str | None = None,
    last_login_at: str | None = None,
) -> dict[str, Any]:
    return {
        "id": id,
        "name": name,
        "role": role,
        "enabled": enabled,
        "createdAt": created_at,
        "updatedAt": updated_at,
        "lastLoginAt": last_login_at,
    }


# ──── Fixtures ────────────────────────────────────────────────────────────────────────


@pytest.fixture
def user_provider() -> FakeUserProvider:
    return FakeUserProvider()


@pytest.fixture
def user_handler_module(
    monkeypatch: pytest.MonkeyPatch,
    user_provider: FakeUserProvider,
):
    import user.provider as user_provider_module

    monkeypatch.setattr(
        user_provider_module,
        "CognitoUserProvider",
        lambda: user_provider,
    )

    import user.handler as handler

    return importlib.reload(handler)


@pytest.fixture
def invoke_user_api(
    user_handler_module,
    apigw_event,
    lambda_context,
) -> Callable[..., dict[str, Any]]:
    def invoke(
        path: str,
        *,
        method: str = "GET",
        body: dict[str, Any] | None = None,
        query_params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return user_handler_module.lambda_handler(
            apigw_event(
                path,
                body,
                method=method,
                query_params=query_params,
            ),
            lambda_context,
        )

    return invoke


@pytest.fixture
def user_record() -> User:
    return make_user()


@pytest.fixture
def user_page(user_record: User) -> UserPage:
    return UserPage(
        users=[user_record],
        cursor="next-cursor",
    )


@pytest.fixture
def user_creds() -> UserCreds:
    return UserCreds(
        name="alice",
        password="TempPass#2026",
    )


# ──── GET /user ───────────────────────────────────────────────────────────────────────


class TestList:
    def test_returns_page(
        self,
        user_provider: FakeUserProvider,
        invoke_user_api,
        admin_caller,
        use_caller,
        user_page: UserPage,
    ) -> None:
        use_caller(admin_caller)
        user_provider.list_users.result = user_page

        response = invoke_user_api(
            "/user",
            query_params={
                "q": "alice",
                "limit": 10,
                "cursor": "users-cursor",
            },
        )

        assert_status(response, 200)
        assert_body(
            response,
            {
                "users": [user_body()],
                "cursor": "next-cursor",
            },
        )
        assert user_provider.list_users.calls == [
            {
                "q": "alice",
                "limit": 10,
                "cursor": "users-cursor",
            }
        ]

    def test_passes_normalized_query_to_provider(
        self,
        user_provider: FakeUserProvider,
        invoke_user_api,
        admin_caller,
        use_caller,
        user_page: UserPage,
    ) -> None:
        use_caller(admin_caller)
        user_provider.list_users.result = user_page

        response = invoke_user_api(
            "/user",
            query_params={
                "q": '  ALICE "X"  ',
            },
        )

        assert_status(response, 200)
        assert user_provider.list_users.calls == [
            {
                "q": 'alice \\"x\\"',
                "limit": None,
                "cursor": None,
            }
        ]

    def test_accepts_role_claim(
        self,
        user_provider: FakeUserProvider,
        invoke_user_api,
        admin_caller,
        use_caller,
        user_page: UserPage,
    ) -> None:
        use_caller(admin_caller)
        user_provider.list_users.result = user_page

        response = invoke_user_api("/user")

        assert_status(response, 200)
        assert user_provider.list_users.calls == [
            {
                "q": None,
                "limit": None,
                "cursor": None,
            }
        ]

    def test_rejects_invalid_query_params(
        self,
        invoke_user_api,
        admin_caller,
        use_caller,
    ) -> None:
        use_caller(admin_caller)

        response = invoke_user_api(
            "/user",
            query_params={
                "limit": "not-an-int",
            },
        )

        assert_status(response, 422)

    def test_requires_authentication(
        self,
        user_provider: FakeUserProvider,
        invoke_user_api,
        use_unauthorized_caller,
    ) -> None:
        use_unauthorized_caller()

        response = invoke_user_api("/user")

        assert_problem(response, status=401, title="Unauthorized")
        assert user_provider.list_users.calls == []

    def test_requires_admin(
        self,
        user_provider: FakeUserProvider,
        invoke_user_api,
        user_caller,
        use_caller,
    ) -> None:
        use_caller(user_caller)

        response = invoke_user_api("/user")

        assert_problem(response, status=403, title="Forbidden")
        assert user_provider.list_users.calls == []

    @pytest.mark.parametrize(
        ("provider_error", "expected_status", "expected_title"),
        PROVIDER_ERRORS,
    )
    def test_maps_provider_errors(
        self,
        user_provider: FakeUserProvider,
        invoke_user_api,
        admin_caller,
        use_caller,
        provider_error: Exception,
        expected_status: int,
        expected_title: str,
    ) -> None:
        use_caller(admin_caller)
        user_provider.list_users.error = provider_error

        response = invoke_user_api("/user")

        assert_problem(response, status=expected_status, title=expected_title)


# ──── POST /user ──────────────────────────────────────────────────────────────────────


class TestCreate:
    def test_returns_created_user(
        self,
        user_provider: FakeUserProvider,
        invoke_user_api,
        admin_caller,
        use_caller,
        user_creds: UserCreds,
    ) -> None:
        use_caller(admin_caller)
        user_provider.create_user.result = user_creds

        response = invoke_user_api(
            "/user",
            method="POST",
            body={
                "name": "Alice",
                "role": "user",
            },
        )

        assert_status(response, 201)
        assert_body(
            response,
            {
                "name": "alice",
                "password": "TempPass#2026",
            },
        )
        assert user_provider.create_user.calls == [
            {
                "name": "alice",
                "role": Role.USER,
            }
        ]

    @pytest.mark.parametrize(
        "body",
        [
            pytest.param({}, id="missing-all-fields"),
            pytest.param({"name": "Alice"}, id="missing-role"),
            pytest.param({"role": "user"}, id="missing-name"),
            pytest.param({"name": "", "role": "user"}, id="blank-name"),
            pytest.param({"name": "alice", "role": "owner"}, id="invalid-role"),
        ],
    )
    def test_rejects_invalid_body(
        self,
        invoke_user_api,
        admin_caller,
        use_caller,
        body: dict[str, Any],
    ) -> None:
        use_caller(admin_caller)

        response = invoke_user_api(
            "/user",
            method="POST",
            body=body,
        )

        assert_status(response, 422)

    def test_requires_authentication(
        self,
        user_provider: FakeUserProvider,
        invoke_user_api,
        use_unauthorized_caller,
    ) -> None:
        use_unauthorized_caller()

        response = invoke_user_api(
            "/user",
            method="POST",
            body={
                "name": "alice",
                "role": "user",
            },
        )

        assert_problem(response, status=401, title="Unauthorized")
        assert user_provider.create_user.calls == []

    def test_requires_admin(
        self,
        user_provider: FakeUserProvider,
        invoke_user_api,
        user_caller,
        use_caller,
    ) -> None:
        use_caller(user_caller)

        response = invoke_user_api(
            "/user",
            method="POST",
            body={
                "name": "alice",
                "role": "user",
            },
        )

        assert_problem(response, status=403, title="Forbidden")
        assert user_provider.create_user.calls == []

    @pytest.mark.parametrize(
        ("provider_error", "expected_status", "expected_title"),
        PROVIDER_ERRORS,
    )
    def test_maps_provider_errors(
        self,
        user_provider: FakeUserProvider,
        invoke_user_api,
        admin_caller,
        use_caller,
        provider_error: Exception,
        expected_status: int,
        expected_title: str,
    ) -> None:
        use_caller(admin_caller)
        user_provider.create_user.error = provider_error

        response = invoke_user_api(
            "/user",
            method="POST",
            body={
                "name": "alice",
                "role": "user",
            },
        )

        assert_problem(response, status=expected_status, title=expected_title)


# ──── GET /user/<userId> ──────────────────────────────────────────────────────────────


class TestRead:
    @pytest.mark.parametrize(
        ("caller_fixture", "path", "expected_provider_id"),
        [
            pytest.param("user_caller", "/user/me", USER_ID, id="self-alias"),
            pytest.param("user_caller", f"/user/{USER_ID}", USER_ID, id="self-id"),
            pytest.param(
                "admin_caller",
                f"/user/{OTHER_USER_ID}",
                OTHER_USER_ID,
                id="admin-other",
            ),
            pytest.param("admin_caller", "/user/me", ADMIN_ID, id="admin-self-alias"),
        ],
    )
    def test_returns_user(
        self,
        request,
        user_provider: FakeUserProvider,
        invoke_user_api,
        use_caller,
        user_record: User,
        caller_fixture: str,
        path: str,
        expected_provider_id: str,
    ) -> None:
        caller = request.getfixturevalue(caller_fixture)
        use_caller(caller)
        user_provider.read_user.result = user_record

        response = invoke_user_api(path)

        assert_status(response, 200)
        assert_body(response, user_body())
        assert user_provider.read_user.calls == [{"id": expected_provider_id}]

    def test_rejects_invalid_userId(
        self,
        invoke_user_api,
        user_caller,
        use_caller,
    ) -> None:
        use_caller(user_caller)

        response = invoke_user_api("/user/not!valid")

        assert_status(response, 422)

    def test_requires_authentication(
        self,
        user_provider: FakeUserProvider,
        invoke_user_api,
        use_unauthorized_caller,
    ) -> None:
        use_unauthorized_caller()

        response = invoke_user_api("/user/me")

        assert_problem(response, status=401, title="Unauthorized")
        assert user_provider.read_user.calls == []

    def test_forbids_user_reading_other_user(
        self,
        user_provider: FakeUserProvider,
        invoke_user_api,
        user_caller,
        use_caller,
    ) -> None:
        use_caller(user_caller)

        response = invoke_user_api(f"/user/{OTHER_USER_ID}")

        assert_problem(response, status=403, title="Forbidden")
        assert user_provider.read_user.calls == []

    @pytest.mark.parametrize(
        ("provider_error", "expected_status", "expected_title"),
        PROVIDER_ERRORS_WITH_NOT_FOUND,
    )
    def test_maps_provider_errors(
        self,
        user_provider: FakeUserProvider,
        invoke_user_api,
        admin_caller,
        use_caller,
        provider_error: Exception,
        expected_status: int,
        expected_title: str,
    ) -> None:
        use_caller(admin_caller)
        user_provider.read_user.error = provider_error

        response = invoke_user_api(f"/user/{OTHER_USER_ID}")

        assert_problem(response, status=expected_status, title=expected_title)


# ──── PATCH /user/<userId> ────────────────────────────────────────────────────────────


class TestUpdate:
    @pytest.mark.parametrize(
        ("caller_fixture", "path", "body", "expected_provider_call"),
        [
            pytest.param(
                "user_caller",
                "/user/me",
                {"name": "Alice Updated"},
                {
                    "id": USER_ID,
                    "name": "alice updated",
                    "role": None,
                    "enabled": None,
                },
                id="user-self-name",
            ),
            pytest.param(
                "admin_caller",
                f"/user/{OTHER_USER_ID}",
                {"role": "admin"},
                {
                    "id": OTHER_USER_ID,
                    "name": None,
                    "role": Role.ADMIN,
                    "enabled": None,
                },
                id="admin-other-role",
            ),
            pytest.param(
                "admin_caller",
                f"/user/{OTHER_USER_ID}",
                {"enabled": False},
                {
                    "id": OTHER_USER_ID,
                    "name": None,
                    "role": None,
                    "enabled": False,
                },
                id="admin-other-enabled",
            ),
        ],
    )
    def test_returns_updated_user(
        self,
        request,
        user_provider: FakeUserProvider,
        invoke_user_api,
        use_caller,
        user_record: User,
        caller_fixture: str,
        path: str,
        body: dict[str, Any],
        expected_provider_call: dict[str, Any],
    ) -> None:
        caller = request.getfixturevalue(caller_fixture)
        use_caller(caller)
        user_provider.update_user.result = user_record

        response = invoke_user_api(
            path,
            method="PATCH",
            body=body,
        )

        assert_status(response, 200)
        assert_body(response, user_body())
        assert user_provider.update_user.calls == [expected_provider_call]

    @pytest.mark.parametrize(
        "body",
        [
            pytest.param({"name": ""}, id="blank-name"),
            pytest.param({"role": "owner"}, id="invalid-role"),
            pytest.param({"enabled": "true"}, id="invalid-enabled-type"),
        ],
    )
    def test_rejects_invalid_body(
        self,
        invoke_user_api,
        user_caller,
        use_caller,
        body: dict[str, Any],
    ) -> None:
        use_caller(user_caller)

        response = invoke_user_api(
            "/user/me",
            method="PATCH",
            body=body,
        )

        assert_status(response, 422)

    def test_requires_authentication(
        self,
        user_provider: FakeUserProvider,
        invoke_user_api,
        use_unauthorized_caller,
    ) -> None:
        use_unauthorized_caller()

        response = invoke_user_api(
            "/user/me",
            method="PATCH",
            body={"name": "alice"},
        )

        assert_problem(response, status=401, title="Unauthorized")
        assert user_provider.update_user.calls == []

    @pytest.mark.parametrize(
        "body",
        [
            pytest.param({"role": "admin"}, id="role"),
            pytest.param({"enabled": False}, id="enabled"),
        ],
    )
    def test_forbids_user_updating_admin_only_fields(
        self,
        user_provider: FakeUserProvider,
        invoke_user_api,
        user_caller,
        use_caller,
        body: dict[str, Any],
    ) -> None:
        use_caller(user_caller)

        response = invoke_user_api(
            "/user/me",
            method="PATCH",
            body=body,
        )

        assert_problem(response, status=403, title="Forbidden")
        assert user_provider.update_user.calls == []

    def test_forbids_user_updating_other_user(
        self,
        user_provider: FakeUserProvider,
        invoke_user_api,
        user_caller,
        use_caller,
    ) -> None:
        use_caller(user_caller)

        response = invoke_user_api(
            f"/user/{OTHER_USER_ID}",
            method="PATCH",
            body={"name": "bob"},
        )

        assert_problem(response, status=403, title="Forbidden")
        assert user_provider.update_user.calls == []

    @pytest.mark.parametrize(
        ("provider_error", "expected_status", "expected_title"),
        PROVIDER_ERRORS_WITH_NOT_FOUND,
    )
    def test_maps_provider_errors(
        self,
        user_provider: FakeUserProvider,
        invoke_user_api,
        admin_caller,
        use_caller,
        provider_error: Exception,
        expected_status: int,
        expected_title: str,
    ) -> None:
        use_caller(admin_caller)
        user_provider.update_user.error = provider_error

        response = invoke_user_api(
            f"/user/{OTHER_USER_ID}",
            method="PATCH",
            body={"name": "alice"},
        )

        assert_problem(response, status=expected_status, title=expected_title)


# ──── DELETE /user/<userId> ──────────────────────────────────────────────────────────


class TestDelete:
    def test_returns_no_content(
        self,
        user_provider: FakeUserProvider,
        invoke_user_api,
        admin_caller,
        use_caller,
    ) -> None:
        use_caller(admin_caller)

        response = invoke_user_api(
            f"/user/{OTHER_USER_ID}",
            method="DELETE",
        )

        assert_status(response, 204)
        assert_no_body(response)
        assert user_provider.delete_user.calls == [{"id": OTHER_USER_ID}]

    def test_is_idempotent(
        self,
        user_provider: FakeUserProvider,
        invoke_user_api,
        admin_caller,
        use_caller,
    ) -> None:
        use_caller(admin_caller)
        user_provider.delete_user.error = DomainNotFound()

        response = invoke_user_api(
            f"/user/{OTHER_USER_ID}",
            method="DELETE",
        )

        assert_status(response, 204)
        assert_no_body(response)

    def test_rejects_invalid_userId(
        self,
        invoke_user_api,
        admin_caller,
        use_caller,
    ) -> None:
        use_caller(admin_caller)

        response = invoke_user_api(
            "/user/not!valid",
            method="DELETE",
        )

        assert_status(response, 422)

    def test_requires_authentication(
        self,
        user_provider: FakeUserProvider,
        invoke_user_api,
        use_unauthorized_caller,
    ) -> None:
        use_unauthorized_caller()

        response = invoke_user_api(
            f"/user/{OTHER_USER_ID}",
            method="DELETE",
        )

        assert_problem(response, status=401, title="Unauthorized")
        assert user_provider.delete_user.calls == []

    def test_requires_admin(
        self,
        user_provider: FakeUserProvider,
        invoke_user_api,
        user_caller,
        use_caller,
    ) -> None:
        use_caller(user_caller)

        response = invoke_user_api(
            f"/user/{OTHER_USER_ID}",
            method="DELETE",
        )

        assert_problem(response, status=403, title="Forbidden")
        assert user_provider.delete_user.calls == []

    @pytest.mark.parametrize(
        "path",
        [
            pytest.param("/user/me", id="self-alias"),
            pytest.param(f"/user/{ADMIN_ID}", id="self-id"),
        ],
    )
    def test_forbids_deleting_own_profile(
        self,
        user_provider: FakeUserProvider,
        invoke_user_api,
        admin_caller,
        use_caller,
        path: str,
    ) -> None:
        use_caller(admin_caller)

        response = invoke_user_api(
            path,
            method="DELETE",
        )

        assert_problem(response, status=403, title="Forbidden")
        assert user_provider.delete_user.calls == []

    @pytest.mark.parametrize(
        ("provider_error", "expected_status", "expected_title"),
        PROVIDER_ERRORS,
    )
    def test_maps_provider_errors(
        self,
        user_provider: FakeUserProvider,
        invoke_user_api,
        admin_caller,
        use_caller,
        provider_error: Exception,
        expected_status: int,
        expected_title: str,
    ) -> None:
        use_caller(admin_caller)
        user_provider.delete_user.error = provider_error

        response = invoke_user_api(
            f"/user/{OTHER_USER_ID}",
            method="DELETE",
        )

        assert_problem(response, status=expected_status, title=expected_title)


# ──── POST /user/<userId>/reset ───────────────────────────────────────────────────────


class TestReset:
    def test_returns_reset_user_credentials(
        self,
        user_provider: FakeUserProvider,
        invoke_user_api,
        admin_caller,
        use_caller,
        user_creds: UserCreds,
    ) -> None:
        use_caller(admin_caller)
        user_provider.reset_user.result = user_creds

        response = invoke_user_api(
            f"/user/{USER_ID}/reset",
            method="POST",
            body={},
        )

        assert_status(response, 200)
        assert_body(
            response,
            {
                "name": "alice",
                "password": "TempPass#2026",
            },
        )
        assert user_provider.reset_user.calls == [{"id": USER_ID}]

    def test_rejects_invalid_userId(
        self,
        invoke_user_api,
        admin_caller,
        use_caller,
    ) -> None:
        use_caller(admin_caller)

        response = invoke_user_api(
            "/user/me/reset",
            method="POST",
            body={},
        )

        assert_status(response, 422)

    def test_requires_authentication(
        self,
        user_provider: FakeUserProvider,
        invoke_user_api,
        use_unauthorized_caller,
    ) -> None:
        use_unauthorized_caller()

        response = invoke_user_api(
            f"/user/{USER_ID}/reset",
            method="POST",
            body={},
        )

        assert_problem(response, status=401, title="Unauthorized")
        assert user_provider.reset_user.calls == []

    def test_requires_admin(
        self,
        user_provider: FakeUserProvider,
        invoke_user_api,
        user_caller,
        use_caller,
    ) -> None:
        use_caller(user_caller)

        response = invoke_user_api(
            f"/user/{USER_ID}/reset",
            method="POST",
            body={},
        )

        assert_problem(response, status=403, title="Forbidden")
        assert user_provider.reset_user.calls == []

    @pytest.mark.parametrize(
        ("provider_error", "expected_status", "expected_title"),
        PROVIDER_ERRORS_WITH_NOT_FOUND,
    )
    def test_maps_provider_errors(
        self,
        user_provider: FakeUserProvider,
        invoke_user_api,
        admin_caller,
        use_caller,
        provider_error: Exception,
        expected_status: int,
        expected_title: str,
    ) -> None:
        use_caller(admin_caller)
        user_provider.reset_user.error = provider_error

        response = invoke_user_api(
            f"/user/{USER_ID}/reset",
            method="POST",
            body={},
        )

        assert_problem(response, status=expected_status, title=expected_title)


# ──── Routing ─────────────────────────────────────────────────────────────────────────


class TestRouting:
    @pytest.mark.parametrize(
        ("method", "path"),
        [
            pytest.param("PATCH", "/user", id="list-create-user"),
            pytest.param("POST", f"/user/{USER_ID}", id="get-update-delete-user"),
            pytest.param("GET", f"/user/{USER_ID}/reset", id="reset-user"),
        ],
    )
    def test_rejects_unsupported_methods(
        self,
        user_handler_module,
        apigw_event,
        lambda_context,
        method: str,
        path: str,
    ) -> None:
        response = user_handler_module.lambda_handler(
            apigw_event(path, {}, method=method),
            lambda_context,
        )

        assert_status(response, 405)

    def test_returns_not_found_for_unknown_route(
        self,
        user_handler_module,
        apigw_event,
        lambda_context,
    ) -> None:
        response = user_handler_module.lambda_handler(
            apigw_event("/user/unknown/path", {}, method="GET"),
            lambda_context,
        )

        assert_status(response, 404)
