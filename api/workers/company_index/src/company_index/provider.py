from typing import Protocol

import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from opensearchpy.exceptions import NotFoundError
from pydantic import HttpUrl
from shared.config import settings
from shared.errors import DomainNotFound
from shared.provider import BaseProvider, ExceptionMap, apimethod

from .models import Address, CompanySector

__all__ = [
    "IndexProvider",
    "OpenSearchIndexProvider",
]


class IndexProvider(Protocol):
    def index_company(
        self,
        *,
        id: str,
        sector: CompanySector,
        name: str,
        logo: HttpUrl,
        website: HttpUrl,
        locations: list[Address],
    ) -> None: ...

    def unindex_company(
        self,
        *,
        id: str,
    ) -> None: ...


# ──── OpenSearch Index Provider ───────────────────────────────────────────────────────


class OpenSearchIndexProvider(BaseProvider):
    _os: OpenSearch
    _os_idx: str

    def __init__(
        self,
        *,
        region: str | None = None,
        company_index: str | None = None,
    ) -> None:
        region = region or settings.aws_region
        self._os = OpenSearch(
            hosts=[{"host": settings.opensearch_endpoint, "port": 443}],
            http_auth=settings.aws_auth(boto3.Session(region_name=region)),
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            timeout=300,
        )
        self._os_idx = company_index or f"{settings.opensearch_index}-companies"

    @property
    def _exception_map(self) -> ExceptionMap:
        return {
            DomainNotFound: [NotFoundError],
        }

    # ──── Public Methods ────

    @apimethod
    def index_company(
        self,
        *,
        id: str,
        sector: CompanySector,
        name: str,
        logo: HttpUrl,
        website: HttpUrl,
        locations: list[Address],
    ) -> None:
        self._os.index(
            index=self._os_idx,
            id=id,
            body={
                "id": id,
                "sector": sector.value,
                "name": name,
                "logo": str(logo),
                "website": str(website),
                "locations": [location.model_dump() for location in locations],
            },
            params={"refresh": "wait_for"},
        )
        return None

    @apimethod
    def unindex_company(
        self,
        *,
        id: str,
    ) -> None:
        self._os.delete(
            index=self._os_idx,
            id=id,
            params={"refresh": "wait_for"},
        )
        return None
