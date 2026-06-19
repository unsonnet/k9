from datetime import datetime, timezone
from typing import overload

from .errors import DomainForbidden
from .http import Caller


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


def require_admin(caller: Caller) -> None:
    if not caller.is_admin:
        raise DomainForbidden("Admin role required")


def require_admin_or_self(caller: Caller, id: str) -> str:
    if not caller.is_admin and id not in {"me", caller.id}:
        raise DomainForbidden("Cannot access another user's resource")
    return caller.id if id == "me" else id
