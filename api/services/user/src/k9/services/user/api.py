from k9.resolvers.http.errors import Forbidden, NotFound, TooManyRequests, Unauthorized
from k9.resolvers.http.responses import OK, Created, NoContent
from k9.types.common import Caller, Password, UserID, is_set
from k9.types.errors import (
    DomainForbidden,
    DomainNotFound,
    DomainRateLimited,
    DomainUnauthorized,
)

from . import app
from .http import Create, Delete, List, Read, Reset, Update, Upload
from .provider import Credentials, Page, UploadForm, User, UserProvider

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
    request: List,
) -> OK[Page] | Unauthorized | TooManyRequests:
    try:
        page = provider.list_users(
            limit=request.limit,
            cursor=request.cursor,
        )
        return OK(page)
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
    request: Create,
) -> Created[Credentials] | Unauthorized | Forbidden | TooManyRequests:
    try:
        caller.require_admin()
        creds = provider.create_user(
            id=UserID.random(),
            role=request.role,
            name=request.name,
            password=Password.random(),
            enabled=request.enabled,
        )
        return Created(creds)
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
    request: Read,
) -> OK[User] | Unauthorized | Forbidden | NotFound | TooManyRequests:
    try:
        user_id = caller.resolve(request.id)
        user = provider.read_user(
            id=user_id,
        )
        return OK(user)
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
    request: Update,
) -> OK[User] | Unauthorized | Forbidden | NotFound | TooManyRequests:
    try:
        user_id = caller.resolve(request.id)
        if user_id == caller.id and (is_set(request.role) or is_set(request.enabled)):
            raise DomainForbidden("Cannot update own `role` or `enabled` status")
        user = provider.update_user(
            id=user_id,
            role=request.role,
            name=request.name,
            picture=request.picture,
            enabled=request.enabled,
        )
        return OK(user)
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
    request: Delete,
) -> NoContent | Unauthorized | Forbidden | TooManyRequests:
    try:
        caller.require_admin()
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
    request: Upload,
) -> OK[UploadForm] | Unauthorized | Forbidden | NotFound | TooManyRequests:
    try:
        user_id = caller.resolve(request.id)
        form = provider.upload_picture(
            id=user_id,
            format=request.format,
            length=request.length,
        )
        return OK(form)
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
    request: Reset,
) -> OK[Credentials] | Unauthorized | Forbidden | NotFound | TooManyRequests:
    try:
        user_id = caller.resolve(request.id)
        creds = provider.reset_user(
            id=user_id,
            password=Password.random(),
        )
        return OK(creds)
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainForbidden as exc:
        return Forbidden(cause=exc)
    except DomainNotFound as exc:
        return NotFound(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)
