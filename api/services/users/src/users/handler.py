from shared.config import is_set
from shared.errors import (
    DomainForbidden,
    DomainNotFound,
    DomainRateLimited,
    DomainUnauthorized,
)
from shared.helpers import (
    generate_id,
    generate_password,
    require_admin,
    require_admin_or_self,
)
from shared.http import Caller, HttpResolver
from shared.http.errors import Forbidden, NotFound, TooManyRequests, Unauthorized
from shared.http.responses import OK, Created, NoContent

from .models import Request, Response
from .provider import UserProvider

app = HttpResolver(enable_validation=True)
provider = UserProvider()
app.grant(*provider.permissions)


@app.get(
    "/users",
    summary="List users",
    description="List or search users.",
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
        return OK(Response.Page.pack(page))
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


@app.post(
    "/users",
    summary="Create user profile",
    description="Create a new user profile. Requires admin role.",
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
            id=generate_id(),
            name=request.name,
            password=generate_password(),
            role=request.role,
            enabled=request.enabled,
        )
        return Created(Response.Credentials.pack(creds))
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainForbidden as exc:
        return Forbidden(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


@app.get(
    "/users/<id>",
    summary="Read user profile",
    description=(
        "Read a user profile. "
        "Reading another user's profile requires admin role. "
        "The special id value 'me' resolves to the authenticated caller."
    ),
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
        return OK(Response.User.pack(user))
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
    summary="Update user profile",
    description=(
        "Update a user profile. "
        "Updating another user's profile requires admin role. "
        "The special id value 'me' resolves to the authenticated caller."
    ),
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
        if caller.id == user_id:
            if is_set(request.role) or is_set(request.enabled):
                raise DomainForbidden("Cannot update own `role` or `enabled` status")
        user = provider.update_user(
            id=user_id,
            name=request.name,
            picture=request.picture,
            role=request.role,
            enabled=request.enabled,
        )
        return OK(Response.User.pack(user))
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
    summary="Delete user profile",
    description="Delete a user profile other than self. Requires admin role.",
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
    summary="Create user picture upload form",
    description=(
        "Create a user picture upload form. "
        "Uploading another user's picture requires admin role. "
        "The special id value 'me' resolves to the authenticated caller."
    ),
    tags=["user"],
    responses={
        200: "User picture upload form created",
        401: "Authentication required",
        403: "Access denied",
        404: "User not found",
        429: "Too many requests",
    },
)
def picture(
    caller: Caller,
    request: Request.Picture,
) -> OK[Response.UploadURL] | Unauthorized | Forbidden | NotFound | TooManyRequests:
    try:
        user_id = require_admin_or_self(caller, request.id)
        form = provider.upload_picture(
            id=user_id,
            content_type=request.contentType,
            max_bytes=5 * 1024 * 1024,
            max_seconds=5 * 60,
        )
        return OK(Response.UploadURL.pack(form))
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
    summary="Reset user credentials",
    description=(
        "Reset a user's password and disable their MFA device. "
        "Resetting another user's credentials requires admin role. "
        "The special id value 'me' resolves to the authenticated caller."
    ),
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
            password=generate_password(),
        )
        return OK(Response.Credentials.pack(creds))
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainForbidden as exc:
        return Forbidden(cause=exc)
    except DomainNotFound as exc:
        return NotFound(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


def lambda_handler(event, context):
    return app.resolve(event, context)
