import base64
from typing import Iterable

from shared.config import GrantSpec, settings
from shared.providers import BaseProvider, apimethod
from shared.providers.identity import (
    MFA,
    Challenge,
    ChallengeKey,
    IdentityProvider,
    Tokens,
)

__all__ = [
    "ChallengeKey",
    "Challenge",
    "Tokens",
    "MFA",
    "AuthProvider",
]


class AuthProvider(BaseProvider):
    _idp: IdentityProvider

    def __init__(
        self,
        *,
        region: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        user_pool_id: str | None = None,
    ) -> None:
        region = region or settings.aws_region
        # cognito idp
        self._idp = IdentityProvider(
            region=region,
            client=client_id or settings.cognito_client_id,
            secret=client_secret or settings.cognito_client_secret,
            pool=user_pool_id or settings.cognito_user_pool_id,
        )

    @property
    def permissions(self) -> Iterable[GrantSpec]:
        yield from self._idp.permissions

    # ──── Public Methods ────

    @apimethod
    def authenticate(
        self,
        *,
        name: str,
        password: str,
    ) -> Tokens | Challenge:
        return self._idp.authenticate(
            username=f"name:{self._encode(name)}",
            password=password,
        )

    @apimethod
    def respond_to_challenge(
        self,
        *,
        session: str,
        challenge: ChallengeKey,
        response: dict[str, str],
    ) -> Tokens | Challenge:
        match challenge:
            case "NEW_PASSWORD_REQUIRED":
                return self._idp.respond_to_challenge(
                    session=session,
                    challenge="NEW_PASSWORD_REQUIRED",
                    username=f"name:{self._encode(response['name'])}",
                    new_password=response["password"],
                )
            case "SOFTWARE_TOKEN_MFA":
                return self._idp.respond_to_challenge(
                    session=session,
                    challenge="SOFTWARE_TOKEN_MFA",
                    username=f"name:{self._encode(response['name'])}",
                    software_token_mfa_code=response["code"],
                )
        raise NotImplementedError

    @apimethod
    def setup_mfa(
        self,
        *,
        access_token: str,
        name: str,
    ) -> MFA:
        return self._idp.setup_mfa(
            access_token=access_token,
            label=f"K9 - {name}",
        )

    @apimethod
    def verify_mfa(
        self,
        *,
        access_token: str,
        code: str,
    ) -> None:
        return self._idp.verify_mfa(
            access_token=access_token,
            code=code,
        )

    @apimethod
    def refresh_tokens(
        self,
        *,
        refresh_token: str,
    ) -> Tokens:
        return self._idp.refresh_tokens(
            refresh_token=refresh_token,
        )

    @apimethod
    def revoke_tokens(
        self,
        *,
        id: str,
    ) -> None:
        return self._idp.revoke_tokens(
            username=f"id:{id}",
        )

    # ──── Private Methods ────

    @staticmethod
    def _encode(name: str) -> str:
        return base64.b64encode(name.encode()).decode("ascii")
