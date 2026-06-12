from typing import Final

from shared.abc import BaseService, Caller, public_api
from shared.errors import DomainForbidden
from shared.providers.cognito import generate_id, generate_password

from .models import Request, Response
from .provider import UserProvider

__all__ = [
    "UserService",
]

PICTURE_MAX_SIZE: Final = 5 * 1024 * 1024
PICTURE_EXPIRES_IN: Final = 5 * 60

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
        return Response.Page.from_provider(
            self.provider.list_users(
                q=request.q,
                limit=request.limit or 25,
                cursor=request.cursor,
            )
        )

    @public_api(require_admin=True)
    def create(
        self,
        caller: Caller,
        request: Request.Create,
    ) -> Response.Credentials:
        return Response.Credentials.from_provider(
            self.provider.create_user(
                id=generate_id(),
                name=request.name,
                password=generate_password(),
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
        return Response.Profile.from_provider(
            self.provider.read_user(
                id=request.id if request.id != "me" else caller.id,
            )
        )

    @public_api(require_owner=True)
    def update(
        self,
        caller: Caller,
        request: Request.Update,
    ) -> Response.Profile:
        if not caller.is_admin or request.id in ["me", caller.id]:
            if request.role is not None or request.enabled is not None:
                raise DomainForbidden("Cannot update own `role` or `enabled` status")
        return Response.Profile.from_provider(
            self.provider.update_user(
                id=request.id if request.id != "me" else caller.id,
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
        if request.id == caller.id:
            raise DomainForbidden("Cannot delete own user profile")
        return self.provider.delete_user(
            id=request.id,
        )

    @public_api(require_owner=True)
    def picture(
        self,
        caller: Caller,
        request: Request.Picture,
    ) -> Response.UploadForm:
        return Response.UploadForm.from_provider(
            self.provider.generate_upload_form(
                id=request.id if request.id != "me" else caller.id,
                content_type=request.contentType,
                max_bytes=PICTURE_MAX_SIZE,
                max_seconds=PICTURE_EXPIRES_IN,
            )
        )

    @public_api(require_admin=True)
    def reset(
        self,
        caller: Caller,
        request: Request.Reset,
    ) -> Response.Credentials:
        return Response.Credentials.from_provider(
            self.provider.reset_user(
                id=request.id if request.id != "me" else caller.id,
                password=generate_password(),
            )
        )
