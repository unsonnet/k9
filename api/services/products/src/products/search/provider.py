from typing import Iterable

from shared.config import is_set, missing, settings
from shared.providers.base import BaseProvider, GrantSpec, apimethod
from shared.providers.database import DatabaseProvider
from shared.providers.search import Page, SearchProvider
from shared.providers.search.queries import (
    AllOf,
    AnyOf,
    Exclude,
    Prefix,
    Query,
    Range,
    Term,
    Text,
)

from .models import FormatFilter, MaterialFilter, ProductIndex

__all__ = [
    "ProductSearchProvider",
]


class ProductSearchProvider(BaseProvider):
    _db: DatabaseProvider
    _os: SearchProvider

    def __init__(
        self,
        *,
        region: str | None = None,
        table: str | None = None,
        index: str | None = None,
        opensearch_endpoint: str | None = None,
    ) -> None:
        region = region or settings.aws_region
        # dynamodb
        self._db = DatabaseProvider(
            region=region,
            table=table or settings.dynamodb_table,
        )
        # opensearch
        self._os = SearchProvider(
            region=region,
            endpoint=opensearch_endpoint or settings.opensearch_endpoint,
            index=index or settings.opensearch_index_products,
        )

    @property
    def permissions(self) -> Iterable[GrantSpec]:
        yield from self._db.permissions
        yield from self._os.permissions

    # ──── Public Methods ────

    @apimethod
    def search_products(
        self,
        *,
        q: str | missing,
        sku: str | missing,
        store: list[str] | missing,
        material: list[MaterialFilter] | missing,
        format: list[FormatFilter] | missing,
        reference: str | missing,
        limit: int,
        cursor: str | missing,
    ) -> Page[ProductIndex]:
        if is_set(reference):
            self._db.read_item(f"products/{reference}")
        return self._os.search(
            Text("$listings.name", q) if is_set(q) else None,
            Prefix("$listings.sku", sku) if is_set(sku) else None,
            self._store(store) if is_set(store) else None,
            self._material(material) if is_set(material) else None,
            self._format(format) if is_set(format) else None,
            Exclude(reference) if is_set(reference) else None,
            limit=limit,
            cursor=cursor if is_set(cursor) else None,
        ).hydrate(ProductIndex)

    # ──── Private Methods ────

    @staticmethod
    def _store(store: list[str]) -> Query:
        return AnyOf(Term("brand", *store), Term("$listings.vendor", *store))

    @staticmethod
    def _material(options: list[MaterialFilter]) -> Query:
        return AnyOf(
            AllOf(Term(f"material.{k}", v) for k, v in option.terms())
            for option in options
        )

    @classmethod
    def _format(cls, options: list[FormatFilter]) -> Query:
        def ranges(pre: str, option: FormatFilter) -> Iterable[Query]:
            for dim, r in option.ranges():
                yield Range(f"{pre}.{dim}", r.gte, r.lte, r.include_missing)

        return AnyOf(
            AnyOf(
                AllOf(ranges("format", option)),
                AllOf(ranges("$subformat", option), nest=True),
            )
            for option in options
        )
