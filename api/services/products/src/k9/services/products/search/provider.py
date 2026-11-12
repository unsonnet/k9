from decimal import Decimal
from typing import Iterable, Iterator, Self

from k9.providers.base import BaseProvider, GrantSpec, apimethod
from k9.providers.search import Page, SearchProvider
from k9.providers.search.queries import (
    AllOf,
    AnyOf,
    Exclude,
    Prefix,
    Query,
    Range,
    Term,
    Text,
)
from k9.shared.config import is_set, missing, settings
from k9.shared.types import ResourceID, SubresourceID
from pydantic import BaseModel, Field, HttpUrl, model_validator

from ..provider import Format, Material

__all__ = [
    "ProductSearchProvider",
]


class MaterialFilter(BaseModel, frozen=True):
    type: str | None = None
    subtype: str | None = None
    look: str | None = None
    edge: str | None = None
    finish: str | None = None
    texture: str | None = None

    def terms(self) -> Iterator[tuple[str, str]]:
        return ((k, v) for k, v in self if v is not None)


class FormatFilter(BaseModel, frozen=True):
    class Range(BaseModel, frozen=True):
        gte: Decimal | None = None
        lte: Decimal | None = None
        include_missing: bool = False

        @model_validator(mode="after")
        def validate_bounds(self) -> Self:
            if self.gte is not None and self.lte is not None and self.gte > self.lte:
                raise ValueError("gte must not exceed lte")
            return self

    length: Range | None = None
    width: Range | None = None
    thickness: Range | None = None
    wear: Range | None = None

    def ranges(self) -> Iterator[tuple[str, Range]]:
        return ((k, v) for k, v in self if v is not None)


class ImageIndex(BaseModel, frozen=True):
    id: SubresourceID
    scope: ResourceID | None
    url: HttpUrl


class ListingIndex(BaseModel, frozen=True):
    id: SubresourceID
    scope: ResourceID | None
    vendor: ResourceID
    sku: str | None
    name: str


class ProductIndex(BaseModel, frozen=True):
    id: ResourceID
    scope: ResourceID | None
    brand: ResourceID | None
    material: Material
    format: Format
    subformats: list[Format] = Field(default_factory=list, alias="$subformats")
    images: list[ImageIndex] = Field(default_factory=list, alias="$images")
    listings: list[ListingIndex] = Field(default_factory=list, alias="$listings")
    score: Decimal | None = Field(None, alias="$score")


class ProductSearchProvider(BaseProvider):
    _os: SearchProvider

    def __init__(
        self,
        *,
        region: str | None = None,
        index: str | None = None,
        opensearch_endpoint: str | None = None,
    ) -> None:
        region = region or settings.aws_region
        # opensearch
        self._os = SearchProvider(
            region=region,
            endpoint=opensearch_endpoint or settings.opensearch_endpoint,
            index=index or settings.opensearch_index_products,
        )

    @property
    def permissions(self) -> Iterable[GrantSpec]:
        yield from self._os.permissions

    # ──── Public Methods ────

    @apimethod
    def search_products(
        self,
        *,
        q: str | missing,
        sku: str | missing,
        store: list[ResourceID] | missing,
        material: list[MaterialFilter] | missing,
        format: list[FormatFilter] | missing,
        reference: ResourceID | missing,
        limit: int,
        cursor: str | missing,
    ) -> Page[ProductIndex]:
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
    def _store(store: list[ResourceID]) -> Query:
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
                AllOf(ranges("$subformats", option), nest=True),
            )
            for option in options
        )
