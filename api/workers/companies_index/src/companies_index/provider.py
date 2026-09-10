from collections.abc import Iterable

from shared.config import GrantSpec, settings
from shared.providers import BaseProvider, apimethod
from shared.providers.search import SearchProvider

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
    def sync(self, *, type: str, id: str, **attrs) -> None:
        self._os.upsert(
            type=type,
            id=id,
            **attrs,
        )

    @apimethod
    def remove(self, *, type: str, id: str) -> None:
        self._os.delete(
            type=type,
            id=id,
        )
