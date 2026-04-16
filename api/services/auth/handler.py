from shared.errors import assert_unreachable
from shared.http import Body, HttpResolver
from shared.http.errors import Unauthorized
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
    },
)
def login(
    request: Body[AuthRequest.Login],
) -> OK[AuthResponse.Tokens] | Accepted[AuthResponse.Challenge] | Unauthorized:
    match svc.login(request):
        case AuthResponse.Tokens() as tokens:
            return OK(tokens)
        case AuthResponse.Challenge() as challenge:
            return Accepted(challenge)
        case _ as never:
            assert_unreachable(never)


@app.post(
    "/auth/challenge",
    summary="Respond to auth challenge",
    description="Submit challenge response and continue authentication flow.",
    tags=["auth"],
    responses={
        200: "Authentication completed",
        202: "Further authentication challenge required",
        401: "Invalid challenge response",
    },
)
def challenge(
    request: Body[AuthRequest.Challenge],
) -> OK[AuthResponse.Tokens] | Accepted[AuthResponse.Challenge] | Unauthorized:
    match svc.challenge(request):
        case AuthResponse.Tokens() as tokens:
            return OK(tokens)
        case AuthResponse.Challenge() as challenge:
            return Accepted(challenge)
        case _ as never:
            assert_unreachable(never)


@app.post(
    "/auth/refresh",
    summary="Refresh tokens",
    description="Refresh access token using refresh token.",
    tags=["auth"],
    responses={
        200: "Tokens refreshed",
        401: "Invalid refresh token",
    },
)
def refresh(
    request: Body[AuthRequest.Refresh],
) -> OK[AuthResponse.Tokens] | Unauthorized:
    match svc.refresh(request):
        case AuthResponse.Tokens() as tokens:
            return OK(tokens)
        case _ as never:
            assert_unreachable(never)


@app.post(
    "/auth/logout",
    summary="Logout user",
    description="Logout user by invalidating their tokens.",
    tags=["auth"],
    responses={
        204: "User logged out",
    },
)
def logout(
    request: Body[AuthRequest.Logout],
) -> NoContent:
    match svc.logout(request):
        case None:
            return NoContent()
        case _ as never:
            assert_unreachable(never)


def lambda_handler(event, context):
    return app.resolve(event, context)
