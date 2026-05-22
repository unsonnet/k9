from shared.abc import BaseService, Caller, public_api

from .models import Provider, Request, Response
from .provider import AuthProvider

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
            case Provider.Tokens() as tokens:
                return Response.Tokens.from_provider(tokens)
            case Provider.Challenge() as challenge:
                return Response.Challenge.from_provider(challenge)

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
            case Provider.Tokens() as tokens:
                return Response.Tokens.from_provider(tokens)
            case Provider.Challenge() as challenge:
                return Response.Challenge.from_provider(challenge)

    @public_api
    def setup(
        self,
        caller: Caller,
    ) -> Response.MFA:
        return Response.MFA.from_provider(
            self.provider.setup_mfa(
                access_token=caller.token,
                name=caller.name,
            )
        )

    @public_api
    def verify(
        self,
        caller: Caller,
        request: Request.Verify,
    ) -> None:
        return self.provider.verify_mfa(
            access_token=caller.token,
            code=request.code,
        )

    @public_api
    def refresh(
        self,
        request: Request.Refresh,
    ) -> Response.Tokens:
        return Response.Tokens.from_provider(
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
