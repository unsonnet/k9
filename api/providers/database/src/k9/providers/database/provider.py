from collections.abc import Iterable
from itertools import batched
from typing import Any, overload

from k9.providers.base import BaseProvider, GrantSpec, apimethod
from k9.types.base import Partial, ResourceModel

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
    def create_item(
        self, key: str, model: ResourceModel | None = None, /, **attrs: DatabaseTypes
    ) -> None:
        with self.batch() as tx:
            tx.create_item(key, model, **attrs)
        return None

    @overload
    def read_item(self, key: str, /) -> dict[str, DatabaseTypes]: ...

    @overload
    def read_item[T: ResourceModel](self, key: str, model: type[T], /) -> T: ...

    @apimethod
    def read_item(
        self,
        key: str,
        model: type[ResourceModel] | None = None,
        /,
    ) -> dict[str, DatabaseTypes] | ResourceModel:
        root = Node()
        skip = (key.count("/") + 1) // 2
        for item in self._db.query_item(key):
            node = root
            subkey = str(item["key"]["key"])  # type: ignore
            for part in list(batched(subkey.split("/"), 2))[skip:]:
                node = node.subitems.setdefault(part, Node())  # type: ignore
            node.item = item
        item = root.serialize()
        return model.model_validate(item) if model is not None else item

    @apimethod
    def update_item(
        self,
        key: str,
        model: ResourceModel | Partial[Any] | None = None,
        /,
        **attrs: DatabaseTypes,
    ) -> None:
        with self.batch() as tx:
            tx.update_item(key, model, **attrs)
        return None

    @apimethod
    def delete_item(self, key: str, /) -> None:
        with self.batch() as tx:
            tx.delete_item(key)
        return None
