from shared.abc import BaseService, public_api

from .payloads import Request, Response
from .providers.auth import AuthProvider, Challenge, Tokens

__all__ = [
    "AuthService",
]


# ──── Authentication Service ──────────────────────────────────────────────────────────


class AuthService(BaseService):
    provider: AuthProvider

    def __init__(self, provider: AuthProvider) -> None:
        self.provider = provider

    # ──── Public APIs ────

    @public_api
    def login(
        self,
        request: Request.Login,
    ) -> Response.Tokens | Response.Challenge:
        match self.provider.authenticate(
            name=request.name,
            password=request.password,
        ):
            case Tokens() as tokens:
                return Response.Tokens.from_(tokens)
            case Challenge() as challenge:
                return Response.Challenge.from_(challenge)

    @public_api
    def challenge(
        self,
        request: Request.Challenge,
    ) -> Response.Tokens | Response.Challenge:
        match self.provider.respond_to_challenge(
            session=request.session,
            challenge=request.challenge,
            response=request.response,
        ):
            case Tokens() as tokens:
                return Response.Tokens.from_(tokens)
            case Challenge() as challenge:
                return Response.Challenge.from_(challenge)

    @public_api
    def refresh(
        self,
        request: Request.Refresh,
    ) -> Response.Tokens:
        return Response.Tokens.from_(
            self.provider.refresh_tokens(
                refresh_token=request.refreshToken,
            )
        )

    @public_api
    def logout(
        self,
        request: Request.Logout,
    ) -> None:
        return self.provider.revoke_tokens(
            access_token=request.accessToken,
            refresh_token=request.refreshToken,
        )
