import importlib
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

import pytest
from shared.errors import (
    DomainForbidden,
    DomainNotFound,
    DomainRateLimited,
    DomainUnauthorized,
)
from user.providers.report import Report, ReportPage
from user.providers.user import User, UserPage

pytestmark = pytest.mark.integration


# ──── Helpers ─────────────────────────────────────────────────────────────────────────


TEST_NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


class FakeUserProvider:
    def __init__(self) -> None:
        self.list_result: UserPage | None = None
        self.list_error: Exception | None = None

        self.get_result: User | None = None
        self.get_error: Exception | None = None

        self.update_result: User | None = None
        self.update_error: Exception | None = None

        self.list_calls: list[dict[str, Any]] = []
        self.get_calls: list[dict[str, Any]] = []
        self.update_calls: list[dict[str, Any]] = []

    def list_users(
        self,
        *,
        q: str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> UserPage:
        self.list_calls.append({"q": q, "limit": limit, "cursor": cursor})

        if self.list_error is not None:
            raise self.list_error
        if self.list_result is None:
            raise AssertionError("list_result not configured")

        return self.list_result

    def get_user(self, *, id: str) -> User:
        self.get_calls.append({"id": id})

        if self.get_error is not None:
            raise self.get_error
        if self.get_result is None:
            raise AssertionError("get_result not configured")

        return self.get_result

    def update_user(self, *, id: str, update: User.Update) -> User:
        self.update_calls.append({"id": id, "update": update})

        if self.update_error is not None:
            raise self.update_error
        if self.update_result is None:
            raise AssertionError("update_result not configured")

        return self.update_result


class FakeReportProvider:
    def __init__(self) -> None:
        self.list_result: ReportPage | None = None
        self.list_error: Exception | None = None

        self.list_calls: list[dict[str, Any]] = []

    def list_reports(
        self,
        *,
        user: str,
        q: str | None = None,
        final: bool | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> ReportPage:
        self.list_calls.append(
            {
                "user": user,
                "q": q,
                "final": final,
                "date_from": date_from,
                "date_to": date_to,
                "limit": limit,
                "cursor": cursor,
            }
        )

        if self.list_error is not None:
            raise self.list_error
        if self.list_result is None:
            raise AssertionError("list_result not configured")

        return self.list_result


def make_user(
    *,
    id: str = "user-1",
    name: str = "Alice",
    role: User.Role = User.Role.USER,
    enabled: bool = True,
) -> User:
    return User(
        id=id,
        name=name,
        role=role,
        enabled=enabled,
        created_at=TEST_NOW,
        updated_at=None,
        last_login_at=None,
    )


def make_report(
    *,
    id: str = "report-1",
    user: str = "user-1",
    title: str = "Report One",
    final: bool = False,
) -> Report:
    return Report(
        id=id,
        user=user,
        title=title,
        final=final,
        created_at=TEST_NOW,
        updated_at=None,
    )


def assert_problem_response(
    response: dict[str, Any],
    response_body: Callable[[dict[str, Any]], dict[str, Any]],
    *,
    status: int,
    title: str,
    detail: str | None = None,
) -> None:
    assert response["statusCode"] == status

    body = response_body(response)
    assert body["title"] == title

    if detail is not None:
        assert body["detail"] == detail


# ──── Fixtures ───────────────────────────────────────────────────────────────────────


@pytest.fixture
def user_provider() -> FakeUserProvider:
    return FakeUserProvider()


@pytest.fixture
def report_provider() -> FakeReportProvider:
    return FakeReportProvider()


@pytest.fixture
def user_handler_module(
    monkeypatch: pytest.MonkeyPatch,
    user_provider: FakeUserProvider,
    report_provider: FakeReportProvider,
):
    import user.providers.report as report_provider_module
    import user.providers.user as user_provider_module

    monkeypatch.setattr(
        user_provider_module,
        "CognitoUserProvider",
        lambda: user_provider,
    )
    monkeypatch.setattr(
        report_provider_module,
        "OpenSearchReportProvider",
        lambda: report_provider,
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


# ──── Tests ───────────────────────────────────────────────────────────────────────────


# ──── GET /user ───────────────────────────────────────────────────────────────────────


class TestListUsers:
    def test_returns_user_page_for_admin(
        self,
        user_provider: FakeUserProvider,
        invoke_user_api,
        user_handler_module,
        admin_caller,
        use_caller,
        response_body,
    ) -> None:
        use_caller(user_handler_module, admin_caller)
        user_provider.list_result = UserPage(
            users=[
                make_user(id="user-1", name="Alice", role=User.Role.USER),
                make_user(id="admin-1", name="Admin", role=User.Role.ADMIN),
            ],
            cursor="next-cursor",
        )

        response = invoke_user_api(
            "/user",
            query_params={
                "q": "ali",
                "limit": 10,
                "cursor": "cursor-1",
            },
        )

        assert response["statusCode"] == 200
        assert user_provider.list_calls == [
            {"q": "ali", "limit": 10, "cursor": "cursor-1"}
        ]

        body = response_body(response)
        assert body["cursor"] == "next-cursor"
        assert body["users"][0]["id"] == "user-1"
        assert body["users"][0]["name"] == "Alice"
        assert body["users"][0]["role"] == "user"
        assert body["users"][1]["id"] == "admin-1"
        assert body["users"][1]["name"] == "Admin"
        assert body["users"][1]["role"] == "admin"

    def test_forbids_non_admin(
        self,
        user_provider: FakeUserProvider,
        invoke_user_api,
        user_handler_module,
        user_caller,
        use_caller,
        response_body,
    ) -> None:
        use_caller(user_handler_module, user_caller)

        response = invoke_user_api("/user")

        assert_problem_response(
            response,
            response_body,
            status=403,
            title="Forbidden",
        )
        assert user_provider.list_calls == []

    def test_requires_authentication(
        self,
        user_provider: FakeUserProvider,
        invoke_user_api,
        user_handler_module,
        use_unauthorized_caller,
        response_body,
    ) -> None:
        use_unauthorized_caller(user_handler_module)

        response = invoke_user_api("/user")

        assert_problem_response(
            response,
            response_body,
            status=401,
            title="Unauthorized",
        )
        assert user_provider.list_calls == []

    @pytest.mark.parametrize(
        ("provider_error", "expected_status", "expected_title"),
        [
            pytest.param(DomainUnauthorized(), 401, "Unauthorized", id="unauthorized"),
            pytest.param(DomainForbidden(), 403, "Forbidden", id="forbidden"),
            pytest.param(
                DomainRateLimited(),
                429,
                "Too Many Requests",
                id="rate-limited",
            ),
        ],
    )
    def test_maps_domain_errors(
        self,
        user_provider: FakeUserProvider,
        invoke_user_api,
        user_handler_module,
        admin_caller,
        use_caller,
        provider_error: Exception,
        expected_status: int,
        expected_title: str,
        response_body,
    ) -> None:
        use_caller(user_handler_module, admin_caller)
        user_provider.list_error = provider_error

        response = invoke_user_api("/user")

        assert_problem_response(
            response,
            response_body,
            status=expected_status,
            title=expected_title,
        )

    @pytest.mark.parametrize(
        "query_params",
        [
            pytest.param({"limit": "not-an-int"}, id="invalid-limit"),
        ],
    )
    def test_rejects_invalid_query_params(
        self,
        invoke_user_api,
        user_handler_module,
        admin_caller,
        use_caller,
        query_params: dict[str, Any],
    ) -> None:
        use_caller(user_handler_module, admin_caller)

        response = invoke_user_api("/user", query_params=query_params)

        assert response["statusCode"] == 422


# ──── GET /user/<userId> ──────────────────────────────────────────────────────────────


class TestGetUser:
    @pytest.mark.parametrize(
        ("path", "expected_provider_id"),
        [
            pytest.param("/user/me", "user-1", id="me"),
            pytest.param("/user/user-1", "user-1", id="self-id"),
        ],
    )
    def test_returns_user_for_self(
        self,
        user_provider: FakeUserProvider,
        invoke_user_api,
        user_handler_module,
        user_caller,
        use_caller,
        path: str,
        expected_provider_id: str,
        response_body,
    ) -> None:
        use_caller(user_handler_module, user_caller)
        user_provider.get_result = make_user(id="user-1", name="Alice")

        response = invoke_user_api(path)

        assert response["statusCode"] == 200
        assert user_provider.get_calls == [{"id": expected_provider_id}]

        body = response_body(response)
        assert body["id"] == "user-1"
        assert body["name"] == "Alice"
        assert body["role"] == "user"
        assert body["enabled"] is True

    def test_returns_user_for_admin_reading_another_user(
        self,
        user_provider: FakeUserProvider,
        invoke_user_api,
        user_handler_module,
        admin_caller,
        use_caller,
        response_body,
    ) -> None:
        use_caller(user_handler_module, admin_caller)
        user_provider.get_result = make_user(id="user-2", name="Bob")

        response = invoke_user_api("/user/user-2")

        assert response["statusCode"] == 200
        assert user_provider.get_calls == [{"id": "user-2"}]

        body = response_body(response)
        assert body["id"] == "user-2"
        assert body["name"] == "Bob"
        assert body["role"] == "user"
        assert body["enabled"] is True

    def test_forbids_user_reading_another_user(
        self,
        user_provider: FakeUserProvider,
        invoke_user_api,
        user_handler_module,
        user_caller,
        use_caller,
        response_body,
    ) -> None:
        use_caller(user_handler_module, user_caller)

        response = invoke_user_api("/user/user-2")

        assert_problem_response(
            response,
            response_body,
            status=403,
            title="Forbidden",
        )
        assert user_provider.get_calls == []

    def test_requires_authentication(
        self,
        user_provider: FakeUserProvider,
        invoke_user_api,
        user_handler_module,
        use_unauthorized_caller,
        response_body,
    ) -> None:
        use_unauthorized_caller(user_handler_module)

        response = invoke_user_api("/user/me")

        assert_problem_response(
            response,
            response_body,
            status=401,
            title="Unauthorized",
        )
        assert user_provider.get_calls == []

    @pytest.mark.parametrize(
        ("provider_error", "expected_status", "expected_title"),
        [
            pytest.param(DomainUnauthorized(), 401, "Unauthorized", id="unauthorized"),
            pytest.param(DomainForbidden(), 403, "Forbidden", id="forbidden"),
            pytest.param(
                DomainNotFound("User not found"),
                404,
                "Not Found",
                id="not-found",
            ),
            pytest.param(
                DomainRateLimited(),
                429,
                "Too Many Requests",
                id="rate-limited",
            ),
        ],
    )
    def test_maps_domain_errors(
        self,
        user_provider: FakeUserProvider,
        invoke_user_api,
        user_handler_module,
        admin_caller,
        use_caller,
        provider_error: Exception,
        expected_status: int,
        expected_title: str,
        response_body,
    ) -> None:
        use_caller(user_handler_module, admin_caller)
        user_provider.get_error = provider_error

        response = invoke_user_api("/user/user-2")

        assert_problem_response(
            response,
            response_body,
            status=expected_status,
            title=expected_title,
        )


# ──── PATCH /user/<userId> ────────────────────────────────────────────────────────────


class TestUpdateUser:
    @pytest.mark.parametrize(
        ("path", "expected_provider_id"),
        [
            pytest.param("/user/me", "user-1", id="me"),
            pytest.param("/user/user-1", "user-1", id="self-id"),
        ],
    )
    def test_updates_self_profile_fields(
        self,
        user_provider: FakeUserProvider,
        invoke_user_api,
        user_handler_module,
        user_caller,
        use_caller,
        path: str,
        expected_provider_id: str,
        response_body,
    ) -> None:
        use_caller(user_handler_module, user_caller)
        user_provider.update_result = make_user(
            id="user-1",
            name="Alice Updated",
        )

        response = invoke_user_api(
            path,
            method="PATCH",
            body={"name": "Alice Updated"},
        )

        assert response["statusCode"] == 200
        assert user_provider.update_calls == [
            {
                "id": expected_provider_id,
                "update": {"name": "Alice Updated"},
            }
        ]

        body = response_body(response)
        assert body["id"] == "user-1"
        assert body["name"] == "Alice Updated"
        assert body["role"] == "user"
        assert body["enabled"] is True

    def test_updates_another_user_for_admin(
        self,
        user_provider: FakeUserProvider,
        invoke_user_api,
        user_handler_module,
        admin_caller,
        use_caller,
        response_body,
    ) -> None:
        use_caller(user_handler_module, admin_caller)
        user_provider.update_result = make_user(
            id="user-2",
            name="Bob Updated",
        )

        response = invoke_user_api(
            "/user/user-2",
            method="PATCH",
            body={"name": "Bob Updated"},
        )

        assert response["statusCode"] == 200
        assert user_provider.update_calls == [
            {
                "id": "user-2",
                "update": {"name": "Bob Updated"},
            }
        ]

        body = response_body(response)
        assert body["id"] == "user-2"
        assert body["name"] == "Bob Updated"
        assert body["role"] == "user"
        assert body["enabled"] is True

    def test_updates_admin_only_fields_for_admin(
        self,
        user_provider: FakeUserProvider,
        invoke_user_api,
        user_handler_module,
        admin_caller,
        use_caller,
        response_body,
    ) -> None:
        use_caller(user_handler_module, admin_caller)
        user_provider.update_result = make_user(
            id="user-2",
            name="Bob",
            role=User.Role.ADMIN,
            enabled=False,
        )

        response = invoke_user_api(
            "/user/user-2",
            method="PATCH",
            body={
                "role": "admin",
                "enabled": False,
            },
        )

        assert response["statusCode"] == 200
        assert user_provider.update_calls == [
            {
                "id": "user-2",
                "update": {
                    "role": User.Role.ADMIN,
                    "enabled": False,
                },
            }
        ]

        body = response_body(response)
        assert body["id"] == "user-2"
        assert body["name"] == "Bob"
        assert body["role"] == "admin"
        assert body["enabled"] is False

    def test_forbids_user_updating_another_user(
        self,
        user_provider: FakeUserProvider,
        invoke_user_api,
        user_handler_module,
        user_caller,
        use_caller,
        response_body,
    ) -> None:
        use_caller(user_handler_module, user_caller)

        response = invoke_user_api(
            "/user/user-2",
            method="PATCH",
            body={"name": "Bob Updated"},
        )

        assert_problem_response(
            response,
            response_body,
            status=403,
            title="Forbidden",
        )
        assert user_provider.update_calls == []

    @pytest.mark.parametrize(
        "payload",
        [
            pytest.param({"role": "admin"}, id="role"),
            pytest.param({"enabled": False}, id="enabled"),
            pytest.param({"role": "admin", "enabled": False}, id="role-and-enabled"),
        ],
    )
    def test_forbids_user_updating_admin_only_fields(
        self,
        user_provider: FakeUserProvider,
        invoke_user_api,
        user_handler_module,
        user_caller,
        use_caller,
        payload: dict[str, Any],
        response_body,
    ) -> None:
        use_caller(user_handler_module, user_caller)

        response = invoke_user_api(
            "/user/me",
            method="PATCH",
            body=payload,
        )

        assert_problem_response(
            response,
            response_body,
            status=403,
            title="Forbidden",
        )
        assert user_provider.update_calls == []

    def test_requires_authentication(
        self,
        user_provider: FakeUserProvider,
        invoke_user_api,
        user_handler_module,
        use_unauthorized_caller,
        response_body,
    ) -> None:
        use_unauthorized_caller(user_handler_module)

        response = invoke_user_api(
            "/user/me",
            method="PATCH",
            body={"name": "Alice Updated"},
        )

        assert_problem_response(
            response,
            response_body,
            status=401,
            title="Unauthorized",
        )
        assert user_provider.update_calls == []

    @pytest.mark.parametrize(
        ("provider_error", "expected_status", "expected_title"),
        [
            pytest.param(DomainUnauthorized(), 401, "Unauthorized", id="unauthorized"),
            pytest.param(DomainForbidden(), 403, "Forbidden", id="forbidden"),
            pytest.param(
                DomainNotFound("User not found"),
                404,
                "Not Found",
                id="not-found",
            ),
            pytest.param(
                DomainRateLimited(),
                429,
                "Too Many Requests",
                id="rate-limited",
            ),
        ],
    )
    def test_maps_domain_errors(
        self,
        user_provider: FakeUserProvider,
        invoke_user_api,
        user_handler_module,
        admin_caller,
        use_caller,
        provider_error: Exception,
        expected_status: int,
        expected_title: str,
        response_body,
    ) -> None:
        use_caller(user_handler_module, admin_caller)
        user_provider.update_error = provider_error

        response = invoke_user_api(
            "/user/user-2",
            method="PATCH",
            body={"name": "Bob Updated"},
        )

        assert_problem_response(
            response,
            response_body,
            status=expected_status,
            title=expected_title,
        )

    @pytest.mark.parametrize(
        "payload",
        [
            pytest.param({"enabled": "not-a-bool"}, id="invalid-enabled"),
            pytest.param({"role": "not-a-role"}, id="invalid-role"),
        ],
    )
    def test_rejects_invalid_body(
        self,
        invoke_user_api,
        user_handler_module,
        user_caller,
        use_caller,
        payload: dict[str, Any],
    ) -> None:
        use_caller(user_handler_module, user_caller)

        response = invoke_user_api(
            "/user/me",
            method="PATCH",
            body=payload,
        )

        assert response["statusCode"] == 422


# ──── GET /user/<userId>/reports ──────────────────────────────────────────────────────


class TestListReports:
    @pytest.mark.parametrize(
        ("path", "expected_provider_user"),
        [
            pytest.param("/user/me/reports", "user-1", id="me"),
            pytest.param("/user/user-1/reports", "user-1", id="self-id"),
        ],
    )
    def test_returns_report_page_for_self(
        self,
        report_provider: FakeReportProvider,
        invoke_user_api,
        user_handler_module,
        user_caller,
        use_caller,
        path: str,
        expected_provider_user: str,
        response_body,
    ) -> None:
        use_caller(user_handler_module, user_caller)
        report_provider.list_result = ReportPage(
            reports=[
                make_report(
                    id="report-1",
                    user="user-1",
                    title="Report One",
                    final=True,
                )
            ],
            cursor="next-cursor",
        )

        response = invoke_user_api(
            path,
            query_params={
                "q": "report",
                "final": "true",
                "dateFrom": "2026-01-01T00:00:00Z",
                "dateTo": "2026-01-31T23:59:59Z",
                "limit": 10,
                "cursor": "cursor-1",
            },
        )

        assert response["statusCode"] == 200
        assert report_provider.list_calls == [
            {
                "user": expected_provider_user,
                "q": "report",
                "final": True,
                "date_from": datetime(2026, 1, 1, tzinfo=timezone.utc),
                "date_to": datetime(2026, 1, 31, 23, 59, 59, tzinfo=timezone.utc),
                "limit": 10,
                "cursor": "cursor-1",
            }
        ]

        body = response_body(response)
        assert body["cursor"] == "next-cursor"
        assert body["reports"][0]["id"] == "report-1"
        assert body["reports"][0]["user"] == "user-1"
        assert body["reports"][0]["title"] == "Report One"
        assert body["reports"][0]["final"] is True

    def test_returns_report_page_for_admin_reading_another_user(
        self,
        report_provider: FakeReportProvider,
        invoke_user_api,
        user_handler_module,
        admin_caller,
        use_caller,
        response_body,
    ) -> None:
        use_caller(user_handler_module, admin_caller)
        report_provider.list_result = ReportPage(
            reports=[
                make_report(
                    id="report-2",
                    user="user-2",
                    title="Report Two",
                )
            ],
            cursor=None,
        )

        response = invoke_user_api("/user/user-2/reports")

        assert response["statusCode"] == 200
        assert report_provider.list_calls == [
            {
                "user": "user-2",
                "q": None,
                "final": None,
                "date_from": None,
                "date_to": None,
                "limit": None,
                "cursor": None,
            }
        ]

        body = response_body(response)
        assert body["cursor"] is None
        assert body["reports"][0]["id"] == "report-2"
        assert body["reports"][0]["user"] == "user-2"
        assert body["reports"][0]["title"] == "Report Two"
        assert body["reports"][0]["final"] is False

    def test_forbids_user_reading_another_users_reports(
        self,
        report_provider: FakeReportProvider,
        invoke_user_api,
        user_handler_module,
        user_caller,
        use_caller,
        response_body,
    ) -> None:
        use_caller(user_handler_module, user_caller)

        response = invoke_user_api("/user/user-2/reports")

        assert_problem_response(
            response,
            response_body,
            status=403,
            title="Forbidden",
        )
        assert report_provider.list_calls == []

    def test_requires_authentication(
        self,
        report_provider: FakeReportProvider,
        invoke_user_api,
        user_handler_module,
        use_unauthorized_caller,
        response_body,
    ) -> None:
        use_unauthorized_caller(user_handler_module)

        response = invoke_user_api("/user/me/reports")

        assert_problem_response(
            response,
            response_body,
            status=401,
            title="Unauthorized",
        )
        assert report_provider.list_calls == []

    @pytest.mark.parametrize(
        ("provider_error", "expected_status", "expected_title"),
        [
            pytest.param(DomainUnauthorized(), 401, "Unauthorized", id="unauthorized"),
            pytest.param(DomainForbidden(), 403, "Forbidden", id="forbidden"),
            pytest.param(
                DomainNotFound("User not found"),
                404,
                "Not Found",
                id="not-found",
            ),
            pytest.param(
                DomainRateLimited(),
                429,
                "Too Many Requests",
                id="rate-limited",
            ),
        ],
    )
    def test_maps_domain_errors(
        self,
        report_provider: FakeReportProvider,
        invoke_user_api,
        user_handler_module,
        admin_caller,
        use_caller,
        provider_error: Exception,
        expected_status: int,
        expected_title: str,
        response_body,
    ) -> None:
        use_caller(user_handler_module, admin_caller)
        report_provider.list_error = provider_error

        response = invoke_user_api("/user/user-2/reports")

        assert_problem_response(
            response,
            response_body,
            status=expected_status,
            title=expected_title,
        )

    @pytest.mark.parametrize(
        "query_params",
        [
            pytest.param({"limit": "not-an-int"}, id="invalid-limit"),
            pytest.param({"limit": "0"}, id="limit-too-low"),
            pytest.param({"limit": "101"}, id="limit-too-high"),
            pytest.param({"final": "not-a-bool"}, id="invalid-final"),
            pytest.param({"dateFrom": "not-a-date"}, id="invalid-date-from"),
            pytest.param({"dateTo": "not-a-date"}, id="invalid-date-to"),
            pytest.param(
                {
                    "dateFrom": "2026-02-01T00:00:00Z",
                    "dateTo": "2026-01-01T00:00:00Z",
                },
                id="date-range-backwards",
            ),
        ],
    )
    def test_rejects_invalid_query_params(
        self,
        invoke_user_api,
        user_handler_module,
        user_caller,
        use_caller,
        query_params: dict[str, Any],
    ) -> None:
        use_caller(user_handler_module, user_caller)

        response = invoke_user_api(
            "/user/me/reports",
            query_params=query_params,
        )

        assert response["statusCode"] == 422


# ──── Routing ────────────────────────────────────────────────────────────────────────


class TestRouting:
    @pytest.mark.parametrize(
        ("path", "method"),
        [
            pytest.param("/user", "POST", id="post-user"),
            pytest.param("/user/user-1", "POST", id="post-user-id"),
            pytest.param("/user/user-1/reports", "POST", id="post-user-id-reports"),
            pytest.param("/user/user-1/reports", "PATCH", id="patch-user-id-reports"),
        ],
    )
    def test_rejects_unsupported_methods(
        self,
        invoke_user_api,
        path: str,
        method: str,
    ) -> None:
        response = invoke_user_api(path, method=method, body={})

        assert response["statusCode"] == 405

    @pytest.mark.parametrize(
        "path",
        [
            pytest.param("/user/unknown/extra", id="extra-path-segment"),
            pytest.param("/users", id="wrong-prefix"),
            pytest.param("/user/me/report", id="wrong-report-route"),
        ],
    )
    def test_returns_not_found_for_unknown_route(
        self,
        invoke_user_api,
        path: str,
    ) -> None:
        response = invoke_user_api(path)

        assert response["statusCode"] == 404
