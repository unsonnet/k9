import base64
import hashlib
import hmac
from typing import Any, Iterable, Mapping, Protocol
from urllib.parse import quote

import boto3
from shared.config import GrantSpec, settings
from shared.errors import (
    DomainExpiredToken,
    DomainForbidden,
    DomainInvalidCredentials,
    DomainInvalidTokens,
    DomainInvariantViolation,
    DomainNotFound,
    DomainRateLimited,
)
from shared.helpers import now
from shared.providers import BaseProvider, ExceptionMap, apimethod
from types_boto3_cognito_idp import CognitoIdentityProviderClient

from .models import MFA, Challenge, ChallengeKey, Tokens

__all__ = [
    "AuthProvider",
    "CognitoAuthProvider",
]


class AuthProvider(Protocol):
    @property
    def permissions(self) -> Iterable[GrantSpec]: ...

    def authenticate(
        self,
        *,
        name: str,
        password: str,
    ) -> Tokens | Challenge: ...

    def respond_to_challenge(
        self,
        *,
        session: str,
        challenge: ChallengeKey,
        response: dict[str, str],
    ) -> Tokens | Challenge: ...

    def setup_mfa(
        self,
        *,
        access_token: str,
        name: str,
    ) -> MFA: ...

    def verify_mfa(
        self,
        *,
        access_token: str,
        code: str,
    ) -> None: ...

    def refresh_tokens(
        self,
        *,
        refresh_token: str,
    ) -> Tokens: ...

    def revoke_tokens(
        self,
        *,
        id: str,
    ) -> None: ...


# ──── AWS Authentication Provider ─────────────────────────────────────────────────────


class CognitoAuthProvider(BaseProvider):
    _idp: CognitoIdentityProviderClient
    _idp_id: str
    _idp_secret: str
    _idp_pool: str

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
        self._idp = boto3.client("cognito-idp", region_name=region)
        self._idp_id = client_id or settings.cognito_client_id
        self._idp_secret = client_secret or settings.cognito_client_secret
        self._idp_pool = user_pool_id or settings.cognito_user_pool_id

    @property
    def permissions(self) -> Iterable[GrantSpec]:
        yield GrantSpec(
            actions=(
                "cognito-idp:AdminInitiateAuth",
                "cognito-idp:AdminRespondToAuthChallenge",
                "cognito-idp:AdminUpdateUserAttributes",
                "cognito-idp:AdminUserGlobalSignOut",
                "cognito-idp:AssociateSoftwareToken",
                "cognito-idp:GetTokensFromRefreshToken",
                "cognito-idp:SetUserMFAPreference",
                "cognito-idp:VerifySoftwareToken",
            ),
            resources=("cognito-user-pool",),
        )

    @property
    def _exception_map(self) -> ExceptionMap:
        cx = self._idp.exceptions
        return {
            DomainExpiredToken: [
                cx.ExpiredCodeException,
                cx.PasswordResetRequiredException,
            ],
            DomainForbidden: [
                cx.ForbiddenException,
                cx.UnauthorizedException,
            ],
            DomainInvalidCredentials: [
                cx.NotAuthorizedException,
                cx.InvalidPasswordException,
                cx.CodeMismatchException,
            ],
            DomainInvalidTokens: [
                cx.RefreshTokenReuseException,
                cx.UnsupportedTokenTypeException,
            ],
            DomainRateLimited: [
                cx.TooManyRequestsException,
                cx.LimitExceededException,
            ],
            DomainNotFound: [
                cx.UserNotFoundException,
            ],
        }

    # ──── Private Methods ────

    def _secret_hash(self, xname: str) -> str:
        message = f"{xname}{self._idp_id}".encode("utf-8")
        key = self._idp_secret.encode("utf-8")
        digest = hmac.new(key, message, hashlib.sha256).digest()
        return base64.b64encode(digest).decode("utf-8")

    @staticmethod
    def _encode_id(id: str) -> str:
        return f"id:{id}"

    @staticmethod
    def _encode_name(name: str) -> str:
        return f"name:{base64.b64encode(name.encode()).decode('ascii')}"

    @classmethod
    def _tokens(cls, response: Mapping[str, Any]) -> Tokens:
        match response:
            case {
                "AuthenticationResult": {
                    "AccessToken": str(access_token),
                    "ExpiresIn": int(expires_in),
                    "RefreshToken": str(refresh_token),
                    "IdToken": str(id_token),
                }
            }:
                return Tokens(
                    access_token=access_token,
                    expires_in=expires_in,
                    refresh_token=refresh_token,
                    id_token=id_token,
                )
        raise DomainInvariantViolation(f"Unexpected cognito tokens: {response}")

    @classmethod
    def _challenge(cls, response: Mapping[str, Any]) -> Challenge:
        match response:
            case {"Session": str(session), "ChallengeName": str(challenge)}:
                match challenge:
                    case "NEW_PASSWORD_REQUIRED":
                        return Challenge(
                            session=session,
                            challenge=ChallengeKey.NEW_PASSWORD,
                        )
                    case "SOFTWARE_TOKEN_MFA":
                        return Challenge(
                            session=session,
                            challenge=ChallengeKey.MFA,
                        )
        raise DomainInvariantViolation(f"Unexpected cognito challenge: {response}")

    @classmethod
    def _result(cls, response: Mapping[str, Any]) -> Tokens | Challenge:
        match response:
            case {"AuthenticationResult": dict()}:
                return cls._tokens(response)
            case {"Session": str(), "ChallengeName": str()}:
                return cls._challenge(response)
        raise DomainInvariantViolation(f"Unexpected cognito response: {response}")

    @classmethod
    def _mfa(cls, response: Mapping[str, Any], *, name: str) -> MFA:
        match response:
            case {"SecretCode": str(secret)}:
                issuer = quote("Amazon Web Services")
                label = f"{issuer}:{quote(f'K9 - {name}')}"
                return MFA(
                    secret=secret,
                    url=f"otpauth://totp/{label}?secret={secret}&issuer={issuer}",
                )
        raise DomainInvariantViolation(f"Unexpected cognito MFA: {response}")

    def _log_auth(self, xname: str) -> None:
        self._idp.admin_update_user_attributes(
            UserPoolId=self._idp_pool,
            Username=xname,
            UserAttributes=[
                {
                    "Name": "custom:last_login_at",
                    "Value": now().strftime("%Y-%m-%d %H:%M:%S %z"),
                }
            ],
        )

    # ──── Public Methods ────

    @apimethod
    def authenticate(
        self,
        *,
        name: str,
        password: str,
    ) -> Tokens | Challenge:
        xname = self._encode_name(name)
        result = self._result(
            self._idp.admin_initiate_auth(
                ClientId=self._idp_id,
                UserPoolId=self._idp_pool,
                AuthFlow="ADMIN_USER_PASSWORD_AUTH",
                AuthParameters={
                    "SECRET_HASH": self._secret_hash(xname),
                    "USERNAME": xname,
                    "PASSWORD": password,
                },
            )
        )
        if isinstance(result, Tokens):
            self._log_auth(xname)
        return result

    @apimethod
    def respond_to_challenge(
        self,
        *,
        session: str,
        challenge: ChallengeKey,
        response: dict[str, str],
    ) -> Tokens | Challenge:
        xname = self._encode_name(response["name"])
        match challenge:
            case ChallengeKey.NEW_PASSWORD:
                result = self._result(
                    self._idp.admin_respond_to_auth_challenge(
                        ClientId=self._idp_id,
                        UserPoolId=self._idp_pool,
                        Session=session,
                        ChallengeName="NEW_PASSWORD_REQUIRED",
                        ChallengeResponses={
                            "SECRET_HASH": self._secret_hash(xname),
                            "USERNAME": xname,
                            "NEW_PASSWORD": response["password"],
                        },
                    )
                )
            case ChallengeKey.MFA:
                result = self._tokens(
                    self._idp.admin_respond_to_auth_challenge(
                        ClientId=self._idp_id,
                        UserPoolId=self._idp_pool,
                        Session=session,
                        ChallengeName="SOFTWARE_TOKEN_MFA",
                        ChallengeResponses={
                            "SECRET_HASH": self._secret_hash(xname),
                            "USERNAME": xname,
                            "SOFTWARE_TOKEN_MFA_CODE": response["code"],
                        },
                    )
                )
        if isinstance(result, Tokens):
            self._log_auth(xname)
        return result

    @apimethod
    def setup_mfa(
        self,
        *,
        access_token: str,
        name: str,
    ) -> MFA:
        return self._mfa(
            self._idp.associate_software_token(
                AccessToken=access_token,
            ),
            name=name,
        )

    @apimethod
    def verify_mfa(
        self,
        *,
        access_token: str,
        code: str,
    ) -> None:
        self._idp.verify_software_token(
            AccessToken=access_token,
            UserCode=code,
        )
        self._idp.set_user_mfa_preference(
            AccessToken=access_token,
            SoftwareTokenMfaSettings={
                "Enabled": True,
                "PreferredMfa": True,
            },
        )
        return None

    @apimethod
    def refresh_tokens(
        self,
        *,
        refresh_token: str,
    ) -> Tokens:
        return self._tokens(
            self._idp.get_tokens_from_refresh_token(
                ClientId=self._idp_id,
                ClientSecret=self._idp_secret,
                RefreshToken=refresh_token,
            )
        )

    @apimethod
    def revoke_tokens(
        self,
        *,
        id: str,
    ) -> None:
        self._idp.admin_user_global_sign_out(
            UserPoolId=self._idp_pool,
            Username=self._encode_id(id),
        )
        return None
