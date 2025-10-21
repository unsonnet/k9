# services/auth/base.py
from abc import ABC, abstractmethod
from models.api import TokenResponse

class AuthProvider(ABC):
    """Abstract authentication provider interface."""
    
    @abstractmethod
    def login(self, username: str, password: str) -> TokenResponse: ...
    
    @abstractmethod
    def refresh(self, username: str, refresh_token: str) -> TokenResponse: ...
    
    @abstractmethod
    def forgot(self, username: str) -> None: ...
    
    @abstractmethod
    def reset(self, user: str, session: str, new_password: str) -> None: ...
