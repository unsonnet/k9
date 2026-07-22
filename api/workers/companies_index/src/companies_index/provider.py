from collections.abc import Iterable

from shared.config import GrantSpec, settings
from shared.providers import BaseProvider, apimethod
from shared.providers.search import SearchProvider

from .models import CompanyItem

__all__ = [
    "CompanyIndexProvider",
]


class CompanyIndexProvider(BaseProvider):
    _os: SearchProvider

    def __init__(
        self,
        *,
        region: str | None = None,
        endpoint: str | None = None,
        index: str | None = None,
    ) -> None:
        self._os = SearchProvider(
            region=region or settings.aws_region,
            endpoint=endpoint or settings.opensearch_endpoint,
            index=index or settings.opensearch_index_companies,
        )

    @property
    def permissions(self) -> Iterable[GrantSpec]:
        yield from self._os.permissions

    # ──── Public Methods ────

    @apimethod
    def sync_company(self, *, item: CompanyItem) -> None:
        self._os.index_document(
            type="COMPANY",
            id=item.id,
            sector=item.sector.value,
            name=item.name,
            logo=item.logo,
            website=item.website,
        )

    @apimethod
    def delete_company(self, *, item: CompanyItem) -> None:
        self._os.delete_document(
            type="COMPANY",
            id=item.id,
        )
