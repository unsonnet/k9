import uuid
from typing import Dict, NoReturn

from config import settings, boto3_client
from models.api import TokenResponse
from utils.auth import verify_token
from utils.cognito import compute_secret_hash
from utils.http import Forbidden, Gone, InvalidRequest, NotFound, Unauthorized

from .base import AuthProvider


class CognitoAuthProvider(AuthProvider):
    """Cognito-backed authentication provider (SECRET_HASH required)."""

    def __init__(self) -> None:
        cfg = settings()
        if not cfg.cognito_client_id:
            raise Unauthorized("Cognito client not configured")
        if not cfg.cognito_client_secret:
            raise Unauthorized("Cognito client secret not configured")

        self.client_id = cfg.cognito_client_id
        self.client_secret = cfg.cognito_client_secret
        self.idp = boto3_client("cognito-idp")

    # ──────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────

    def _secret_hash(self, username: str) -> str:
        return compute_secret_hash(username, self.client_id, self.client_secret)

    def _auth_params(self, username: str, **extra: str) -> Dict[str, str]:
        """Auth/Challenge params that always include USERNAME and SECRET_HASH."""
        return {"USERNAME": username, "SECRET_HASH": self._secret_hash(username), **extra}

    def _handle_error(self, e: Exception) -> NoReturn:
        msg = str(e)
        if "UserNotFoundException" in msg:
            raise NotFound("User not found")
        if "UserNotConfirmedException" in msg:
            raise Forbidden("User not confirmed")
        if "NotAuthorizedException" in msg:
            raise Unauthorized("Invalid credentials")
        if "CodeMismatchException" in msg:
            raise InvalidRequest("Invalid verification code")
        if "ExpiredCodeException" in msg or "SessionExpiredException" in msg:
            raise Gone("SessionExpired")
        raise Unauthorized(msg)

    def _extract_user_id(self, access_token: str) -> uuid.UUID:
        claims = verify_token(access_token, expected_typ=None)
        sub = claims.get("sub")
        if not sub:
            raise Unauthorized("Invalid token claims")
        return uuid.UUID(str(sub))

    # ──────────────────────────────────────────────────────────────
    # Interface
    # ──────────────────────────────────────────────────────────────

    def login(self, username: str, password: str) -> TokenResponse:
        try:
            res = self.idp.initiate_auth(
                AuthFlow="USER_PASSWORD_AUTH",
                AuthParameters=self._auth_params(username, PASSWORD=password),
                ClientId=self.client_id,
            )

            if res.get("ChallengeName") == "NEW_PASSWORD_REQUIRED":
                return TokenResponse(
                    user=uuid.uuid5(uuid.NAMESPACE_URL, f"user:{username}"),
                    accessToken="",
                    refreshToken=res.get("Session", ""),
                    expiresIn=settings().access_token_ttl,
                )

            auth = res.get("AuthenticationResult") or {}
            access, refresh = auth.get("AccessToken"), auth.get("RefreshToken")
            if not access or not refresh:
                raise Unauthorized("Authentication failed")

            user_id = self._extract_user_id(access)
            return TokenResponse(
                user=user_id,
                accessToken=access,
                refreshToken=refresh,
                expiresIn=int(auth.get("ExpiresIn", settings().access_token_ttl)),
            )
        except Exception as e:  # noqa: BLE001
            self._handle_error(e)

    def refresh(self, username: str, refresh_token: str) -> TokenResponse:
        try:
            params = self._auth_params(username, REFRESH_TOKEN=refresh_token)
            res = self.idp.initiate_auth(
                AuthFlow="REFRESH_TOKEN_AUTH",
                AuthParameters=params,
                ClientId=self.client_id,
            )

            auth = res.get("AuthenticationResult") or {}
            access = auth.get("AccessToken")
            if not access:
                raise Unauthorized("Refresh failed")

            user_id = self._extract_user_id(access)
            return TokenResponse(
                user=user_id,
                accessToken=access,
                refreshToken=auth.get("RefreshToken") or refresh_token,
                expiresIn=int(auth.get("ExpiresIn", settings().access_token_ttl)),
            )
        except Exception as e:  # noqa: BLE001
            self._handle_error(e)

    def forgot(self, username: str) -> None:
        try:
            self.idp.forgot_password(
                ClientId=self.client_id,
                Username=username,
                SecretHash=self._secret_hash(username),
            )
        except Exception as e:  # noqa: BLE001
            self._handle_error(e)

    def reset(self, user: str, session: str, new_password: str) -> None:
        try:
            if session.startswith("AYAB"):  # NEW_PASSWORD_REQUIRED session token
                self.idp.respond_to_auth_challenge(
                    ClientId=self.client_id,
                    ChallengeName="NEW_PASSWORD_REQUIRED",
                    ChallengeResponses=self._auth_params(user, NEW_PASSWORD=new_password),
                    Session=session,
                )
            else:  # Forgot-password flow
                self.idp.confirm_forgot_password(
                    ClientId=self.client_id,
                    Username=user,
                    ConfirmationCode=session,
                    Password=new_password,
                    SecretHash=self._secret_hash(user),
                )
        except Exception as e:  # noqa: BLE001
            self._handle_error(e)