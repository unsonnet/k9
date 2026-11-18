from k9.resolvers.http.errors import Forbidden, TooManyRequests, Unauthorized
from k9.resolvers.http.responses import OK, Accepted, NoContent
from k9.types.common import Caller
from k9.types.errors import DomainForbidden, DomainRateLimited, DomainUnauthorized

from . import app
from .http import Login, LoginChallenge, Logout, Refresh, Verify
from .provider import MFA, AuthProvider, Challenge, Tokens

provider = AuthProvider()
app.grant(*provider.permissions)


@app.post(
    "/auth/login",
    summary="Authenticate user",
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
    request: Login,
) -> OK[Tokens] | Accepted[Challenge] | Unauthorized | Forbidden | TooManyRequests:
    try:
        match provider.authenticate(
            name=request.name,
            password=request.password,
        ):
            case Tokens() as tokens:
                return OK(tokens)
            case Challenge() as challenge:
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
    request: LoginChallenge,
) -> OK[Tokens] | Accepted[Challenge] | Unauthorized | Forbidden | TooManyRequests:
    try:
        match provider.respond_to_challenge(
            session=request.session,
            challenge=request.challenge,
            response=request.response,
        ):
            case Tokens() as tokens:
                return OK(tokens)
            case Challenge() as challenge:
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
) -> OK[MFA] | Unauthorized | Forbidden | TooManyRequests:
    try:
        mfa = provider.setup_mfa(
            access_token=caller.token,
            name=caller.name,
        )
        return OK(mfa)
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainForbidden as exc:
        return Forbidden(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


@app.post(
    "/auth/mfa/verify",
    summary="Verify MFA enrollment",
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
    request: Verify,
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
    tags=["auth"],
    responses={
        200: "Tokens refreshed",
        401: "Invalid refresh token",
        403: "Access denied",
        429: "Too many requests",
    },
)
def refresh(
    request: Refresh,
) -> OK[Tokens] | Unauthorized | Forbidden | TooManyRequests:
    try:
        tokens = provider.refresh_tokens(
            refresh_token=request.refreshToken,
        )
        return OK(tokens)
    except DomainUnauthorized as exc:
        return Unauthorized("Invalid refresh token", cause=exc)
    except DomainForbidden as exc:
        return Forbidden(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


@app.post(
    "/auth/logout/<id>",
    summary="Logout user",
    tags=["auth"],
    responses={
        204: "User logged out",
        403: "Access denied",
        429: "Too many requests",
    },
)
def logout(
    caller: Caller,
    request: Logout,
) -> NoContent | Forbidden | TooManyRequests:
    try:
        user_id = caller.resolve(request.id)
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
