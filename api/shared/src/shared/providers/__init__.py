from collections import defaultdict
from collections.abc import Callable, Iterable
from functools import cached_property, wraps
from typing import Concatenate

from ..config import GrantSpec
from ..errors import DomainError, DomainUnknown

__all__ = [
    "ExceptionMap",
    "BaseProvider",
    "apimethod",
]


type ExceptionMap = dict[type[DomainError], list[type[Exception]]]


class BaseProvider:
    @property
    def permissions(self) -> Iterable[GrantSpec]:
        return ()

    @property
    def exception_map(self) -> ExceptionMap:
        return {}

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


type APIMethod[T: BaseProvider, **P, R] = Callable[Concatenate[T, P], R]


def apimethod[T: BaseProvider, **P, R](fn: APIMethod[T, P, R]) -> APIMethod[T, P, R]:
    @wraps(fn)
    def wrapped(self: T, *args: P.args, **kwargs: P.kwargs) -> R:
        try:
            return fn(self, *args, **kwargs)
        except DomainError:
            raise
        except Exception as exc:
            raise self._exc_map[type(exc)]() from exc

    return wrapped
