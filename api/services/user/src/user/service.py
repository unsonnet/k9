from shared.abc import BaseService, public_api
from shared.errors import DomainForbidden
from shared.http import Caller

from .payloads import Request, Response
from .providers.report import ReportProvider
from .providers.user import UserProvider

__all__ = [
    "UserService",
]


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
        request: Request.ListUsers,
    ) -> Response.UserPage:
        return Response.UserPage.from_(
            self.users.list_users(
                q=request.q,
                limit=request.limit,
                cursor=request.cursor,
            )
        )

    @public_api(require_admin=True)
    def create_user(
        self,
        caller: Caller,
        request: Request.CreateUser,
    ) -> Response.User:
        return Response.User.from_(
            self.users.create_user(
                name=request.name,
                role=request.role,
            )
        )

    @public_api(require_owner=True)
    def get_user(
        self,
        caller: Caller,
        request: Request.GetUser,
    ) -> Response.User:
        id = request.userId if caller.is_admin and request.userId != "me" else caller.id
        return Response.User.from_(
            self.users.get_user(
                id=id,
            )
        )

    @public_api(require_owner=True)
    def update_user(
        self,
        caller: Caller,
        request: Request.UpdateUser,
    ) -> Response.User:
        if not caller.is_admin:
            if request.role is not None or request.enabled is not None:
                raise DomainForbidden("Cannot update `role` or `enabled`")
        id = request.userId if caller.is_admin and request.userId != "me" else caller.id
        return Response.User.from_(
            self.users.update_user(
                id=id,
                name=request.name,
                role=request.role,
                enabled=request.enabled,
            )
        )

    @public_api(require_admin=True)
    def reset_user(
        self,
        caller: Caller,
        request: Request.ResetUser,
    ) -> Response.UserCreds:
        return Response.UserCreds.from_(
            self.users.reset_user(
                id=request.userId,
            )
        )

    @public_api(require_owner=True)
    def list_reports(
        self,
        caller: Caller,
        request: Request.ListReports,
    ) -> Response.ReportPage:
        id = request.userId if caller.is_admin and request.userId != "me" else caller.id
        return Response.ReportPage.from_(
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
