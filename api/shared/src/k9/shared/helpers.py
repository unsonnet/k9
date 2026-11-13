from __future__ import annotations

import importlib
import pkgutil
from datetime import datetime, timezone
from typing import Iterable, Literal, overload

from k9.types.common import Caller, UserID

from .errors import DomainForbidden

# ──── Registration ────────────────────────────────────────────────────────────────────


def load_apis(package: str, path: Iterable[str]) -> None:
    """Import every `api` module in a package tree so its endpoints register on the app."""
    for module in pkgutil.walk_packages(path, f"{package}."):
        if module.name.rpartition(".")[2] == "api":
            importlib.import_module(module.name)


# ──── Datetime ────────────────────────────────────────────────────────────────────────


def now() -> datetime:
    return datetime.now(timezone.utc)


@overload
def dt(value: datetime) -> datetime: ...
@overload
def dt(value: str, iso: bool = True) -> datetime: ...
@overload
def dt(value: None, iso: bool = True) -> None: ...
def dt(value: datetime | str | None, iso: bool = True) -> datetime | None:
    match value:
        case datetime() as dt:
            return dt.astimezone(timezone.utc)
        case str() as s:
            if iso:
                return datetime.fromisoformat(s).astimezone(timezone.utc)
            return datetime.strptime(s, "%Y-%m-%d %H:%M:%S %Z").astimezone(timezone.utc)
        case None:
            return None


# ──── Identity ────────────────────────────────────────────────────────────────────────


def require_admin(caller: Caller) -> None:
    if not caller.is_admin:
        raise DomainForbidden("Admin role required")


def require_admin_or_self(caller: Caller, id: UserID | Literal["me"]) -> UserID:
    if not caller.is_admin and id not in {"me", caller.id}:
        raise DomainForbidden("Cannot access another user's resource")
    return caller.id if id == "me" else id


# ──── Query ───────────────────────────────────────────────────────────────────────────


def sanitize_query(q: str) -> str | None:
    return q.replace("\\", "\\\\").replace('"', '\\"') if (q := q.strip()) else None
