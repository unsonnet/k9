from collections.abc import Iterable
from itertools import batched

from k9.providers.base import BaseProvider, GrantSpec, apimethod

from .batch import DatabaseBatchProvider
from .types import DatabaseTypes, Node

__all__ = [
    "DatabaseProvider",
]


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
