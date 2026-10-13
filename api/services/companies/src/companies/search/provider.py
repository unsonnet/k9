from decimal import Decimal
from typing import Iterable

from shared.config import is_set, missing, settings
from shared.providers.base import BaseProvider, GrantSpec, apimethod
from shared.providers.search import Near, Page, SearchProvider, Term, Text

from .models import CompanyIndex, Sector

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
        sector: list[Sector] | missing,
        name: str | missing,
        geo: tuple[Decimal, Decimal, int] | missing,
        limit: int,
        cursor: str | missing,
    ) -> Page[CompanyIndex]:
        return self._os.search(
            Term("sector", [i.value for i in sector] if is_set(sector) else None),
            Text("name", name if is_set(name) else None),
            Near("$location", geo if is_set(geo) else None),
            limit=limit,
            cursor=cursor if is_set(cursor) else None,
        ).hydrate(CompanyIndex)
