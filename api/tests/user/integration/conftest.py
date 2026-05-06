import importlib
from datetime import datetime, timezone
from typing import Any

import pytest
from user.providers.report import Report, ReportPage
from user.providers.user import User, UserPage

TEST_NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


def make_user(
    *,
    id: str = "user-1",
    name: str = "Alice",
    role: User.Role = User.Role.USER,
    status: User.Status = User.Status.ACTIVE,
) -> User:
    return User(
        id=id,
        name=name,
        role=role,
        status=status,
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


class DummyUserProvider:
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


class DummyReportProvider:
    def __init__(self) -> None:
        self.list_result: ReportPage | None = None
        self.list_error: Exception | None = None

        self.list_calls: list[dict[str, Any]] = []

    def list_reports(
        self,
        *,
        user: str,
        q: str | None = None,
        final: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
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


@pytest.fixture
def dummy_user_provider() -> DummyUserProvider:
    return DummyUserProvider()


@pytest.fixture
def dummy_report_provider() -> DummyReportProvider:
    return DummyReportProvider()


@pytest.fixture
def user_handler_module(
    monkeypatch: pytest.MonkeyPatch,
    dummy_user_provider: DummyUserProvider,
    dummy_report_provider: DummyReportProvider,
):
    import user.providers.report as report_provider_module
    import user.providers.user as user_provider_module

    monkeypatch.setattr(
        user_provider_module,
        "UserProvider",
        lambda: dummy_user_provider,
    )
    monkeypatch.setattr(
        report_provider_module,
        "ReportProvider",
        lambda: dummy_report_provider,
    )

    import user.handler as handler

    return importlib.reload(handler)
