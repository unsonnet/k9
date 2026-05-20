from shared.errors import (
    DomainForbidden,
    DomainNotFound,
    DomainRateLimited,
    DomainUnauthorized,
)
from shared.http import HttpResolver
from shared.http.errors import Forbidden, NotFound, TooManyRequests, Unauthorized
from shared.http.responses import OK, Created, NoContent

from .payloads import Request, Response
from .provider import CognitoUserProvider as UserProvider
from .service import UserService

app = HttpResolver(enable_validation=True)
svc = UserService(UserProvider())


@app.get(
    "/user",
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
) -> OK[Response.UserPage] | Unauthorized | Forbidden | TooManyRequests:
    try:
        return OK(svc.list(app.caller(), request))
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainForbidden as exc:
        return Forbidden(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


@app.post(
    "/user",
    summary="Create user",
    description="Create a new user. Requires admin role.",
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
) -> Created[Response.UserCreds] | Unauthorized | Forbidden | TooManyRequests:
    try:
        return Created(svc.create(app.caller(), request))
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainForbidden as exc:
        return Forbidden(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


@app.get(
    "/user/<userId>",
    summary="Read user profile",
    description=(
        "Read a user profile. The special userId value 'me' resolves to the "
        "authenticated caller. Reading another user's profile requires admin role."
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
) -> OK[Response.User] | Unauthorized | Forbidden | NotFound | TooManyRequests:
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
    "/user/<userId>",
    summary="Update user profile",
    description=(
        "Update a user profile. The special userId value 'me' resolves to the "
        "authenticated caller. Updating another user's profile requires admin role."
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
) -> OK[Response.User] | Unauthorized | Forbidden | NotFound | TooManyRequests:
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
    "/user/<userId>",
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
    "/user/<userId>/reset",
    summary="Reset user credentials",
    description=(
        "Reset user credentials. Requires admin role. Resets the user's password "
        "and MFA enrollment state, when present, and returns a new temporary password."
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
) -> OK[Response.UserCreds] | Unauthorized | Forbidden | NotFound | TooManyRequests:
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
