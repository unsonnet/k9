from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Callable
from functools import cached_property, wraps
from typing import Concatenate

from shared.errors import DomainError, DomainUnknown

__all__ = [
    "ExceptionMap",
    "BaseProvider",
    "apimethod",
]


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


def apimethod[T: BaseProvider, **P, R](
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
