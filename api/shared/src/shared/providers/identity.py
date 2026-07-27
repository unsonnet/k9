import base64
import hashlib
import hmac
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping, Sequence, get_args
from urllib.parse import quote

import boto3
from types_boto3_cognito_idp import CognitoIdentityProviderClient
from types_boto3_cognito_idp.literals import ChallengeNameTypeType
from types_boto3_cognito_idp.type_defs import AttributeTypeTypeDef

from ..config import GrantSpec, is_set, missing
from ..errors import (
    DomainExpiredToken,
    DomainForbidden,
    DomainInvalidCredentials,
    DomainInvalidTokens,
    DomainInvariantViolation,
    DomainNotFound,
    DomainRateLimited,
)
from ..helpers import dt, now
from . import BaseProvider, ExceptionMap, apimethod

__all__ = [
    "ChallengeKey",
    "Challenge",
    "Tokens",
    "MFA",
    "User",
    "UserPage",
    "IdentityProvider",
]

_STANDARD_ATTRIBUTES: set[str] = {
    "address",
    "birthdate",
    "email",
    "family_name",
    "gender",
    "given_name",
    "locale",
    "middle_name",
    "name",
    "nickname",
    "phone_number",
    "picture",
    "preferred_username",
    "profile",
    "updated_at",
    "website",
    "zoneinfo",
}


type ChallengeKey = ChallengeNameTypeType


@dataclass(frozen=True, slots=True)
class Challenge:
    session: str
    challenge: ChallengeKey


@dataclass(frozen=True, slots=True)
class Tokens:
    access_token: str
    expires_in: int
    refresh_token: str | None
    id_token: str | None


@dataclass(frozen=True, slots=True)
class MFA:
    secret: str
    url: str


@dataclass(frozen=True, slots=True)
class User:
    username: str
    enabled: bool
    attributes: dict[str, str | None]
    created_at: datetime
    updated_at: datetime | None
    last_login_at: datetime | None

    def __getitem__(self, key: str) -> str | None:
        return self.attributes.get(key)


@dataclass(frozen=True, slots=True)
class UserPage:
    users: list[User]
    cursor: str | None


class IdentityProvider(BaseProvider):
    _idp: CognitoIdentityProviderClient
    _idp_id: str
    _idp_secret: str
    _idp_pool: str

    def __init__(
        self,
        *,
        region: str,
        pool: str | None = None,
        client: str | None = None,
        secret: str | None = None,
    ) -> None:
        self._idp = boto3.client("cognito-idp", region_name=region)
        self._idp_pool = pool or NotImplemented
        self._idp_id = client or NotImplemented
        self._idp_secret = secret or NotImplemented

    @property
    def permissions(self) -> Iterable[GrantSpec]:
        yield GrantSpec(
            actions=(
                "cognito-idp:AdminCreateUser",
                "cognito-idp:AdminDeleteUser",
                "cognito-idp:AdminDisableUser",
                "cognito-idp:AdminEnableUser",
                "cognito-idp:AdminGetUser",
                "cognito-idp:AdminInitiateAuth",
                "cognito-idp:AdminRespondToAuthChallenge",
                "cognito-idp:AdminSetUserMFAPreference",
                "cognito-idp:AdminSetUserPassword",
                "cognito-idp:AdminUpdateUserAttributes",
                "cognito-idp:AdminUserGlobalSignOut",
                "cognito-idp:AssociateSoftwareToken",
                "cognito-idp:GetTokensFromRefreshToken",
                "cognito-idp:ListUsers",
                "cognito-idp:SetUserMFAPreference",
                "cognito-idp:VerifySoftwareToken",
            ),
            resources=("cognito-user-pool",),
        )

    @property
    def exception_map(self) -> ExceptionMap:
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
                cx.ResourceNotFoundException,
            ],
        }

    # ──── Public Auth Methods ────

    @apimethod
    def authenticate(
        self,
        *,
        username: str,
        password: str,
    ) -> Tokens | Challenge:
        return self._auth(
            self._idp.admin_initiate_auth(
                ClientId=self._idp_id,
                UserPoolId=self._idp_pool,
                AuthFlow="ADMIN_USER_PASSWORD_AUTH",
                AuthParameters={
                    "SECRET_HASH": self._secret_hash(username),
                    "USERNAME": username,
                    "PASSWORD": password,
                },
            ),
            username=username,
        )

    @apimethod
    def respond_to_challenge(
        self,
        *,
        session: str,
        challenge: ChallengeKey,
        username: str,
        **responses: str,
    ) -> Tokens | Challenge:
        responses["SECRET_HASH"] = self._secret_hash(username)
        responses["USERNAME"] = username
        return self._auth(
            self._idp.admin_respond_to_auth_challenge(
                ClientId=self._idp_id,
                UserPoolId=self._idp_pool,
                Session=session,
                ChallengeName=challenge,
                ChallengeResponses={key.upper(): val for key, val in responses.items()},
            ),
            username=username,
        )

    @apimethod
    def setup_mfa(
        self,
        *,
        access_token: str,
        label: str,
    ) -> MFA:
        return self._mfa(
            self._idp.associate_software_token(AccessToken=access_token),
            issuer="Amazon Web Services",
            label=label,
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
            )["AuthenticationResult"]
        )

    @apimethod
    def revoke_tokens(
        self,
        *,
        username: str,
    ) -> None:
        self._idp.admin_user_global_sign_out(
            UserPoolId=self._idp_pool,
            Username=username,
        )
        return None

    # ──── Public User Methods ────

    @apimethod
    def list_users(
        self,
        *,
        limit: int,
        cursor: str | None,
    ) -> UserPage:
        return self._user_page(
            self._idp.list_users(
                UserPoolId=self._idp_pool,
                Limit=limit,
                **({"PaginationToken": cursor} if cursor else {}),
            )
        )

    @apimethod
    def create_user(
        self,
        *,
        username: str,
        password: str,
        enabled: bool,
        **attrs: str | None,
    ) -> User:
        self._idp.admin_create_user(
            UserPoolId=self._idp_pool,
            Username=username,
            UserAttributes=self._pack(attrs),
            MessageAction="SUPPRESS",
        )
        self._idp.admin_set_user_password(
            UserPoolId=self._idp_pool,
            Username=username,
            Password=password,
            Permanent=False,
        )
        if not enabled:
            self._idp.admin_disable_user(
                UserPoolId=self._idp_pool,
                Username=username,
            )
        return self.read_user(username=username)

    @apimethod
    def read_user(
        self,
        *,
        username: str,
    ) -> User:
        return self._user(
            self._idp.admin_get_user(
                UserPoolId=self._idp_pool,
                Username=username,
            )
        )

    @apimethod
    def update_user(
        self,
        *,
        username: str,
        enabled: bool | missing,
        **attrs: str | None,
    ) -> User:
        if attrs:
            self._idp.admin_update_user_attributes(
                UserPoolId=self._idp_pool,
                Username=username,
                UserAttributes=self._pack(attrs),
            )
        if is_set(enabled):
            if enabled:
                self._idp.admin_enable_user(
                    UserPoolId=self._idp_pool,
                    Username=username,
                )
            else:
                self._idp.admin_disable_user(
                    UserPoolId=self._idp_pool,
                    Username=username,
                )
        return self.read_user(username=username)

    @apimethod
    def delete_user(
        self,
        *,
        username: str,
    ) -> None:
        self._idp.admin_delete_user(
            UserPoolId=self._idp_pool,
            Username=username,
        )
        return None

    @apimethod
    def reset_user(
        self,
        *,
        username: str,
        password: str,
    ) -> None:
        self._idp.admin_set_user_password(
            UserPoolId=self._idp_pool,
            Username=username,
            Password=password,
            Permanent=False,
        )
        self._idp.admin_set_user_mfa_preference(
            UserPoolId=self._idp_pool,
            Username=username,
            SoftwareTokenMfaSettings={
                "Enabled": False,
                "PreferredMfa": False,
            },
        )
        self._idp.admin_user_global_sign_out(
            UserPoolId=self._idp_pool,
            Username=username,
        )
        return None

    # ──── Private Auth Methods ────

    def _secret_hash(self, username: str) -> str:
        key = self._idp_secret.encode("utf-8")
        message = f"{username}{self._idp_id}".encode("utf-8")
        digest = hmac.new(key, message, hashlib.sha256).digest()
        return base64.b64encode(digest).decode("utf-8")

    @classmethod
    def _tokens(cls, response: Mapping[str, Any], /) -> Tokens:
        match response:
            case {
                "AccessToken": str(access_token),
                "ExpiresIn": int(expires_in),
                "RefreshToken": str(refresh_token),
                "IdToken": str(id_token),
            }:
                return Tokens(
                    access_token=access_token,
                    expires_in=expires_in,
                    refresh_token=refresh_token,
                    id_token=id_token,
                )
        raise DomainInvariantViolation(f"Unexpected cognito tokens: {response}")

    @classmethod
    def _challenge(cls, /, session: str, challenge: str) -> Challenge:
        if challenge in frozenset(get_args(ChallengeNameTypeType)):
            return Challenge(
                session=session,
                challenge=challenge,  # type: ignore
            )
        raise DomainInvariantViolation(f"Unexpected cognito challenge: {challenge}")

    @classmethod
    def _mfa(cls, response: Mapping[str, Any], /, issuer: str, label: str) -> MFA:
        match response:
            case {"SecretCode": str(secret)}:
                issuer = quote(issuer)
                label = f"{issuer}:{quote(label)}"
                return MFA(
                    secret=secret,
                    url=f"otpauth://totp/{label}?secret={secret}&issuer={issuer}",
                )
        raise DomainInvariantViolation(f"Unexpected cognito MFA: {response}")

    def _auth(
        self,
        response: Mapping[str, Any],
        /,
        username: str,
    ) -> Tokens | Challenge:
        match response:
            case {"AuthenticationResult": dict(response)}:
                tokens = self._tokens(response)
                self._idp.admin_update_user_attributes(
                    UserPoolId=self._idp_pool,
                    Username=username,
                    UserAttributes=[
                        {
                            "Name": "custom:last_login_at",
                            "Value": now().strftime("%Y-%m-%d %H:%M:%S %z"),
                        }
                    ],
                )
                return tokens
            case {"Session": str(session), "ChallengeName": str(challenge)}:
                return self._challenge(session=session, challenge=challenge)
        raise DomainInvariantViolation(f"Unexpected cognito auth response: {response}")

    # ──── Private User Methods ────

    @staticmethod
    def _pack(attrs: Mapping[str, str | None]) -> Sequence[AttributeTypeTypeDef]:
        return [
            {
                "Name": key if key in _STANDARD_ATTRIBUTES else f"custom:{key}",
                "Value": val or "",
            }
            for key, val in attrs.items()
        ]

    @staticmethod
    def _unpack(attrs: Sequence[AttributeTypeTypeDef]) -> dict[str, str | None]:
        a = {kv["Name"].removeprefix("custom:"): kv.get("Value") for kv in attrs}
        a.setdefault("last_login_at", None)
        return a

    @classmethod
    def _user(cls, response: Mapping[str, Any], /) -> User:
        response = dict(response)
        response.setdefault("UserLastModifiedDate", None)
        response.setdefault("UserAttributes", response.get("Attributes", []))
        match response:
            case {
                "Username": str(username),
                "Enabled": bool(enabled),
                "UserCreateDate": datetime() as created_at,
                "UserLastModifiedDate": datetime() | None as updated_at,
                "UserAttributes": list(attributes),
            }:
                match cls._unpack(attributes):
                    case {
                        "last_login_at": str() | None as last_login_at,
                        **attributes,
                    }:
                        return User(
                            username=username,
                            enabled=enabled,
                            attributes=attributes,
                            created_at=dt(created_at),
                            updated_at=dt(updated_at),
                            last_login_at=dt(last_login_at, iso=False),
                        )
        raise DomainInvariantViolation(f"Unexpected cognito user: {response}")

    @classmethod
    def _user_page(cls, response: Mapping[str, Any], /) -> UserPage:
        response = dict(response)
        response.setdefault("PaginationToken", None)
        match response:
            case {"Users": list(users), "PaginationToken": str() | None as cursor}:
                return UserPage(
                    users=[cls._user(user) for user in users],
                    cursor=cursor,
                )
        raise DomainInvariantViolation(f"Unexpected cognito user page: {response}")
