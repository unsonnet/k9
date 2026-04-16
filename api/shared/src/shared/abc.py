from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Callable
from functools import cached_property, wraps
from typing import Concatenate, ParamSpec, TypeVar

from pydantic import BaseModel

from shared.errors import DomainError, DomainUnknown

P = ParamSpec("P")
R = TypeVar("R")
S = TypeVar("S", bound="BaseService")
T = TypeVar("T", bound="BaseProvider")


class ApiModel(BaseModel, frozen=True, extra="forbid"): ...


class DataModel(BaseModel, frozen=True, extra="forbid"): ...


# ──── Abstract Service ────────────────────────────────────────────────────────────────


def public_api(fn: Callable[Concatenate[S, P], R]) -> Callable[Concatenate[S, P], R]:
    @wraps(fn)
    def wrapped(self: S, *args: P.args, **kwargs: P.kwargs) -> R:
        return fn(self, *args, **kwargs)

    return wrapped


class BaseService(ABC): ...


# ──── Abstract Provider ───────────────────────────────────────────────────────────────


type ExceptionMap = dict[type[DomainError], list[type[Exception]]]


def private_api(fn: Callable[Concatenate[T, P], R]) -> Callable[Concatenate[T, P], R]:
    @wraps(fn)
    def wrapped(self: T, *args: P.args, **kwargs: P.kwargs) -> R:
        try:
            return fn(self, *args, **kwargs)
        except DomainError:
            raise
        except Exception as exc:
            raise self._exc_map[type(exc)](str(exc)) from exc

    if getattr(fn, "__isabstractmethod__", False):
        wrapped.__isabstractmethod__ = True  # type: ignore[attr-defined]
    return wrapped


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
