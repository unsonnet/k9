from dataclasses import dataclass
from typing import Annotated, TypeAlias, TypeVar

from pydantic import AliasPath, BaseModel

__all__ = [
    "Keys",
    "NewImage",
    "OldImage",
    "EventModel",
]


@dataclass(frozen=True, slots=True)
class SourceMarker:
    source: str


T = TypeVar("T")

Keys: TypeAlias = Annotated[T, SourceMarker(source="keys")]
NewImage: TypeAlias = Annotated[T, SourceMarker(source="new_image")]
OldImage: TypeAlias = Annotated[T, SourceMarker(source="old_image")]


class EventModel(BaseModel, frozen=True):
    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs):
        super().__pydantic_init_subclass__(**kwargs)
        for name, field in cls.model_fields.items():
            for marker in field.metadata:
                if isinstance(marker, SourceMarker):
                    field.validation_alias = AliasPath(marker.source, name)
                    continue
        cls.model_rebuild(force=True)
