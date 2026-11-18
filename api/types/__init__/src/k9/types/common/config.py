from typing import TYPE_CHECKING, TypeAliasType, TypeGuard

from pydantic_core import MISSING as missing  # type: ignore

if TYPE_CHECKING:
    type missing = TypeAliasType

__all__ = [
    "is_set",
    "missing",
]


def is_set[T](value: T | missing) -> TypeGuard[T]:
    return value is not missing
