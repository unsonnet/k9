# services/auth/service.py
from config import settings
from models.api import TokenResponse
from utils.http import Unauthorized
from .base import AuthProvider
from .cognito import CognitoAuthProvider
from .local import LocalAuthProvider


class AuthService:
    """Delegates authentication calls to the configured provider."""

    def __init__(self) -> None:
        mode = settings().auth_mode.lower()
        self.provider: AuthProvider = self._init_provider(mode)

    def _init_provider(self, mode: str) -> AuthProvider:
        if mode == "cognito":
            return CognitoAuthProvider()
        if mode in {"local", "dev", "test"}:
            return LocalAuthProvider()
        raise Unauthorized(f"Unknown auth mode: {mode}")

    def login(self, username: str, password: str) -> TokenResponse:
        return self.provider.login(username, password)

    def refresh(self, username: str, refresh_token: str) -> TokenResponse:
        return self.provider.refresh(username, refresh_token)

    def forgot(self, username: str) -> None:
        self.provider.forgot(username)

    def reset(self, user: str, session: str, new_password: str) -> None:
        self.provider.reset(user, session, new_password)
