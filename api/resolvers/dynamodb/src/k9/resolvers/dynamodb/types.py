from inspect import Parameter
from typing import Callable, Protocol, overload

from aws_lambda_powertools.utilities.data_classes.dynamo_db_stream_event import (
    DynamoDBRecord,
)
from k9.shared.config import missing
from pydantic import BaseModel

__all__ = [
    "DynamoDBEventDecorator",
    "DynamoDBRecord",
    "MISSING_PARAM",
]


MISSING_PARAM = Parameter(
    name="caller",
    kind=Parameter.POSITIONAL_OR_KEYWORD,
    annotation=missing,
)


class DynamoDBEventDecorator[R: BaseModel, S: BaseModel, T](Protocol):
    @overload
    def __call__(self, func: Callable[[], T]) -> Callable[[], T]: ...
    @overload
    def __call__(self, func: Callable[[str], T]) -> Callable[[str], T]: ...
    @overload
    def __call__(self, func: Callable[[str, R], T]) -> Callable[[str, R], T]: ...
    @overload
    def __call__(self, func: Callable[[str, R, S], T]) -> Callable[[str, R, S], T]: ...
    @overload
    def __call__(self, func: Callable[[R], T]) -> Callable[[R], T]: ...
    @overload
    def __call__(self, func: Callable[[R, S], T]) -> Callable[[R, S], T]: ...
    def __call__(self, func: Callable[..., T]) -> Callable[..., T]: ...
