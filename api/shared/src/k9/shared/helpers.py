from __future__ import annotations

import importlib
import pkgutil
from datetime import datetime, timezone
from secrets import SystemRandom
from string import ascii_lowercase, ascii_uppercase, digits
from typing import Callable, Final, Iterable, Literal, overload

from pydantic import TypeAdapter
from typing_extensions import TypeForm

from .errors import DomainForbidden
from .types import Caller, Name, Password, ResourceID, SubresourceID, UserID

_RANDOM: Final = SystemRandom()


# ──── Registration ────────────────────────────────────────────────────────────────────


def load_apis(package: str, path: Iterable[str]) -> None:
    """Import every `api` module in a package tree so its endpoints register on the app."""
    for module in pkgutil.walk_packages(path, f"{package}."):
        if module.name.rpartition(".")[2] == "api":
            importlib.import_module(module.name)


def validate[T](type: TypeForm[T]) -> Callable[[str], T]:
    return TypeAdapter(type).validate_python


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


# ──── Credentials ─────────────────────────────────────────────────────────────────────


validate_name = validate(Name)
validate_password = validate(Password)


_PASSWORD_SPECIALS: Final = "!@#$%^&*()-_=+[]{}:,.?"
_PASSWORD_ALPHABET: Final = (
    ascii_lowercase + ascii_uppercase + digits + _PASSWORD_SPECIALS
)


def generate_password(length: int = 8) -> Password:
    chars = [
        _RANDOM.choice(ascii_lowercase),
        _RANDOM.choice(ascii_uppercase),
        _RANDOM.choice(digits),
        _RANDOM.choice(_PASSWORD_SPECIALS),
    ]
    chars += _RANDOM.choices(_PASSWORD_ALPHABET, k=length - len(chars))
    _RANDOM.shuffle(chars)
    return validate_password("".join(chars))


# ──── Identity ────────────────────────────────────────────────────────────────────────


validate_user_id = validate(UserID)


def generate_user_id() -> UserID:
    id = "".join(_RANDOM.choices(ascii_lowercase, k=3) + _RANDOM.choices(digits, k=3))
    return validate_user_id(id)


def require_admin(caller: Caller) -> None:
    if not caller.is_admin:
        raise DomainForbidden("Admin role required")


def require_admin_or_self(caller: Caller, id: UserID | Literal["me"]) -> UserID:
    if not caller.is_admin and id not in {"me", caller.id}:
        raise DomainForbidden("Cannot access another user's resource")
    return caller.id if id == "me" else id


# ──── Resources ───────────────────────────────────────────────────────────────────────


validate_resource_id = validate(ResourceID)
validate_subresource_id = validate(SubresourceID)


def generate_resource_id() -> ResourceID:
    id = "-".join("".join(_RANDOM.choice(digits) for _ in range(3)) for _ in range(3))
    return validate_resource_id(id)


def generate_subresource_id() -> SubresourceID:
    id = "".join(_RANDOM.choice(digits) for _ in range(4))
    return validate_subresource_id(id)


# ──── Query ───────────────────────────────────────────────────────────────────────────


def sanitize_query(q: str) -> str | None:
    return q.replace("\\", "\\\\").replace('"', '\\"') if (q := q.strip()) else None
