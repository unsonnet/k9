from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from itertools import batched

from shared.errors import DomainNotFound
from shared.providers.base import BaseProvider, GrantSpec, apimethod

from .batch import DatabaseBatchProvider, DatabaseTypes

__all__ = [
    "DatabaseTypes",
    "DatabaseProvider",
    "DatabaseBatchProvider",
]


@dataclass
class Node:
    item: dict[str, DatabaseTypes] = field(default_factory=dict)
    subitems: dict[tuple[str, str], Node] = field(default_factory=dict)

    def serialize(self) -> dict[str, DatabaseTypes]:
        if not self.item:
            raise DomainNotFound
        subitems: dict[str, list[dict[str, DatabaseTypes]]] = {}
        for (t, _), node in self.subitems.items():
            subitems.setdefault(f"${t}", []).append(node.serialize())
        return self.item | subitems


class DatabaseProvider(BaseProvider):
    _db: DatabaseBatchProvider

    def __init__(
        self,
        *,
        region: str,
        table: str,
    ) -> None:
        self._db = DatabaseBatchProvider(region=region, table=table)

    @property
    def permissions(self) -> Iterable[GrantSpec]:
        yield from self._db.permissions

    # ──── Public Methods ────

    @apimethod
    def batch(self) -> DatabaseBatchProvider:
        return self._db

    @apimethod
    def create_item(self, key: str, **attrs: DatabaseTypes) -> None:
        with self.batch() as batch:
            batch.create_item(key, **attrs)
        return None

    @apimethod
    def read_item(self, key: str) -> dict[str, DatabaseTypes]:
        root = Node()
        skip = (key.count("/") + 1) // 2
        for item in self._db.query_item(key):
            node = root
            subkey = str(item["key"]["key"])  # type: ignore
            for part in list(batched(subkey.split("/"), 2))[skip:]:
                node = node.subitems.setdefault(part, Node())  # type: ignore
            node.item = item
        return root.serialize()

    @apimethod
    def update_item(self, key: str, **attrs: DatabaseTypes) -> None:
        with self.batch() as batch:
            batch.update_item(key, **attrs)
        return None

    @apimethod
    def delete_item(self, key: str) -> None:
        with self.batch() as batch:
            batch.delete_item(key)
        return None
