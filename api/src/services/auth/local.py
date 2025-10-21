# services/auth/local.py
import uuid
from config import settings
from utils.auth import create_token, verify_token
from utils.http import InvalidRequest, Unauthorized
from models.api import TokenResponse

from .base import AuthProvider


class LocalAuthProvider(AuthProvider):
    def login(self, username: str, password: str) -> TokenResponse:
        if not username or not password:
            raise Unauthorized("Invalid credentials")
        user_id = uuid.uuid5(uuid.NAMESPACE_URL, f"user:{username}")
        return TokenResponse(
            user=user_id,
            accessToken=create_token(str(user_id), settings().access_token_ttl, "access"),
            refreshToken=create_token(str(user_id), settings().refresh_token_ttl, "refresh"),
            expiresIn=settings().access_token_ttl,
        )

    def refresh(self, username: str, refresh_token: str) -> TokenResponse:
        claims = verify_token(refresh_token, expected_typ="refresh")
        sub = claims["sub"]
        return TokenResponse(
            user=uuid.UUID(sub),
            accessToken=create_token(sub, settings().access_token_ttl, "access"),
            refreshToken=create_token(sub, settings().refresh_token_ttl, "refresh"),
            expiresIn=settings().access_token_ttl,
        )

    def forgot(self, username: str) -> None:
        if not username:
            raise InvalidRequest("Username required")

    def reset(self, user: str, session: str, new_password: str) -> None:
        if not (user and new_password):
            raise InvalidRequest("Missing fields")
