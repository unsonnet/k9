from typing import Annotated

from shared.errors import (
    DomainForbidden,
    DomainRateLimited,
    DomainUnauthorized,
    assert_unreachable,
)
from shared.http import Body, HttpResolver
from shared.http.errors import Forbidden, TooManyRequests, Unauthorized
from shared.http.responses import OK, Accepted, NoContent

from .service import AuthRequest, AuthResponse, AuthService

app = HttpResolver(enable_validation=True)
svc = AuthService()


@app.post(
    "/auth/login",
    summary="Authenticate user",
    description="Authenticate user with username and password.",
    tags=["auth"],
    responses={
        200: "User logged in",
        202: "Authentication challenge required",
        401: "Invalid credentials",
        403: "Access denied",
        429: "Too many requests",
    },
)
def login(
    request: Annotated[AuthRequest.Login, Body()],
) -> (
    OK[AuthResponse.Tokens]
    | Accepted[AuthResponse.Challenge]
    | Unauthorized
    | Forbidden
    | TooManyRequests
):
    try:
        match svc.login(request):
            case AuthResponse.Tokens() as tokens:
                return OK(tokens)
            case AuthResponse.Challenge() as challenge:
                return Accepted(challenge)
            case _ as never:
                assert_unreachable(never)
    except DomainUnauthorized as exc:
        return Unauthorized("Invalid credentials", cause=exc)
    except DomainForbidden as exc:
        return Forbidden(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


@app.post(
    "/auth/challenge",
    summary="Respond to auth challenge",
    description="Submit challenge response and continue authentication flow.",
    tags=["auth"],
    responses={
        200: "Authentication completed",
        202: "Further authentication challenge required",
        401: "Invalid challenge response",
        403: "Access denied",
        429: "Too many requests",
    },
)
def challenge(
    request: Annotated[AuthRequest.Challenge, Body()],
) -> (
    OK[AuthResponse.Tokens]
    | Accepted[AuthResponse.Challenge]
    | Unauthorized
    | Forbidden
    | TooManyRequests
):
    try:
        match svc.challenge(request):
            case AuthResponse.Tokens() as tokens:
                return OK(tokens)
            case AuthResponse.Challenge() as challenge:
                return Accepted(challenge)
            case _ as never:
                assert_unreachable(never)
    except DomainUnauthorized as exc:
        return Unauthorized("Invalid challenge response", cause=exc)
    except DomainForbidden as exc:
        return Forbidden(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


@app.post(
    "/auth/refresh",
    summary="Refresh tokens",
    description="Refresh access token using refresh token.",
    tags=["auth"],
    responses={
        200: "Tokens refreshed",
        401: "Invalid refresh token",
        403: "Access denied",
        429: "Too many requests",
    },
)
def refresh(
    request: Annotated[AuthRequest.Refresh, Body()],
) -> OK[AuthResponse.Tokens] | Unauthorized | Forbidden | TooManyRequests:
    try:
        match svc.refresh(request):
            case AuthResponse.Tokens() as tokens:
                return OK(tokens)
            case _ as never:
                assert_unreachable(never)
    except DomainUnauthorized as exc:
        return Unauthorized("Invalid refresh token", cause=exc)
    except DomainForbidden as exc:
        return Forbidden(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


@app.post(
    "/auth/logout",
    summary="Logout user",
    description="Logout user by invalidating their tokens.",
    tags=["auth"],
    responses={
        204: "User logged out",
        403: "Access denied",
        429: "Too many requests",
    },
)
def logout(
    request: Annotated[AuthRequest.Logout, Body()],
) -> NoContent | Forbidden | TooManyRequests:
    try:
        match svc.logout(request):
            case None:
                return NoContent()
            case _ as never:
                assert_unreachable(never)
    except DomainUnauthorized:
        return NoContent()
    except DomainForbidden as exc:
        return Forbidden(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


def lambda_handler(event, context):
    return app.resolve(event, context)
