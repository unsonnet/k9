from dataclasses import dataclass
from typing import Any, Callable, Mapping, Protocol, overload

from aws_lambda_powertools.utilities.data_classes.common import DictWrapper
from aws_lambda_powertools.utilities.data_classes.s3_event import S3EventRecord
from pydantic import BaseModel

__all__ = [
    "S3EventDecorator",
    "S3EventRecord",
    "S3Wrapper",
]


class S3EventDecorator[R: BaseModel, T](Protocol):
    @overload
    def __call__(self, func: Callable[[], T]) -> Callable[[], T]: ...
    @overload
    def __call__(self, func: Callable[[R], T]) -> Callable[[R], T]: ...
    def __call__(self, func: Callable[..., T]) -> Callable[..., T]: ...


@dataclass(frozen=True, slots=True)
class S3Wrapper(Mapping[str, Any]):
    _data: DictWrapper

    def __getitem__(self, key: str) -> Any:
        return getattr(self._data, key)

    def __iter__(self):
        return iter(("key", "size", "etag", "version_id", "sequencer"))

    def __len__(self):
        return 5
