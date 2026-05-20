from shared.errors import DomainForbidden, DomainRateLimited, DomainUnauthorized
from shared.http import HttpResolver
from shared.http.errors import Forbidden, TooManyRequests, Unauthorized
from shared.http.responses import OK, Accepted, NoContent

from .payloads import Request, Response
from .providers.auth import CognitoAuthProvider as AuthProvider
from .service import AuthService

app = HttpResolver(enable_validation=True)
svc = AuthService(AuthProvider())


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
    request: Request.Login,
) -> (
    OK[Response.Tokens]
    | Accepted[Response.Challenge]
    | Unauthorized
    | Forbidden
    | TooManyRequests
):
    try:
        match svc.login(request):
            case Response.Tokens() as tokens:
                return OK(tokens)
            case Response.Challenge() as challenge:
                return Accepted(challenge)
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
    request: Request.Challenge,
) -> (
    OK[Response.Tokens]
    | Accepted[Response.Challenge]
    | Unauthorized
    | Forbidden
    | TooManyRequests
):
    try:
        match svc.challenge(request):
            case Response.Tokens() as tokens:
                return OK(tokens)
            case Response.Challenge() as challenge:
                return Accepted(challenge)
    except DomainUnauthorized as exc:
        return Unauthorized("Invalid challenge response", cause=exc)
    except DomainForbidden as exc:
        return Forbidden(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


@app.post(
    "/auth/mfa/setup",
    summary="Start MFA enrollment",
    description="Start TOTP MFA enrollment for the authenticated user.",
    tags=["auth"],
    responses={
        200: "MFA setup started",
        401: "Authentication required",
        403: "Access denied",
        429: "Too many requests",
    },
)
def setup() -> OK[Response.MFA] | Unauthorized | Forbidden | TooManyRequests:
    try:
        return OK(svc.setup(app.caller()))
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainForbidden as exc:
        return Forbidden(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


@app.post(
    "/auth/mfa/verify",
    summary="Verify MFA enrollment",
    description="Verify TOTP MFA code and enable MFA for the authenticated user.",
    tags=["auth"],
    responses={
        204: "MFA enabled",
        401: "Invalid MFA code",
        403: "Access denied",
        429: "Too many requests",
    },
)
def verify(
    request: Request.Verify,
) -> NoContent | Unauthorized | Forbidden | TooManyRequests:
    try:
        return NoContent(svc.verify(app.caller(), request))
    except DomainUnauthorized as exc:
        return Unauthorized("Invalid MFA code", cause=exc)
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
    request: Request.Refresh,
) -> OK[Response.Tokens] | Unauthorized | Forbidden | TooManyRequests:
    try:
        return OK(svc.refresh(request))
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
    request: Request.Logout,
) -> NoContent | Forbidden | TooManyRequests:
    try:
        return NoContent(svc.logout(request))
    except DomainUnauthorized:
        return NoContent()
    except DomainForbidden as exc:
        return Forbidden(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


def lambda_handler(event, context):
    return app.resolve(event, context)
