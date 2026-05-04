from typing import Mapping

from shared.abc import ApiModel, BaseService, public_api
from shared.errors import assert_unreachable

from .providers import AuthProvider, Challenge, Tokens

__all__ = [
    "AuthRequest",
    "AuthResponse",
    "AuthService",
]

# ──── Request Payloads ────────────────────────────────────────────────────────────────


class AuthRequest:
    class Login(ApiModel, frozen=True):
        username: str
        password: str

    class Challenge(ApiModel, frozen=True):
        session: str
        challenge: Challenge.Key
        response: Mapping[str, str]

    class Refresh(ApiModel, frozen=True):
        refreshToken: str

    class Logout(ApiModel, frozen=True):
        accessToken: str | None = None
        refreshToken: str | None = None


# ──── Response Payloads ───────────────────────────────────────────────────────────────


class AuthResponse:
    class Tokens(ApiModel, frozen=True):
        accessToken: str
        expiresIn: int
        refreshToken: str | None = None
        idToken: str | None = None

        @classmethod
        def from_provider(cls, tokens: Tokens):
            return cls(
                accessToken=tokens.access_token,
                expiresIn=tokens.expires_in,
                refreshToken=tokens.refresh_token,
                idToken=tokens.id_token,
            )

    class Challenge(ApiModel, frozen=True):
        session: str
        challenge: Challenge.Key
        parameters: Mapping[str, str]

        @classmethod
        def from_provider(cls, challenge: Challenge):
            return cls(
                session=challenge.session,
                challenge=challenge.challenge,
                parameters=challenge.parameters,
            )


# ──── Authentication Service ──────────────────────────────────────────────────────────


class AuthService(BaseService):
    provider: AuthProvider

    def __init__(self, provider: AuthProvider) -> None:
        self.provider = provider

    # ──── Public APIs ────

    @public_api
    def login(
        self,
        request: AuthRequest.Login,
    ) -> AuthResponse.Tokens | AuthResponse.Challenge:
        match self.provider.authenticate(
            username=request.username,
            password=request.password,
        ):
            case Tokens() as tokens:
                return AuthResponse.Tokens.from_provider(tokens)
            case Challenge() as challenge:
                return AuthResponse.Challenge.from_provider(challenge)
            case _ as never:
                assert_unreachable(never)

    @public_api
    def challenge(
        self,
        request: AuthRequest.Challenge,
    ) -> AuthResponse.Tokens | AuthResponse.Challenge:
        match self.provider.respond_to_challenge(
            session=request.session,
            challenge=request.challenge,
            response=request.response,
        ):
            case Tokens() as tokens:
                return AuthResponse.Tokens.from_provider(tokens)
            case Challenge() as challenge:
                return AuthResponse.Challenge.from_provider(challenge)
            case _ as never:
                assert_unreachable(never)

    @public_api
    def refresh(
        self,
        request: AuthRequest.Refresh,
    ) -> AuthResponse.Tokens:
        return AuthResponse.Tokens.from_provider(
            self.provider.refresh_tokens(
                refresh_token=request.refreshToken,
            )
        )

    @public_api
    def logout(
        self,
        request: AuthRequest.Logout,
    ) -> None:
        return self.provider.revoke_tokens(
            access_token=request.accessToken,
            refresh_token=request.refreshToken,
        )
