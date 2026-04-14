from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Callable
from functools import cached_property, wraps
from typing import Any

from pydantic import BaseModel

from shared.errors import DomainError, DomainUnknown


class ApiModel(BaseModel):
    model_config = {"frozen": True, "extra": "forbid"}


class DataModel(BaseModel, frozen=True, extra="forbid"): ...


# ──── Abstract Service ────────────────────────────────────────────────────────────────


def public_api(fn: Callable[..., Any]) -> Callable[..., Any]:
    return fn


class BaseService(ABC): ...


# ──── Abstract Provider ───────────────────────────────────────────────────────────────


type ExceptionMap = dict[type[DomainError], list[type[Exception]]]


def private_api(fn: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(fn)
    def wrapped(self: BaseProvider, *args: Any, **kwargs: Any) -> Any:
        try:
            return fn(self, *args, **kwargs)
        except DomainError:
            raise
        except Exception as exc:
            raise self._exc_map[type(exc)](str(exc)) from exc

    return wrapped


class BaseProvider(ABC):
    @property
    @abstractmethod
    def exception_map(self) -> ExceptionMap: ...

    @cached_property
    def _exc_map(self) -> defaultdict[type[Exception], type[DomainError]]:
        return defaultdict(
            lambda: DomainUnknown,
            {
                exc_type: domain_error
                for domain_error, exc_types in self.exception_map.items()
                for exc_type in exc_types
            },
        )
