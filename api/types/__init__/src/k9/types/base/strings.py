import re
from typing import ClassVar, Self

from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema

__all__ = [
    "ValidatedStr",
]


class ValidatedStr(str):
    _pattern: ClassVar[re.Pattern[str]]
    _min_length: ClassVar[int | None] = None
    _max_length: ClassVar[int | None] = None

    def __new__(cls, value: str) -> Self:
        return str.__new__(cls, cls._validate(value))

    @classmethod
    def _validate(cls, value: str) -> str:
        if not cls._pattern.fullmatch(value):
            raise ValueError(f"Invalid {cls.__name__}: {value!r}")
        return value

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: type,
        handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_after_validator_function(
            cls,
            core_schema.str_schema(
                pattern=cls._pattern,
                min_length=cls._min_length,
                max_length=cls._max_length,
            ),
        )
