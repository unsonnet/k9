from shared.abc import BaseService, Caller, public_api
from shared.errors import DomainForbidden

from .payloads import Request, Response
from .provider import UserProvider

__all__ = [
    "UserService",
]


# ──── User Service ───────────────────────────────────────────────────────────────────


class UserService(BaseService):
    provider: UserProvider

    def __init__(self, provider: UserProvider) -> None:
        self.provider = provider

    # ──── Public APIs ────

    @public_api(require_admin=True)
    def list(
        self,
        caller: Caller,
        request: Request.List,
    ) -> Response.Page:
        return Response.Page.from_(
            self.provider.list_users(
                q=request.q,
                limit=request.limit,
                cursor=request.cursor,
            )
        )

    @public_api(require_admin=True)
    def create(
        self,
        caller: Caller,
        request: Request.Create,
    ) -> Response.Credentials:
        return Response.Credentials.from_(
            self.provider.create_user(
                name=request.name,
                role=request.role,
                enabled=request.enabled,
            )
        )

    @public_api(require_owner=True)
    def read(
        self,
        caller: Caller,
        request: Request.Read,
    ) -> Response.Profile:
        id = request.userId if caller.is_admin and request.userId != "me" else caller.id
        return Response.Profile.from_(
            self.provider.read_user(
                id=id,
            )
        )

    @public_api(require_owner=True)
    def update(
        self,
        caller: Caller,
        request: Request.Update,
    ) -> Response.Profile:
        if not caller.is_admin:
            if request.role is not None or request.enabled is not None:
                raise DomainForbidden("Cannot update `role` or `enabled`")
        id = request.userId if caller.is_admin and request.userId != "me" else caller.id
        return Response.Profile.from_(
            self.provider.update_user(
                id=id,
                name=request.name,
                role=request.role,
                enabled=request.enabled,
            )
        )

    @public_api(require_admin=True)
    def delete(
        self,
        caller: Caller,
        request: Request.Delete,
    ) -> None:
        if request.userId == "me" or request.userId == caller.id:
            raise DomainForbidden("Cannot delete own user profile")
        return self.provider.delete_user(
            id=request.userId,
        )

    @public_api(require_admin=True)
    def reset(
        self,
        caller: Caller,
        request: Request.Reset,
    ) -> Response.Credentials:
        return Response.Credentials.from_(
            self.provider.reset_user(
                id=request.userId,
            )
        )
