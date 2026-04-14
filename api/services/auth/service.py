from typing import overload

from shared.abc import ApiModel, BaseService, public_api
from shared.errors import DomainError, assert_unreachable

from .provider import AuthProvider, Challenge, Tokens

# ──── Request Payloads ────────────────────────────────────────────────────────────────


class AuthRequest:
    class Login(ApiModel):
        username: str
        password: str

    class Challenge(ApiModel):
        challengeName: str
        session: str
        challengeResponses: dict[str, str]

    class Forgot(ApiModel):
        username: str

    class Reset(ApiModel):
        username: str
        confirmationCode: str
        newPassword: str

    class Refresh(ApiModel):
        refreshToken: str

    class Logout(ApiModel):
        accessToken: str | None = None
        refreshToken: str | None = None


# ──── Response Payloads ───────────────────────────────────────────────────────────────


class AuthResponse:
    class Tokens(ApiModel):
        accessToken: str
        expiresIn: int
        refreshToken: str | None = None
        idToken: str | None = None

    class Challenge(ApiModel):
        challengeName: str
        session: str
        challengeParameters: dict[str, str] | None = None
        availableChallenges: list[str] | None = None

    class Failed(ApiModel): ...


# ──── Authentication Service ──────────────────────────────────────────────────────────


class AuthService(BaseService):
    provider: AuthProvider

    # ──── Helper Methods ────

    @overload
    @staticmethod
    def _result(x: Tokens) -> AuthResponse.Tokens: ...
    @overload
    @staticmethod
    def _result(x: Challenge) -> AuthResponse.Challenge: ...
    @overload
    @staticmethod
    def _result(x: None) -> None: ...

    @staticmethod
    def _result(
        x: Tokens | Challenge | None,
    ) -> AuthResponse.Tokens | AuthResponse.Challenge | None:
        match x:
            case Tokens() as tokens:
                return AuthResponse.Tokens(
                    accessToken=tokens.access_token,
                    expiresIn=tokens.expires_in,
                    refreshToken=tokens.refresh_token,
                    idToken=tokens.id_token,
                )
            case Challenge() as challenge:
                return AuthResponse.Challenge(
                    challengeName=challenge.challenge,
                    session=challenge.session,
                    challengeParameters=challenge.parameters,
                    availableChallenges=challenge.branches,
                )
            case None:
                return None
            case _ as never:
                assert_unreachable(never)

    # ──── Public APIs ────

    @public_api
    def login(
        self,
        payload: AuthRequest.Login,
    ) -> AuthResponse.Tokens | AuthResponse.Challenge | AuthResponse.Failed:
        try:
            x = self.provider.authenticate(
                username=payload.username,
                password=payload.password,
            )
        except DomainError:
            return AuthResponse.Failed()
        return self._result(x)

    @public_api
    def challenge(
        self,
        payload: AuthRequest.Challenge,
    ) -> AuthResponse.Tokens | AuthResponse.Challenge | AuthResponse.Failed:
        try:
            x = self.provider.respond_to_challenge(
                session=payload.session,
                challenge=payload.challengeName,
                response=payload.challengeResponses,
            )
        except DomainError:
            return AuthResponse.Failed()
        return self._result(x)

    @public_api
    def forgot(
        self,
        payload: AuthRequest.Forgot,
    ) -> None | AuthResponse.Failed:
        try:
            x = self.provider.forgot_password(
                username=payload.username,
            )
        except DomainError:
            return AuthResponse.Failed()
        return self._result(x)

    @public_api
    def reset(
        self,
        payload: AuthRequest.Reset,
    ) -> None | AuthResponse.Failed:
        try:
            x = self.provider.reset_password(
                username=payload.username,
                confirmation_code=payload.confirmationCode,
                new_password=payload.newPassword,
            )
        except DomainError:
            return AuthResponse.Failed()
        return self._result(x)

    @public_api
    def refresh(
        self,
        payload: AuthRequest.Refresh,
    ) -> AuthResponse.Tokens | AuthResponse.Failed:
        try:
            x = self.provider.refresh_tokens(
                refresh_token=payload.refreshToken,
            )
        except DomainError:
            return AuthResponse.Failed()
        return self._result(x)

    @public_api
    def logout(
        self,
        payload: AuthRequest.Logout,
    ) -> None | AuthResponse.Failed:
        try:
            x = self.provider.revoke_tokens(
                access_token=payload.accessToken,
                refresh_token=payload.refreshToken,
            )
        except DomainError:
            return AuthResponse.Failed()
        return self._result(x)
