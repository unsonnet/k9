from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel

__all__ = [
    "Page",
]


@dataclass(frozen=True, slots=True)
class Page[T]:
    items: list[T]
    cursor: str | None

    def hydrate[M: BaseModel](self, model: type[M]) -> Page[M]:
        return Page(
            items=[model.model_validate(item) for item in self.items],
            cursor=self.cursor,
        )
