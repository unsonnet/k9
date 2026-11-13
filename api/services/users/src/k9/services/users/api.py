from k9.resolvers.http.errors import Forbidden, NotFound, TooManyRequests, Unauthorized
from k9.resolvers.http.responses import OK, Created, NoContent
from k9.shared.config import is_set
from k9.shared.errors import (
    DomainForbidden,
    DomainNotFound,
    DomainRateLimited,
    DomainUnauthorized,
)
from k9.shared.helpers import require_admin, require_admin_or_self
from k9.types.common import Caller, Password, UserID

from . import app
from .http import Request, Response
from .provider import UserProvider

provider = UserProvider()
app.grant(*provider.permissions)


@app.get(
    "/users",
    summary="List users",
    tags=["user"],
    responses={
        200: "Users found",
        401: "Authentication required",
        429: "Too many requests",
    },
)
def list(
    caller: Caller,
    request: Request.List,
) -> OK[Response.Page] | Unauthorized | TooManyRequests:
    try:
        page = provider.list_users(
            limit=request.limit,
            cursor=request.cursor,
        )
        return OK(Response.Page.model_validate(page))
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


@app.post(
    "/users",
    summary="Create user",
    tags=["user"],
    responses={
        201: "User created",
        401: "Authentication required",
        403: "Access denied",
        429: "Too many requests",
    },
)
def create(
    caller: Caller,
    request: Request.Create,
) -> Created[Response.Credentials] | Unauthorized | Forbidden | TooManyRequests:
    try:
        require_admin(caller)
        creds = provider.create_user(
            id=UserID.random(),
            role=request.role,
            name=request.name,
            password=Password.random(),
            enabled=request.enabled,
        )
        return Created(Response.Credentials.model_validate(creds))
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainForbidden as exc:
        return Forbidden(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


@app.get(
    "/users/<id>",
    summary="Read user",
    tags=["user"],
    responses={
        200: "User found",
        401: "Authentication required",
        403: "Access denied",
        404: "User not found",
        429: "Too many requests",
    },
)
def read(
    caller: Caller,
    request: Request.Read,
) -> OK[Response.User] | Unauthorized | Forbidden | NotFound | TooManyRequests:
    try:
        user_id = require_admin_or_self(caller, request.id)
        user = provider.read_user(
            id=user_id,
        )
        return OK(Response.User.model_validate(user))
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainForbidden as exc:
        return Forbidden(cause=exc)
    except DomainNotFound as exc:
        return NotFound(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


@app.patch(
    "/users/<id>",
    summary="Update user",
    tags=["user"],
    responses={
        200: "User updated",
        401: "Authentication required",
        403: "Access denied",
        404: "User not found",
        429: "Too many requests",
    },
)
def update(
    caller: Caller,
    request: Request.Update,
) -> OK[Response.User] | Unauthorized | Forbidden | NotFound | TooManyRequests:
    try:
        user_id = require_admin_or_self(caller, request.id)
        if user_id == caller.id and (is_set(request.role) or is_set(request.enabled)):
            raise DomainForbidden("Cannot update own `role` or `enabled` status")
        user = provider.update_user(
            id=user_id,
            role=request.role,
            name=request.name,
            picture=request.picture,
            enabled=request.enabled,
        )
        return OK(Response.User.model_validate(user))
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainForbidden as exc:
        return Forbidden(cause=exc)
    except DomainNotFound as exc:
        return NotFound(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


@app.delete(
    "/users/<id>",
    summary="Delete user",
    tags=["user"],
    responses={
        204: "User deleted",
        401: "Authentication required",
        403: "Access denied",
        429: "Too many requests",
    },
)
def delete(
    caller: Caller,
    request: Request.Delete,
) -> NoContent | Unauthorized | Forbidden | TooManyRequests:
    try:
        require_admin(caller)
        if request.id == caller.id:
            raise DomainForbidden("Cannot delete own user profile")
        provider.delete_user(
            id=request.id,
        )
        return NoContent()
    except DomainNotFound:
        return NoContent()
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainForbidden as exc:
        return Forbidden(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


@app.post(
    "/users/<id>/picture",
    summary="Upload user picture",
    tags=["user"],
    responses={
        200: "User picture upload form created",
        401: "Authentication required",
        403: "Access denied",
        404: "User not found",
        429: "Too many requests",
    },
)
def upload(
    caller: Caller,
    request: Request.Picture,
) -> OK[Response.Upload] | Unauthorized | Forbidden | NotFound | TooManyRequests:
    try:
        user_id = require_admin_or_self(caller, request.id)
        form = provider.upload_picture(
            id=user_id,
            format=request.format,
            length=request.length,
        )
        return OK(Response.Upload.model_validate(form))
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainForbidden as exc:
        return Forbidden(cause=exc)
    except DomainNotFound as exc:
        return NotFound(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


@app.post(
    "/users/<id>/reset",
    summary="Reset user",
    tags=["user"],
    responses={
        200: "User credentials reset",
        401: "Authentication required",
        403: "Access denied",
        404: "User not found",
        429: "Too many requests",
    },
)
def reset(
    caller: Caller,
    request: Request.Reset,
) -> OK[Response.Credentials] | Unauthorized | Forbidden | NotFound | TooManyRequests:
    try:
        user_id = require_admin_or_self(caller, request.id)
        creds = provider.reset_user(
            id=user_id,
            password=Password.random(),
        )
        return OK(Response.Credentials.model_validate(creds))
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainForbidden as exc:
        return Forbidden(cause=exc)
    except DomainNotFound as exc:
        return NotFound(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)
