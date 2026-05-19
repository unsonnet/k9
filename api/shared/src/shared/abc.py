from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Callable
from enum import StrEnum
from functools import cached_property, wraps
from typing import Any, Concatenate, Literal, Protocol, overload

from pydantic import BaseModel

from shared.errors import DomainError, DomainForbidden, DomainUnknown

__all__ = [
    "ApiModel",
    "DataModel",
    "BaseService",
    "public_api",
    "BaseProvider",
    "private_api",
]


class Role(StrEnum):
    USER = "user"
    ADMIN = "admin"


class Caller(BaseModel, frozen=True):
    id: str
    name: str
    role: Role
    token: str

    @property
    def is_admin(self) -> bool:
        return self.role == Role.ADMIN


class ApiModel(BaseModel, frozen=True, extra="forbid"): ...


class DataModel(BaseModel, frozen=True, extra="forbid", populate_by_name=True): ...


# ──── Abstract Service ────────────────────────────────────────────────────────────────


class BaseService(ABC):
    @classmethod
    def require_admin(cls, caller: Caller) -> None:
        if not caller.is_admin:
            raise DomainForbidden("Admin role required")

    @classmethod
    def require_owner(cls, caller: Caller, owner_id: str) -> None:
        if not caller.is_admin and owner_id not in {"me", caller.id}:
            raise DomainForbidden("Cannot access another user's resource")


class UserOwnedRequest(Protocol):
    @property
    def userId(self) -> str: ...


type AnyCallable = Callable[..., Any]
type PublicMethod[S: BaseService, **P, R] = Callable[Concatenate[S, Caller, P], R]
type OwnerMethod[S: BaseService, Req: UserOwnedRequest, **P, R] = Callable[
    Concatenate[S, Caller, Req, P], R
]


@overload
def public_api[F: AnyCallable](
    func: F,
    /,
    *,
    require_admin: Literal[False] = False,
    require_owner: Literal[False] = False,
) -> F: ...


@overload
def public_api[F: AnyCallable](
    func: None = None,
    /,
    *,
    require_admin: Literal[False] = False,
    require_owner: Literal[False] = False,
) -> Callable[[F], F]: ...


@overload
def public_api[S: BaseService, **P, R](
    func: None = None,
    /,
    *,
    require_admin: Literal[True],
    require_owner: Literal[False] = False,
) -> Callable[[PublicMethod[S, P, R]], PublicMethod[S, P, R]]: ...


@overload
def public_api[S: BaseService, Req: UserOwnedRequest, **P, R](
    func: None = None,
    /,
    *,
    require_admin: Literal[False] = False,
    require_owner: Literal[True],
) -> Callable[[OwnerMethod[S, Req, P, R]], OwnerMethod[S, Req, P, R]]: ...


def public_api(
    func: AnyCallable | None = None,
    /,
    *,
    require_admin: bool = False,
    require_owner: bool = False,
) -> AnyCallable:
    if require_admin and require_owner:
        raise TypeError("Use either require_admin or require_owner, not both")

    def decorate(method: AnyCallable) -> AnyCallable:
        @wraps(method)
        def wrapper(
            self: BaseService,
            caller: Caller,
            *args: Any,
            **kwargs: Any,
        ) -> Any:
            if require_admin:
                self.require_admin(caller)
            elif require_owner:
                request = args[0]
                self.require_owner(caller, request.userId)
            return method(self, caller, *args, **kwargs)

        return wrapper

    return decorate(func) if func is not None else decorate


# ──── Abstract Provider ───────────────────────────────────────────────────────────────


type ExceptionMap = dict[type[DomainError], list[type[Exception]]]


class BaseProvider(ABC):
    @property
    @abstractmethod
    def _exception_map(self) -> ExceptionMap: ...

    @cached_property
    def _exc_map(self) -> defaultdict[type[Exception], type[DomainError]]:
        return defaultdict(
            lambda: DomainUnknown,
            {
                exc_type: domain_error
                for domain_error, exc_types in self._exception_map.items()
                for exc_type in exc_types
            },
        )


type PrivateMethod[T: BaseProvider, **P, R] = Callable[Concatenate[T, P], R]


def private_api[T: BaseProvider, **P, R](
    fn: Callable[Concatenate[T, P], R],
) -> Callable[Concatenate[T, P], R]:
    @wraps(fn)
    def wrapped(self: T, *args: P.args, **kwargs: P.kwargs) -> R:
        try:
            return fn(self, *args, **kwargs)
        except DomainError:
            raise
        except Exception as exc:
            raise self._exc_map[type(exc)]() from exc

    if getattr(fn, "__isabstractmethod__", False):
        wrapped.__isabstractmethod__ = True  # type: ignore[attr-defined]

    return wrapped
