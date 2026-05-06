from datetime import datetime
from enum import StrEnum
from typing import NotRequired, Protocol, Sequence, TypedDict

from shared.abc import DataModel

__all__ = [
    "User",
    "UserPage",
    "UserProvider",
]

# ──── User Models ─────────────────────────────────────────────────────────────────────


class User(DataModel, frozen=True):
    class Role(StrEnum):
        USER = "user"
        ADMIN = "admin"

    class Status(StrEnum):
        ACTIVE = "active"
        DISABLED = "disabled"

    class Update(TypedDict):
        name: NotRequired[str]
        role: NotRequired["User.Role"]
        status: NotRequired["User.Status"]

    id: str
    name: str
    role: Role
    status: Status
    created_at: datetime
    updated_at: datetime | None = None
    last_login_at: datetime | None = None


class UserPage(DataModel, frozen=True):
    users: Sequence[User]
    cursor: str | None = None


# ──── User Protocol ───────────────────────────────────────────────────────────────────


class UserProvider(Protocol):
    def list_users(
        self,
        *,
        q: str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> UserPage: ...

    def get_user(
        self,
        *,
        id: str,
    ) -> User: ...

    def update_user(
        self,
        *,
        id: str,
        update: User.Update,
    ) -> User: ...
