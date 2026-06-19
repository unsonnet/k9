from dataclasses import dataclass
from typing import Annotated, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class StreamNewImage:
    pass


@dataclass(frozen=True)
class StreamOldImage:
    pass


@dataclass(frozen=True)
class StreamKeys:
    pass


@dataclass(frozen=True)
class StreamRecord:
    pass


NewImage = Annotated[T, StreamNewImage()]
OldImage = Annotated[T, StreamOldImage()]
Keys = Annotated[T, StreamKeys()]
Record = Annotated[T, StreamRecord()]


__all__ = [
    "StreamNewImage",
    "StreamOldImage",
    "StreamKeys",
    "StreamRecord",
    "NewImage",
    "OldImage",
    "Keys",
    "Record",
]
