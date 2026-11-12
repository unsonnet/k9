from decimal import Decimal
from typing import Iterable

from k9.providers.base import BaseProvider, GrantSpec, apimethod
from k9.providers.search import Page, SearchProvider
from k9.providers.search.queries import Near, Term, Text
from k9.shared.config import is_set, missing, settings

from .models import CompanyIndex, Industry

__all__ = [
    "CompanySearchProvider",
]


class CompanySearchProvider(BaseProvider):
    _os: SearchProvider

    def __init__(
        self,
        *,
        region: str | None = None,
        index: str | None = None,
        opensearch_endpoint: str | None = None,
    ) -> None:
        # opensearch
        self._os = SearchProvider(
            region=region or settings.aws_region,
            endpoint=opensearch_endpoint or settings.opensearch_endpoint,
            index=index or settings.opensearch_index_companies,
        )

    @property
    def permissions(self) -> Iterable[GrantSpec]:
        yield from self._os.permissions

    # ──── Public Methods ────

    @apimethod
    def search_companies(
        self,
        *,
        type: list[Industry] | missing,
        name: str | missing,
        geo: tuple[Decimal, Decimal, int] | missing,
        limit: int,
        cursor: str | missing,
    ) -> Page[CompanyIndex]:
        return self._os.search(
            Term("type", *type) if is_set(type) else None,
            Text("name", name) if is_set(name) else None,
            Near("$locations.geo", geo) if is_set(geo) else None,
            limit=limit,
            cursor=cursor if is_set(cursor) else None,
        ).hydrate(CompanyIndex)
