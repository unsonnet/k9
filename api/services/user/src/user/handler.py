from shared.errors import (
    DomainForbidden,
    DomainNotFound,
    DomainRateLimited,
    DomainUnauthorized,
)
from shared.http import HttpResolver
from shared.http.errors import Forbidden, NotFound, TooManyRequests, Unauthorized
from shared.http.responses import OK, Created, NoContent

from .models import Request, Response
from .provider import CognitoUserProvider as UserProvider
from .service import UserService

app = HttpResolver(strip_prefixes=["/user"], enable_validation=True)
svc = UserService(UserProvider())


@app.get(
    "/",
    summary="List users",
    description="List or search users. Requires admin role.",
    tags=["user"],
    responses={
        200: "Users found",
        401: "Authentication required",
        403: "Access denied",
        429: "Too many requests",
    },
)
def list(
    request: Request.List,
) -> OK[Response.Page] | Unauthorized | Forbidden | TooManyRequests:
    try:
        return OK(svc.list(app.caller(), request))
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainForbidden as exc:
        return Forbidden(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


@app.post(
    "/",
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
    request: Request.Create,
) -> Created[Response.Credentials] | Unauthorized | Forbidden | TooManyRequests:
    try:
        return Created(svc.create(app.caller(), request))
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainForbidden as exc:
        return Forbidden(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


@app.get(
    "/<userId>",
    summary="Read user profile",
    description=(
        "Read a user profile. "
        "Reading another user's profile requires admin role. "
        "The special userId value 'me' resolves to the authenticated caller."
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
    request: Request.Read,
) -> OK[Response.Profile] | Unauthorized | Forbidden | NotFound | TooManyRequests:
    try:
        return OK(svc.read(app.caller(), request))
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainForbidden as exc:
        return Forbidden(cause=exc)
    except DomainNotFound as exc:
        return NotFound(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


@app.patch(
    "/<userId>",
    summary="Update user profile",
    description=(
        "Update a user profile. "
        "Updating another user's profile requires admin role. "
        "The special userId value 'me' resolves to the authenticated caller. "
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
    request: Request.Update,
) -> OK[Response.Profile] | Unauthorized | Forbidden | NotFound | TooManyRequests:
    try:
        return OK(svc.update(app.caller(), request))
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainForbidden as exc:
        return Forbidden(cause=exc)
    except DomainNotFound as exc:
        return NotFound(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


@app.delete(
    "/<userId>",
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
    request: Request.Delete,
) -> NoContent | Unauthorized | Forbidden | TooManyRequests:
    try:
        return NoContent(svc.delete(app.caller(), request))
    except DomainNotFound:
        return NoContent()
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainForbidden as exc:
        return Forbidden(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


@app.post(
    "/<userId>/picture",
    summary="Create user picture upload form",
    description=(
        "Create a user picture upload form. "
        "Uploading another user's picture requires admin role. "
        "The special userId value 'me' resolves to the authenticated caller."
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
    request: Request.Picture,
) -> OK[Response.UploadForm] | Unauthorized | Forbidden | NotFound | TooManyRequests:
    try:
        return OK(svc.picture(app.caller(), request))
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainForbidden as exc:
        return Forbidden(cause=exc)
    except DomainNotFound as exc:
        return NotFound(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


@app.post(
    "/<userId>/reset",
    summary="Reset user credentials",
    description=(
        "Reset a user's password and disable their MFA device. "
        "Requires admin role. "
        "The special userId value 'me' resolves to the authenticated caller. "
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
    request: Request.Reset,
) -> OK[Response.Credentials] | Unauthorized | Forbidden | NotFound | TooManyRequests:
    try:
        return OK(svc.reset(app.caller(), request))
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
