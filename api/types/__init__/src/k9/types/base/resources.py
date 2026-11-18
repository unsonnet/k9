from __future__ import annotations

from copy import copy
from decimal import Decimal
from functools import cache
from typing import TYPE_CHECKING, Any, Self

from pydantic import AnyUrl, BaseModel, create_model
from pydantic_core import MISSING, MultiHostUrl, Url
from types_boto3_dynamodb.type_defs import TableAttributeValueTypeDef

__all__ = [
    "Page",
    "Partial",
    "ResourceModel",
]


def _database_value(value: Any) -> TableAttributeValueTypeDef:
    match value:
        case AnyUrl() | Url() | MultiHostUrl():
            return str(value)
        case float():
            return Decimal(str(value))
        case dict():
            return {str(k): _database_value(v) for k, v in value.items()}
        case list() | tuple():
            return [_database_value(v) for v in value]
        case set():
            return {_database_value(v) for v in value}  # type: ignore
        case None | str() | bytes() | bytearray() | int() | Decimal():
            return value
    raise TypeError(f"Unsupported DynamoDB value: {type(value).__name__}")


@cache
def _partial_model[T: BaseModel](model: type[T]) -> type[T]:
    fields: dict[str, Any] = {}
    for name, original in model.model_fields.items():
        field = copy(original)
        field.default = MISSING
        field.default_factory = None
        field.validate_default = False
        fields[name] = (original.annotation, field)
    return create_model(
        f"Partial{model.__name__}",
        __base__=model,
        **fields,
    )


class Partial[T: BaseModel]:
    def __init__(self, value: T) -> None:
        self._value = value

    def model_dump(self) -> dict[str, Any]:
        return self._value.model_dump(by_alias=True, exclude_unset=True)

    def model_dump_dynamodb(self) -> dict[str, TableAttributeValueTypeDef]:
        return {k: _database_value(v) for k, v in self.model_dump().items()}


class ResourceModel(BaseModel, frozen=True, extra="forbid", validate_by_name=True):
    def model_dump_dynamodb(self) -> dict[str, TableAttributeValueTypeDef]:
        return {
            k: _database_value(v) for k, v in self.model_dump(by_alias=True).items()
        }

    if not TYPE_CHECKING:

        @classmethod
        def partial(cls, **values: Any) -> Partial[Self]:
            return Partial(
                _partial_model(cls).model_validate(
                    {k: v for k, v in values.items() if v is not MISSING}
                )
            )


class Page[T](BaseModel, frozen=True):
    items: list[T]
    cursor: str | None

    def hydrate[M: BaseModel](self, model: type[M]) -> Page[M]:
        return Page(
            items=[model.model_validate(item) for item in self.items],
            cursor=self.cursor,
        )
