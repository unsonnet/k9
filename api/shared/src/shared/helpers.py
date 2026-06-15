from datetime import datetime, timezone
from typing import overload

from .errors import DomainForbidden
from .http import Caller

now = datetime.now


@overload
def dt(value: datetime | str) -> datetime: ...
@overload
def dt(value: None) -> None: ...
def dt(value: datetime | str | None) -> datetime | None:
    match value:
        case datetime() as dt:
            return dt.astimezone(timezone.utc)
        case str() as s:
            return datetime.fromisoformat(s).astimezone(timezone.utc)
        case None:
            return None


def require_admin(caller: Caller) -> None:
    if not caller.is_admin:
        raise DomainForbidden("Admin role required")


def require_owner(caller: Caller, owner_id: str) -> None:
    if not caller.is_admin and owner_id not in {"me", caller.id}:
        raise DomainForbidden("Cannot access another user's resource")
