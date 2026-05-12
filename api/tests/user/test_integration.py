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
from shared.http import Caller
from shared.providers.cognito import encode_id
from user.providers.report import Report, ReportPage
from user.providers.user import User, UserPage

from tests.helpers import ProviderMethod, assert_body, assert_problem, assert_status

pytestmark = pytest.mark.integration


# ──── Helpers ─────────────────────────────────────────────────────────────────────────


TEST_NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)
UTC = timezone.utc

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
        self.get_user = ProviderMethod()
        self.update_user = ProviderMethod()


class FakeReportProvider:
    def __init__(self) -> None:
        self.list_reports = ProviderMethod()


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
    return Report.model_validate(
        {
            "id": id,
            "xuser": encode_id(user),
            "title": title,
            "final": final,
            "created_at": TEST_NOW,
            "updated_at": None,
        }
    )


def user_body(
    *,
    id: str = "user-1",
    name: str = "Alice",
    role: str = "user",
    enabled: bool = True,
) -> dict[str, Any]:
    return {
        "id": id,
        "name": name,
        "role": role,
        "enabled": enabled,
        "createdAt": "2026-01-01T00:00:00Z",
        "updatedAt": None,
        "lastLoginAt": None,
    }


def report_body(
    *,
    id: str = "report-1",
    user: str = "user-1",
    title: str = "Report One",
    final: bool = False,
) -> dict[str, Any]:
    return {
        "id": id,
        "user": user,
        "title": title,
        "final": final,
        "createdAt": "2026-01-01T00:00:00Z",
        "updatedAt": None,
    }


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


@pytest.fixture
def user_record() -> User:
    return make_user()


@pytest.fixture
def admin_record() -> User:
    return make_user(
        id="admin-1",
        name="Admin",
        role=User.Role.ADMIN,
    )


@pytest.fixture
def user_page(
    user_record: User,
    admin_record: User,
) -> UserPage:
    return UserPage(
        users=[user_record, admin_record],
        cursor="next-cursor",
    )


@pytest.fixture
def report_record() -> Report:
    return make_report()


@pytest.fixture
def report_page(report_record: Report) -> ReportPage:
    return ReportPage(
        reports=[report_record],
        cursor="next-cursor",
    )


# ──── GET /user ───────────────────────────────────────────────────────────────────────


class TestListUsers:
    def test_returns_page(
        self,
        user_provider: FakeUserProvider,
        invoke_user_api,
        admin_caller: Caller,
        use_caller,
        user_page: UserPage,
    ) -> None:
        use_caller(admin_caller)
        user_provider.list_users.result = user_page

        response = invoke_user_api(
            "/user",
            query_params={
                "q": "ali",
                "limit": 10,
                "cursor": "cursor-1",
            },
        )

        assert_status(response, 200)
        assert_body(
            response,
            {
                "users": [
                    user_body(),
                    user_body(
                        id="admin-1",
                        name="Admin",
                        role="admin",
                    ),
                ],
                "cursor": "next-cursor",
            },
        )
        assert user_provider.list_users.calls == [
            {
                "q": "ali",
                "limit": 10,
                "cursor": "cursor-1",
            }
        ]

    def test_passes_normalized_query_to_provider(
        self,
        user_provider: FakeUserProvider,
        invoke_user_api,
        admin_caller: Caller,
        use_caller,
    ) -> None:
        use_caller(admin_caller)
        user_provider.list_users.result = UserPage(users=[], cursor=None)

        response = invoke_user_api(
            "/user",
            query_params={"q": '  Alice   "Smith"  '},
        )

        assert_status(response, 200)
        assert user_provider.list_users.calls == [
            {
                "q": 'alice \\"smith\\"',
                "limit": None,
                "cursor": None,
            }
        ]

    def test_accepts_comma_delimited_groups_claim(
        self,
        user_provider: FakeUserProvider,
        invoke_user_api,
        admin_caller: Caller,
        use_caller,
    ) -> None:
        use_caller(admin_caller, groups_as_string=True)
        user_provider.list_users.result = UserPage(users=[], cursor=None)

        response = invoke_user_api("/user")

        assert_status(response, 200)
        assert user_provider.list_users.calls == [
            {
                "q": None,
                "limit": None,
                "cursor": None,
            }
        ]

    @pytest.mark.parametrize(
        "query_params",
        [
            pytest.param({"limit": "not-an-int"}, id="invalid-limit"),
        ],
    )
    def test_rejects_invalid_query_params(
        self,
        invoke_user_api,
        admin_caller: Caller,
        use_caller,
        query_params: dict[str, Any],
    ) -> None:
        use_caller(admin_caller)

        response = invoke_user_api("/user", query_params=query_params)

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
        user_caller: Caller,
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
        admin_caller: Caller,
        use_caller,
        provider_error: Exception,
        expected_status: int,
        expected_title: str,
    ) -> None:
        use_caller(admin_caller)
        user_provider.list_users.error = provider_error

        response = invoke_user_api("/user")

        assert_problem(
            response,
            status=expected_status,
            title=expected_title,
        )


# ──── GET /user/{userId} ──────────────────────────────────────────────────────────────


class TestGetUser:
    @pytest.mark.parametrize(
        ("caller_fixture", "path", "expected_provider_id"),
        [
            pytest.param("user_caller", "/user/me", "user-1", id="self-alias"),
            pytest.param("user_caller", "/user/user-1", "user-1", id="self-id"),
            pytest.param("admin_caller", "/user/user-1", "user-1", id="admin-other"),
            pytest.param("admin_caller", "/user/me", "admin-1", id="admin-self-alias"),
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
        user_provider.get_user.result = user_record

        response = invoke_user_api(path)

        assert_status(response, 200)
        assert_body(response, user_body())
        assert user_provider.get_user.calls == [
            {
                "id": expected_provider_id,
            }
        ]

    def test_requires_authentication(
        self,
        user_provider: FakeUserProvider,
        invoke_user_api,
        use_unauthorized_caller,
    ) -> None:
        use_unauthorized_caller()

        response = invoke_user_api("/user/me")

        assert_problem(response, status=401, title="Unauthorized")
        assert user_provider.get_user.calls == []

    def test_forbids_user_reading_other_user(
        self,
        user_provider: FakeUserProvider,
        invoke_user_api,
        user_caller: Caller,
        use_caller,
    ) -> None:
        use_caller(user_caller)

        response = invoke_user_api("/user/other-user")

        assert_problem(response, status=403, title="Forbidden")
        assert user_provider.get_user.calls == []

    @pytest.mark.parametrize(
        ("provider_error", "expected_status", "expected_title"),
        PROVIDER_ERRORS_WITH_NOT_FOUND,
    )
    def test_maps_provider_errors(
        self,
        user_provider: FakeUserProvider,
        invoke_user_api,
        admin_caller: Caller,
        use_caller,
        provider_error: Exception,
        expected_status: int,
        expected_title: str,
    ) -> None:
        use_caller(admin_caller)
        user_provider.get_user.error = provider_error

        response = invoke_user_api("/user/user-1")

        assert_problem(
            response,
            status=expected_status,
            title=expected_title,
        )


# ──── PATCH /user/{userId} ────────────────────────────────────────────────────────────


class TestUpdateUser:
    @pytest.mark.parametrize(
        ("caller_fixture", "path", "body", "expected_provider_call"),
        [
            pytest.param(
                "user_caller",
                "/user/me",
                {"name": "Alice Updated"},
                {
                    "id": "user-1",
                    "update": {
                        "name": "alice updated",
                    },
                },
                id="self-alias",
            ),
            pytest.param(
                "admin_caller",
                "/user/user-1",
                {"name": "Alice Updated"},
                {
                    "id": "user-1",
                    "update": {
                        "name": "alice updated",
                    },
                },
                id="admin-other",
            ),
            pytest.param(
                "admin_caller",
                "/user/me",
                {
                    "role": "admin",
                    "enabled": False,
                },
                {
                    "id": "admin-1",
                    "update": {
                        "role": User.Role.ADMIN,
                        "enabled": False,
                    },
                },
                id="admin-fields",
            ),
        ],
    )
    def test_updates_user(
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
            pytest.param({"enabled": "yes"}, id="invalid-enabled"),
        ],
    )
    def test_rejects_invalid_body(
        self,
        invoke_user_api,
        user_caller: Caller,
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
            body={"name": "Alice"},
        )

        assert_problem(response, status=401, title="Unauthorized")
        assert user_provider.update_user.calls == []

    def test_forbids_user_updating_other_user(
        self,
        user_provider: FakeUserProvider,
        invoke_user_api,
        user_caller: Caller,
        use_caller,
    ) -> None:
        use_caller(user_caller)

        response = invoke_user_api(
            "/user/other-user",
            method="PATCH",
            body={"name": "Other"},
        )

        assert_problem(response, status=403, title="Forbidden")
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
        user_caller: Caller,
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

    @pytest.mark.parametrize(
        ("provider_error", "expected_status", "expected_title"),
        PROVIDER_ERRORS_WITH_NOT_FOUND,
    )
    def test_maps_provider_errors(
        self,
        user_provider: FakeUserProvider,
        invoke_user_api,
        admin_caller: Caller,
        use_caller,
        provider_error: Exception,
        expected_status: int,
        expected_title: str,
    ) -> None:
        use_caller(admin_caller)
        user_provider.update_user.error = provider_error

        response = invoke_user_api(
            "/user/user-1",
            method="PATCH",
            body={"name": "Alice"},
        )

        assert_problem(
            response,
            status=expected_status,
            title=expected_title,
        )


# ──── GET /user/{userId}/reports ──────────────────────────────────────────────────────


class TestListReports:
    @pytest.mark.parametrize(
        ("caller_fixture", "path", "expected_provider_user"),
        [
            pytest.param("user_caller", "/user/me/reports", "user-1", id="self-alias"),
            pytest.param("user_caller", "/user/user-1/reports", "user-1", id="self-id"),
            pytest.param(
                "admin_caller",
                "/user/user-1/reports",
                "user-1",
                id="admin-other",
            ),
            pytest.param(
                "admin_caller",
                "/user/me/reports",
                "admin-1",
                id="admin-self-alias",
            ),
        ],
    )
    def test_returns_page(
        self,
        request,
        report_provider: FakeReportProvider,
        invoke_user_api,
        use_caller,
        report_page: ReportPage,
        caller_fixture: str,
        path: str,
        expected_provider_user: str,
    ) -> None:
        caller = request.getfixturevalue(caller_fixture)
        use_caller(caller)
        report_provider.list_reports.result = report_page

        response = invoke_user_api(
            path,
            query_params={
                "q": "report",
                "final": "false",
                "dateFrom": "2026-01-01T00:00:00Z",
                "dateTo": "2026-01-02T00:00:00Z",
                "limit": 10,
                "cursor": "cursor-1",
            },
        )

        assert_status(response, 200)
        assert_body(
            response,
            {
                "reports": [
                    report_body(),
                ],
                "cursor": "next-cursor",
            },
        )
        assert report_provider.list_reports.calls == [
            {
                "user": expected_provider_user,
                "q": "report",
                "final": False,
                "date_from": datetime(2026, 1, 1, tzinfo=UTC),
                "date_to": datetime(2026, 1, 2, tzinfo=UTC),
                "limit": 10,
                "cursor": "cursor-1",
            }
        ]

    def test_passes_normalized_query_to_provider(
        self,
        report_provider: FakeReportProvider,
        invoke_user_api,
        user_caller: Caller,
        use_caller,
    ) -> None:
        use_caller(user_caller)
        report_provider.list_reports.result = ReportPage(reports=[], cursor=None)

        response = invoke_user_api(
            "/user/me/reports",
            query_params={"q": '  Report "One"  '},
        )

        assert_status(response, 200)
        assert report_provider.list_reports.calls == [
            {
                "user": "user-1",
                "q": 'Report \\"One\\"',
                "final": None,
                "date_from": None,
                "date_to": None,
                "limit": None,
                "cursor": None,
            }
        ]

    @pytest.mark.parametrize(
        "query_params",
        [
            pytest.param({"final": "not-a-bool"}, id="invalid-final"),
            pytest.param({"dateFrom": "not-a-date"}, id="invalid-date-from"),
            pytest.param({"dateTo": "not-a-date"}, id="invalid-date-to"),
            pytest.param({"limit": 0}, id="limit-too-small"),
            pytest.param({"limit": 101}, id="limit-too-large"),
            pytest.param(
                {
                    "dateFrom": "2026-01-02T00:00:00Z",
                    "dateTo": "2026-01-01T00:00:00Z",
                },
                id="backwards-date-range",
            ),
        ],
    )
    def test_rejects_invalid_query_params(
        self,
        invoke_user_api,
        user_caller: Caller,
        use_caller,
        query_params: dict[str, Any],
    ) -> None:
        use_caller(user_caller)

        response = invoke_user_api(
            "/user/me/reports",
            query_params=query_params,
        )

        assert_status(response, 422)

    def test_requires_authentication(
        self,
        report_provider: FakeReportProvider,
        invoke_user_api,
        use_unauthorized_caller,
    ) -> None:
        use_unauthorized_caller()

        response = invoke_user_api("/user/me/reports")

        assert_problem(response, status=401, title="Unauthorized")
        assert report_provider.list_reports.calls == []

    def test_forbids_user_reading_other_users_reports(
        self,
        report_provider: FakeReportProvider,
        invoke_user_api,
        user_caller: Caller,
        use_caller,
    ) -> None:
        use_caller(user_caller)

        response = invoke_user_api("/user/other-user/reports")

        assert_problem(response, status=403, title="Forbidden")
        assert report_provider.list_reports.calls == []

    @pytest.mark.parametrize(
        ("provider_error", "expected_status", "expected_title"),
        PROVIDER_ERRORS_WITH_NOT_FOUND,
    )
    def test_maps_provider_errors(
        self,
        report_provider: FakeReportProvider,
        invoke_user_api,
        admin_caller: Caller,
        use_caller,
        provider_error: Exception,
        expected_status: int,
        expected_title: str,
    ) -> None:
        use_caller(admin_caller)
        report_provider.list_reports.error = provider_error

        response = invoke_user_api("/user/user-1/reports")

        assert_problem(
            response,
            status=expected_status,
            title=expected_title,
        )


# ──── Routing ────────────────────────────────────────────────────────────────────────


class TestRouting:
    @pytest.mark.parametrize(
        ("method", "path"),
        [
            pytest.param("POST", "/user", id="list-users"),
            pytest.param("POST", "/user/me", id="get-user"),
            pytest.param("DELETE", "/user/me", id="update-user"),
            pytest.param("POST", "/user/me/reports", id="list-reports"),
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
            apigw_event("/user/me/unknown", {}, method="GET"),
            lambda_context,
        )

        assert_status(response, 404)
