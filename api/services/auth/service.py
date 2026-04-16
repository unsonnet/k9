from typing import overload

from shared.abc import ApiModel, BaseService, public_api
from shared.errors import assert_unreachable

from .provider import AuthProvider, Challenge, ChallengeKey, Tokens

# ──── Request Payloads ────────────────────────────────────────────────────────────────


class AuthRequest:
    class Login(ApiModel, frozen=True):
        username: str
        password: str

    class Challenge(ApiModel, frozen=True):
        session: str
        challenge: ChallengeKey
        response: dict[str, str]

    class Forgot(ApiModel, frozen=True):
        username: str

    class Reset(ApiModel, frozen=True):
        username: str
        confirmationCode: str
        newPassword: str

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

    class Challenge(ApiModel, frozen=True):
        session: str
        challenge: ChallengeKey
        parameters: list[str]


# ──── Helper Methods ──────────────────────────────────────────────────────────────────


@overload
def _response(result: Tokens) -> AuthResponse.Tokens: ...
@overload
def _response(result: Challenge) -> AuthResponse.Challenge: ...
def _response(
    result: Tokens | Challenge,
) -> AuthResponse.Tokens | AuthResponse.Challenge:
    match result:
        case Tokens() as tokens:
            return AuthResponse.Tokens(
                accessToken=tokens.access_token,
                expiresIn=tokens.expires_in,
                refreshToken=tokens.refresh_token,
                idToken=tokens.id_token,
            )
        case Challenge() as challenge:
            return AuthResponse.Challenge(
                session=challenge.session,
                challenge=challenge.challenge,
                parameters=challenge.parameters,
            )
        case _ as never:
            assert_unreachable(never)


# ──── Authentication Service ──────────────────────────────────────────────────────────


class AuthService(BaseService):
    provider: AuthProvider

    # ──── Public APIs ────

    @public_api
    def login(
        self,
        request: AuthRequest.Login,
    ) -> AuthResponse.Tokens | AuthResponse.Challenge:
        return _response(
            self.provider.authenticate(
                username=request.username,
                password=request.password,
            )
        )

    @public_api
    def challenge(
        self,
        request: AuthRequest.Challenge,
    ) -> AuthResponse.Tokens | AuthResponse.Challenge:
        return _response(
            self.provider.respond_to_challenge(
                session=request.session,
                challenge=request.challenge,
                response=request.response,
            )
        )

    @public_api
    def refresh(
        self,
        request: AuthRequest.Refresh,
    ) -> AuthResponse.Tokens:
        return _response(
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
