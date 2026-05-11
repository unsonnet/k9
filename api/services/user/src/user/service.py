from datetime import datetime

from shared.abc import ApiModel, BaseService, public_api
from shared.errors import DomainForbidden
from shared.http import Caller

from .providers.report import Report, ReportPage, ReportProvider
from .providers.user import User, UserPage, UserProvider

__all__ = [
    "UserRequest",
    "UserResponse",
    "UserService",
]


# ──── Request Payloads ────────────────────────────────────────────────────────────────


class UserRequest:
    class ListUsers(ApiModel, frozen=True):
        q: str | None = None
        limit: int | None = None
        cursor: str | None = None

    class GetUser(ApiModel, frozen=True):
        id: str

    class UpdateUser(ApiModel, frozen=True):
        class Update(User.Update): ...

        id: str
        update: Update

    class ListReports(ApiModel, frozen=True):
        user: str
        q: str | None = None
        final: str | None = None
        dateFrom: str | None = None
        dateTo: str | None = None
        limit: int | None = None
        cursor: str | None = None


# ──── Response Payloads ───────────────────────────────────────────────────────────────


class UserResponse:
    class User(ApiModel, frozen=True):
        id: str
        name: str
        role: User.Role
        enabled: bool
        createdAt: datetime
        updatedAt: datetime | None = None
        lastLoginAt: datetime | None = None

        @classmethod
        def from_provider(cls, user: User):
            return cls(
                id=user.id,
                name=user.name,
                role=user.role,
                enabled=user.enabled,
                createdAt=user.created_at,
                updatedAt=user.updated_at,
                lastLoginAt=user.last_login_at,
            )

    class UserPage(ApiModel, frozen=True):
        users: list["UserResponse.User"]
        cursor: str | None = None

        @classmethod
        def from_provider(cls, page: UserPage):
            return cls(
                users=[UserResponse.User.from_provider(user) for user in page.users],
                cursor=page.cursor,
            )

    class Report(ApiModel, frozen=True):
        id: str
        user: str
        title: str
        final: bool
        createdAt: datetime | None = None
        updatedAt: datetime | None = None

        @classmethod
        def from_provider(cls, report: Report):
            return cls(
                id=report.id,
                user=report.user,
                title=report.title,
                final=report.final,
                createdAt=report.created_at,
                updatedAt=report.updated_at,
            )

    class ReportPage(ApiModel, frozen=True):
        reports: list["UserResponse.Report"]
        cursor: str | None = None

        @classmethod
        def from_provider(cls, page: ReportPage):
            return cls(
                reports=[
                    UserResponse.Report.from_provider(report) for report in page.reports
                ],
                cursor=page.cursor,
            )


# ──── User Service ───────────────────────────────────────────────────────────────────


class UserService(BaseService):
    users: UserProvider
    reports: ReportProvider

    def __init__(
        self,
        users: UserProvider,
        reports: ReportProvider,
    ) -> None:
        self.users = users
        self.reports = reports

    # ──── Public APIs ────

    @public_api(require_admin=True)
    def list_users(
        self,
        caller: Caller,
        request: UserRequest.ListUsers,
    ) -> UserResponse.UserPage:
        return UserResponse.UserPage.from_provider(
            self.users.list_users(
                q=request.q,
                limit=request.limit,
                cursor=request.cursor,
            )
        )

    @public_api.dispatch_by_role
    def get_user(
        self,
        caller: Caller,
        request: UserRequest.GetUser,
    ) -> UserResponse.User: ...

    @get_user.admin
    def _(
        self,
        caller: Caller,
        request: UserRequest.GetUser,
    ) -> UserResponse.User:
        id = caller.id if request.id == "me" else request.id
        return UserResponse.User.from_provider(self.users.get_user(id=id))

    @get_user.user
    def _(
        self,
        caller: Caller,
        request: UserRequest.GetUser,
    ) -> UserResponse.User:
        if request.id not in ["me", caller.id]:
            raise DomainForbidden("Cannot read another user's profile")
        return UserResponse.User.from_provider(self.users.get_user(id=caller.id))

    @public_api.dispatch_by_role
    def update_user(
        self,
        caller: Caller,
        request: UserRequest.UpdateUser,
    ) -> UserResponse.User: ...

    @update_user.admin
    def _(
        self,
        caller: Caller,
        request: UserRequest.UpdateUser,
    ) -> UserResponse.User:
        id = caller.id if request.id == "me" else request.id
        return UserResponse.User.from_provider(
            self.users.update_user(id=id, update=request.update)
        )

    @update_user.user
    def _(
        self,
        caller: Caller,
        request: UserRequest.UpdateUser,
    ) -> UserResponse.User:
        if request.id not in ["me", caller.id]:
            raise DomainForbidden("Cannot update another user's profile")
        if "role" in request.update or "enabled" in request.update:
            raise DomainForbidden("Cannot update `role` or `enabled`")
        return UserResponse.User.from_provider(
            self.users.update_user(id=caller.id, update=request.update)
        )

    @public_api.dispatch_by_role
    def list_reports(
        self,
        caller: Caller,
        request: UserRequest.ListReports,
    ) -> UserResponse.ReportPage: ...

    @list_reports.admin
    def _(
        self,
        caller: Caller,
        request: UserRequest.ListReports,
    ) -> UserResponse.ReportPage:
        id = caller.id if request.user == "me" else request.user
        return UserResponse.ReportPage.from_provider(
            self.reports.list_reports(
                user=id,
                q=request.q,
                final=request.final,
                date_from=request.dateFrom,
                date_to=request.dateTo,
                limit=request.limit,
                cursor=request.cursor,
            )
        )

    @list_reports.user
    def _(
        self,
        caller: Caller,
        request: UserRequest.ListReports,
    ) -> UserResponse.ReportPage:
        if request.user not in ["me", caller.id]:
            raise DomainForbidden("Cannot list another user's reports")
        return UserResponse.ReportPage.from_provider(
            self.reports.list_reports(
                user=caller.id,
                q=request.q,
                final=request.final,
                date_from=request.dateFrom,
                date_to=request.dateTo,
                limit=request.limit,
                cursor=request.cursor,
            )
        )
