from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Callable
from functools import cached_property, update_wrapper, wraps
from typing import Concatenate, Literal, Self, cast, overload

from pydantic import BaseModel, Field, model_validator

from shared.errors import DomainError, DomainForbidden, DomainUnknown
from shared.http import Caller

__all__ = [
    "Field",
    "model_validator",
    "ApiModel",
    "DataModel",
    "BaseService",
    "public_api",
    "BaseProvider",
    "private_api",
]


class ApiModel(BaseModel, frozen=True, extra="forbid"): ...


class DataModel(BaseModel, frozen=True, extra="forbid"): ...


# ──── Abstract Service ────────────────────────────────────────────────────────────────


class BaseService(ABC):
    @staticmethod
    def is_admin(caller: Caller) -> bool:
        return "admin" in caller.groups

    @classmethod
    def require_admin(cls, caller: Caller) -> None:
        if not cls.is_admin(caller):
            raise DomainForbidden("Admin role required")


type PublicMethod[T: BaseService, **P, R] = Callable[Concatenate[T, Caller, P], R]
type AnyCallable = Callable[..., object]


class RoleDispatcher[T: BaseService, **P, R]:
    """Descriptor returned by @public_api.dispatch_by_role."""

    def __init__(self, func: PublicMethod[T, P, R], /) -> None:
        self.__wrapped__ = func
        self._admin_impl: PublicMethod[T, P, R] | None = None
        self._user_impl: PublicMethod[T, P, R] | None = None
        update_wrapper(cast(AnyCallable, self), func)

    def admin(self, func: PublicMethod[T, P, R], /) -> PublicMethod[T, P, R]:
        self._admin_impl = func
        return func

    def user(self, func: PublicMethod[T, P, R], /) -> PublicMethod[T, P, R]:
        self._user_impl = func
        return func

    @overload
    def __get__(self, instance: None, owner: type[T] | None = None, /) -> Self: ...

    @overload
    def __get__(
        self,
        instance: T,
        owner: type[T] | None = None,
        /,
    ) -> Callable[Concatenate[Caller, P], R]: ...

    def __get__(
        self,
        instance: T | None,
        owner: type[T] | None = None,
        /,
    ) -> Self | Callable[Concatenate[Caller, P], R]:
        if instance is None:
            return self

        @wraps(self.__wrapped__)
        def dispatch(caller: Caller, /, *args: P.args, **kwargs: P.kwargs) -> R:
            is_admin = instance.is_admin(caller)
            impl = self._admin_impl if is_admin else self._user_impl

            if impl is None:
                role = "admin" if is_admin else "user"
                raise DomainUnknown(f"No {role} implementation registered")

            return impl(instance, caller, *args, **kwargs)

        return dispatch


class PublicApi(type):
    @overload
    def __call__[F: AnyCallable](
        cls,
        func: F,
        /,
        *,
        require_admin: Literal[False] = False,
    ) -> F: ...

    @overload
    def __call__[F: AnyCallable](
        cls,
        func: None = None,
        /,
        *,
        require_admin: Literal[False] = False,
    ) -> Callable[[F], F]: ...

    @overload
    def __call__[S: BaseService, **P, R](
        cls,
        func: PublicMethod[S, P, R],
        /,
        *,
        require_admin: Literal[True],
    ) -> PublicMethod[S, P, R]: ...

    @overload
    def __call__[S: BaseService, **P, R](
        cls,
        func: None = None,
        /,
        *,
        require_admin: Literal[True],
    ) -> Callable[[PublicMethod[S, P, R]], PublicMethod[S, P, R]]: ...

    def __call__(
        cls,
        func: AnyCallable | None = None,
        /,
        *,
        require_admin: bool = False,
    ) -> AnyCallable:
        if func is None:
            return cls._require_admin if require_admin else cls._identity

        return cls._require_admin(func) if require_admin else func

    def _identity[F: AnyCallable](cls, func: F, /) -> F:
        return func

    def _require_admin[S: BaseService, **P, R](
        cls,
        method: PublicMethod[S, P, R],
        /,
    ) -> PublicMethod[S, P, R]:
        @wraps(method)
        def wrapper(
            self: S,
            caller: Caller,
            /,
            *args: P.args,
            **kwargs: P.kwargs,
        ) -> R:
            self.require_admin(caller)
            return method(self, caller, *args, **kwargs)

        return cast(PublicMethod[S, P, R], wrapper)

    def dispatch_by_role[S: BaseService, **P, R](
        cls,
        func: PublicMethod[S, P, R],
        /,
    ) -> RoleDispatcher[S, P, R]:
        return RoleDispatcher(func)


class public_api(metaclass=PublicApi):
    """Decorator namespace for public service methods."""


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
