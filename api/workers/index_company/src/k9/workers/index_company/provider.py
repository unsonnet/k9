from collections.abc import Iterable

from k9.providers.base import BaseProvider, GrantSpec, apimethod
from k9.providers.config import settings
from k9.providers.search import SearchProvider

__all__ = [
    "IndexCompanyProvider",
]


class IndexCompanyProvider(BaseProvider):
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
    def index(self, key: str, **attrs) -> None:
        self._os.upsert(key, **attrs)

    @apimethod
    def drop(self, key: str) -> None:
        self._os.delete(key)
