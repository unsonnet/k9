from shared.errors import DomainForbidden, DomainRateLimited, DomainUnauthorized
from shared.helpers import require_admin_or_self
from shared.http import Caller, HttpResolver
from shared.http.errors import Forbidden, TooManyRequests, Unauthorized
from shared.http.responses import OK, Accepted, NoContent

from .models import Request, Response
from .provider import AuthProvider, Challenge, Tokens

app = HttpResolver(enable_validation=True)
provider = AuthProvider()
app.grant(*provider.permissions)


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
        match provider.authenticate(
            name=request.name,
            password=request.password,
        ):
            case Tokens() as tokens:
                return OK(Response.Tokens.pack(tokens))
            case Challenge() as challenge:
                return Accepted(Response.Challenge.pack(challenge))
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
        match provider.respond_to_challenge(
            session=request.session,
            challenge=request.challenge,
            response=request.response,
        ):
            case Tokens() as tokens:
                return OK(Response.Tokens.pack(tokens))
            case Challenge() as challenge:
                return Accepted(Response.Challenge.pack(challenge))
    except DomainUnauthorized as exc:
        return Unauthorized("Invalid challenge response", cause=exc)
    except DomainForbidden as exc:
        return Forbidden(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


@app.post(
    "/auth/mfa/setup",
    summary="Start MFA enrollment",
    description="Start TOTP MFA enrollment for the authenticated caller.",
    tags=["auth"],
    responses={
        200: "MFA setup started",
        401: "Authentication required",
        403: "Access denied",
        429: "Too many requests",
    },
)
def setup(
    caller: Caller,
) -> OK[Response.MFA] | Unauthorized | Forbidden | TooManyRequests:
    try:
        mfa = provider.setup_mfa(
            access_token=caller.token,
            name=caller.name,
        )
        return OK(Response.MFA.pack(mfa))
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainForbidden as exc:
        return Forbidden(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


@app.post(
    "/auth/mfa/verify",
    summary="Verify MFA enrollment",
    description="Verify TOTP MFA code and enable MFA for the authenticated caller.",
    tags=["auth"],
    responses={
        204: "MFA enabled",
        401: "Invalid MFA code",
        403: "Access denied",
        429: "Too many requests",
    },
)
def verify(
    caller: Caller,
    request: Request.Verify,
) -> NoContent | Unauthorized | Forbidden | TooManyRequests:
    try:
        provider.verify_mfa(
            access_token=caller.token,
            code=request.code,
        )
        return NoContent()
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
        tokens = provider.refresh_tokens(
            refresh_token=request.refreshToken,
        )
        return OK(Response.Tokens.pack(tokens))
    except DomainUnauthorized as exc:
        return Unauthorized("Invalid refresh token", cause=exc)
    except DomainForbidden as exc:
        return Forbidden(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


@app.post(
    "/auth/logout/<id>",
    summary="Logout user",
    description=(
        "Logout user by invalidating their tokens. "
        "Logging out another user requires admin role. "
        "The special id value 'me' resolves to the authenticated caller."
    ),
    tags=["auth"],
    responses={
        204: "User logged out",
        403: "Access denied",
        429: "Too many requests",
    },
)
def logout(
    caller: Caller,
    request: Request.Logout,
) -> NoContent | Forbidden | TooManyRequests:
    try:
        user_id = require_admin_or_self(caller, request.id)
        provider.revoke_tokens(
            id=user_id,
        )
        return NoContent()
    except DomainUnauthorized:
        return NoContent()
    except DomainForbidden as exc:
        return Forbidden(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


def lambda_handler(event, context):
    return app.resolve(event, context)
